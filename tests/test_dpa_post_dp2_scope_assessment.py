from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.dpa_post_dp2_scope_assessment import (
    evaluate_post_dp2_scope_assessment,
)
from agentic_project_kit.dpa_readiness import DEFAULT_READINESS_PATH
from agentic_project_kit.dpa_successor_projection import DPA_SUCCESSOR_PROJECTION_SOURCE_PATHS
from agentic_project_kit.dpa_workspace_init_projection import DPA_WORKSPACE_INIT_SOURCE_PATHS

runner = CliRunner()


def _write(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _touch(root: Path, path: str) -> None:
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("fixture\n", encoding="utf-8")


def _fixture_root(root: Path) -> None:
    for path in (*DPA_WORKSPACE_INIT_SOURCE_PATHS, *DPA_SUCCESSOR_PROJECTION_SOURCE_PATHS):
        _touch(root, path)
    _touch(root, "docs/handoff/CURRENT_HANDOFF.md")
    _touch(root, "docs/STATUS.md")
    (root / "docs/reports/handoff-packages/latest").mkdir(parents=True)
    command_reference = root / "docs/reference/agentic-kit-commands.json"
    command_reference.parent.mkdir(parents=True)
    command_reference.write_text(
        json.dumps({"schema_version": 2, "meta": {"manifest_sha": "testsha"}}),
        encoding="utf-8",
    )
    _write(
        root / "docs/architecture/evidence/dpa/probes/fixture-evidence-0b985a22-wrt-ch005-20260729/results.json",
        _fixture_evidence("0b985a22f3a5"),
    )
    _write(
        root / "docs/architecture/evidence/dpa/probes/fixture-evidence-9cd4a7fc-wrt-ch006-20260729/results.json",
        _fixture_evidence("9cd4a7fcc69fd9db252133b3226696ce5bf6cada"),
    )
    _write(
        root / "docs/architecture/evidence/dpa/assessment/DP2_MAINTAINER_ASSESSMENT_RECORD_20260728.json",
        {"schema_version": 1, "status": "DP2_AUTHORIZED"},
    )
    evidence_input = root / "docs/architecture/evidence/dpa/probes/current"
    evidence_input.mkdir(parents=True)
    _write(root / DEFAULT_READINESS_PATH, _readiness_payload())


def _fixture_evidence(validation_ref: str) -> dict[str, object]:
    return {
        "schema_version": 1,
        "kind": "dpa_fixture_evidence",
        "validation_ref": validation_ref,
        "result_status": "FULL_FIXTURE_EVIDENCE_RECORDED",
        "full_evidence_by_family": {
            "PROBE-002": True,
            "RENDERER": True,
            "PROBE-003": True,
            "PROBE-004": True,
        },
        "rollback_cleanup_proven": True,
    }


def _readiness_payload() -> dict[str, object]:
    return {
        "schema_version": 1,
        "kind": "dpa_dp1_assessment_readiness",
        "status": "DP2_AUTHORIZED",
        "command_manifest_ack": "COMMAND_MANIFEST_ACK testsha",
        "evidence_inputs": [
            {
                "id": "current",
                "path": "docs/architecture/evidence/dpa/probes/current/",
                "result": "PASS_WITH_LIMITATIONS",
            }
        ],
        "probe_family_status": {
            "PROBE-001": "SATISFIED_FOR_CURRENT_KIT_REF",
            "PROBE-002": "SATISFIED_FOR_CURRENT_KIT_REF",
            "RENDERER": "SATISFIED_FOR_CURRENT_KIT_REF",
            "PROBE-003": "SATISFIED_FOR_CURRENT_KIT_REF",
            "PROBE-004": "SATISFIED_FOR_CURRENT_KIT_REF",
        },
        "selected_writer_status": {
            "WRT-CH-001": "AUTHORIZED_FOR_DP2_TARGET",
            "WRT-CH-002": "AUTHORIZED_FOR_DP2_TARGET",
            "WRT-CH-003": "AUTHORIZED_FOR_DP2_TARGET",
            "WRT-CH-004": "AUTHORIZED_FOR_DP2_TARGET",
            "WRT-CH-005": "EXTERNAL_HABITABILITY_ONLY",
            "WRT-CH-006": "GENERATED_OUTPUT_CONTRACT_ONLY",
        },
        "dp2_entry_status": {
            "architecture_staging": "SATISFIED_FOR_ARCHITECTURE_STAGING",
            "fresh_kit_baseline_recorded": "SATISFIED_FOR_THIS_RECORD",
            "probe_001_full_evidence": "SATISFIED_FOR_CURRENT_KIT_REF",
            "probe_002_full_evidence": "SATISFIED_FOR_CURRENT_KIT_REF",
            "renderer_full_evidence": "SATISFIED_FOR_CURRENT_KIT_REF",
            "probe_003_full_evidence": "SATISFIED_FOR_CURRENT_KIT_REF",
            "probe_004_full_evidence": "SATISFIED_FOR_CURRENT_KIT_REF",
            "maintainer_assessment": "RECORDED_DP2_AUTHORIZED",
            "first_dp2_target_scope": "SELECTED_WRT_CH001_CH002_CH003_CH004_HANDOFF_SCOPE",
            "rollback_cleanup_proven": "PROVEN_BY_NON_PRODUCTION_FIXTURE_EVIDENCE",
            "maintainer_authorization": "AUTHORIZED_BY_MAINTAINER_RECORD",
        },
        "claims": {
            "full_probe_pass_claimed": False,
            "dp2_authorized": True,
            "maintainer_authorization_recorded": True,
            "runtime_behavior_changed": False,
            "production_mutation_performed": False,
            "kit_conformance_claimed": False,
            "generated_outputs_manually_patched": False,
        },
    }


def test_post_dp2_scope_assessment_separates_dp2_from_kit_wide_dpa(tmp_path: Path) -> None:
    _fixture_root(tmp_path)

    result = evaluate_post_dp2_scope_assessment(tmp_path, validation_ref="test-ref")
    payload = result.as_dict()

    assert payload["result_status"] == "POST_DP2_SCOPE_ASSESSMENT_RECORDED"
    assert payload["dp2_status"] == "DP2_AUTHORIZED"
    assert payload["dp2_implementation_percent"] == 100
    assert payload["kit_wide_dpa_status"] == "DP3_DP5_NOT_COMPLETE"
    assert payload["kit_wide_dpa_conformance_claimed"] is False
    assert payload["final_closeout_ready"] is False
    assert {candidate["writer_id"] for candidate in payload["dp3"]["rollout_candidates"]} == {
        "WRT-CH-005",
        "WRT-CH-006",
    }
    assert all(candidate["entry_ready"] for candidate in payload["dp3"]["rollout_candidates"])
    assert "WRT-CH-005:dp3-adjudicated-rollout-result-missing" in payload["dp3"]["blockers"]
    assert "DP4-STATUS:reader-writer-generator-command-update-inventory-missing" in payload["dp4"]["blockers"]
    assert "strict:accepted-dp3-and-dp4-results-missing" in payload["dp5"]["blockers"]


def test_post_dp2_scope_assessment_blocks_missing_candidate_evidence(tmp_path: Path) -> None:
    _fixture_root(tmp_path)
    (
        tmp_path
        / "docs/architecture/evidence/dpa/probes/fixture-evidence-9cd4a7fc-wrt-ch006-20260729/results.json"
    ).unlink()

    result = evaluate_post_dp2_scope_assessment(tmp_path, validation_ref="test-ref")

    assert "WRT-CH-006:evidence-missing:docs/architecture/evidence/dpa/probes/fixture-evidence-9cd4a7fc-wrt-ch006-20260729/results.json" in result.dp3_blockers


def test_post_dp2_scope_assessment_cli_reports_without_global_closeout_claim(tmp_path: Path) -> None:
    _fixture_root(tmp_path)

    result = runner.invoke(
        app,
        ["dpa", "post-dp2-scope-assessment", "--root", str(tmp_path), "--validation-ref", "test-ref"],
    )

    assert result.exit_code == 0
    assert "DPA_POST_DP2_SCOPE_ASSESSMENT" in result.stdout
    assert "DP2_IMPLEMENTATION_PERCENT=100" in result.stdout
    assert "KIT_WIDE_DPA_STATUS=DP3_DP5_NOT_COMPLETE" in result.stdout
    assert "KIT_WIDE_DPA_CONFORMANCE_CLAIMED=false" in result.stdout


def test_post_dp2_scope_assessment_cli_can_require_closeout_ready(tmp_path: Path) -> None:
    _fixture_root(tmp_path)

    result = runner.invoke(
        app,
        [
            "dpa",
            "post-dp2-scope-assessment",
            "--root",
            str(tmp_path),
            "--require-closeout-ready",
        ],
    )

    assert result.exit_code == 1
    assert "FINAL_CLOSEOUT_READY=false" in result.stdout


def test_post_dp2_scope_assessment_cli_writes_evidence_under_assessment_root(tmp_path: Path) -> None:
    _fixture_root(tmp_path)
    output = "docs/architecture/evidence/dpa/assessment/post-dp2-scope/results.json"

    result = runner.invoke(
        app,
        [
            "dpa",
            "post-dp2-scope-assessment",
            "--root",
            str(tmp_path),
            "--output",
            output,
            "--execute",
            "--json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads((tmp_path / output).read_text(encoding="utf-8"))
    assert payload["kind"] == "dpa_post_dp2_scope_assessment"
    assert payload["kit_wide_dpa_status"] == "DP3_DP5_NOT_COMPLETE"


def test_post_dp2_scope_assessment_cli_rejects_evidence_outside_assessment_root(tmp_path: Path) -> None:
    _fixture_root(tmp_path)

    result = runner.invoke(
        app,
        [
            "dpa",
            "post-dp2-scope-assessment",
            "--root",
            str(tmp_path),
            "--output",
            "tmp/results.json",
            "--execute",
        ],
    )

    assert result.exit_code == 2
    assert not (tmp_path / "tmp/results.json").exists()
    assert "output_outside_dpa_assessment_evidence_root" in result.stdout
