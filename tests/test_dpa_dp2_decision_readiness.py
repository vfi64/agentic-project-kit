from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.dpa_dp2_decision_readiness import (
    DECISION_CONTROL_SURFACES,
    evaluate_dp2_decision_readiness,
)

runner = CliRunner()


def _touch(root: Path, path: str) -> None:
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("fixture\n", encoding="utf-8")


def _minimal_decision_root(root: Path) -> Path:
    command_reference = root / "docs/reference/agentic-kit-commands.json"
    command_reference.parent.mkdir(parents=True, exist_ok=True)
    command_reference.write_text(
        json.dumps({"schema_version": 2, "meta": {"manifest_sha": "testsha"}}),
        encoding="utf-8",
    )
    for path in DECISION_CONTROL_SURFACES:
        _touch(root, path)
    evidence_inputs = [
        ("current-kit-readonly-refresh", "docs/architecture/evidence/dpa/probes/dp1-readonly/"),
        (
            "current-kit-probe-001-registry-compatibility",
            "docs/architecture/evidence/dpa/probes/probe-001/",
        ),
        (
            "current-kit-probe-002-lifecycle-readiness-preflight",
            "docs/architecture/evidence/dpa/probes/probe-002/",
        ),
        (
            "current-kit-wrt-ch001-admin-refresh-observation",
            "docs/architecture/evidence/dpa/probes/wrt-ch001/",
        ),
        (
            "current-kit-probe-003-workflow-readiness-preflight",
            "docs/architecture/evidence/dpa/probes/probe-003/",
        ),
        (
            "current-kit-renderer-probe-readiness-preflight",
            "docs/architecture/evidence/dpa/probes/renderer/",
        ),
        (
            "current-kit-probe-004-migration-readiness-preflight",
            "docs/architecture/evidence/dpa/probes/probe-004/",
        ),
    ]
    for _, path in evidence_inputs:
        (root / path).mkdir(parents=True, exist_ok=True)
    record = root / "docs/architecture/evidence/dpa/assessment/dp1-assessment-readiness-20260728.json"
    record.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "kind": "dpa_dp1_assessment_readiness",
                "status": "DP2_BLOCKED",
                "command_manifest_ack": "COMMAND_MANIFEST_ACK testsha",
                "evidence_inputs": [
                    {"id": evidence_id, "path": path, "result": "PARTIAL_BLOCKED_FOR_DP2"}
                    for evidence_id, path in evidence_inputs
                ],
                "probe_family_status": {
                    "PROBE-001": "SATISFIED_FOR_CURRENT_KIT_REF",
                    "PROBE-002": "PARTIAL_BLOCKED_FOR_DP2",
                    "RENDERER": "PARTIAL_BLOCKED_FOR_DP2",
                    "PROBE-003": "PARTIAL_BLOCKED_FOR_DP2",
                    "PROBE-004": "PARTIAL_BLOCKED_FOR_DP2",
                },
                "dp2_entry_status": {
                    "architecture_staging": "SATISFIED_FOR_ARCHITECTURE_STAGING",
                    "fresh_kit_baseline_recorded": "SATISFIED_FOR_THIS_RECORD",
                    "probe_001_full_evidence": "SATISFIED_FOR_CURRENT_KIT_REF",
                    "probe_002_full_evidence": "BLOCKED",
                    "renderer_full_evidence": "BLOCKED",
                    "probe_003_full_evidence": "BLOCKED",
                    "probe_004_full_evidence": "BLOCKED",
                    "maintainer_assessment": "BLOCKED",
                    "first_dp2_target_scope": "BLOCKED",
                    "rollback_cleanup_proven": "BLOCKED",
                    "maintainer_authorization": "BLOCKED",
                },
                "claims": {
                    "full_probe_pass_claimed": False,
                    "dp2_authorized": False,
                    "runtime_behavior_changed": False,
                    "production_mutation_performed": False,
                    "kit_conformance_claimed": False,
                    "generated_outputs_manually_patched": False,
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return record


def test_dp2_decision_readiness_reports_ready_but_blocked(tmp_path: Path) -> None:
    _minimal_decision_root(tmp_path)

    result = evaluate_dp2_decision_readiness(tmp_path, validation_ref="test-ref")

    assert result.structural_ok
    assert result.result_status == "READY_FOR_MAINTAINER_DECISION_DP2_BLOCKED"
    assert result.implementation_percent == 48
    assert "maintainer_authorization" in result.blockers
    payload = result.as_dict()
    assert payload["validation_ref"] == "test-ref"
    assert payload["candidate_first_dp2_target_scope"]["not_authorization"] is True
    assert payload["claims"]["maintainer_authorization_recorded"] is False
    assert payload["claims"]["dp2_authorized"] is False


def test_dp2_decision_readiness_filters_satisfied_actions(tmp_path: Path) -> None:
    record = _minimal_decision_root(tmp_path)
    data = json.loads(record.read_text(encoding="utf-8"))
    dp2_entry = data["dp2_entry_status"]
    dp2_entry.update(
        {
            "maintainer_assessment": "RECORDED_DP2_BLOCKED",
            "first_dp2_target_scope": "SELECTED_WRT_CH001_HANDOFF_SCOPE",
            "rollback_cleanup_proven": "PROVEN_BY_NON_PRODUCTION_FIXTURE_EVIDENCE",
        }
    )
    record.write_text(json.dumps(data, indent=2), encoding="utf-8")

    result = evaluate_dp2_decision_readiness(tmp_path)

    actions = result.as_dict()["required_maintainer_actions"]
    assert [item["id"] for item in actions] == ["record_dp2_authorization_token"]


def test_dp2_decision_readiness_blocks_missing_control_surface(tmp_path: Path) -> None:
    _minimal_decision_root(tmp_path)
    (tmp_path / "docs/architecture/dpa/probes/DP1_SELECTED_WRITER_FIXTURE_PLAN_20260727.md").unlink()

    result = evaluate_dp2_decision_readiness(tmp_path)

    assert result.result_status == "STRUCTURAL_BLOCK"
    assert any(finding.code == "decision-control-surface-missing" for finding in result.findings)


def test_dp2_decision_readiness_blocks_missing_decision_requirement(tmp_path: Path) -> None:
    record = _minimal_decision_root(tmp_path)
    data = json.loads(record.read_text(encoding="utf-8"))
    del data["dp2_entry_status"]["rollback_cleanup_proven"]
    record.write_text(json.dumps(data, indent=2), encoding="utf-8")

    result = evaluate_dp2_decision_readiness(tmp_path)

    assert result.result_status == "STRUCTURAL_BLOCK"
    assert any(finding.code == "decision-requirement-missing" for finding in result.findings)


def test_dp2_decision_readiness_cli_reports_ready_without_failure(tmp_path: Path) -> None:
    _minimal_decision_root(tmp_path)

    result = runner.invoke(app, ["dpa", "dp2-decision-readiness", "--root", str(tmp_path)])

    assert result.exit_code == 0
    assert "DPA_DP2_DECISION_READINESS" in result.stdout
    assert "STATUS=READY_FOR_MAINTAINER_DECISION_DP2_BLOCKED" in result.stdout
    assert "READINESS_BLOCKER=maintainer_authorization" in result.stdout


def test_dp2_decision_readiness_cli_can_record_explicit_validation_ref(tmp_path: Path) -> None:
    _minimal_decision_root(tmp_path)

    result = runner.invoke(
        app,
        [
            "dpa",
            "dp2-decision-readiness",
            "--root",
            str(tmp_path),
            "--validation-ref",
            "target-ref",
        ],
    )

    assert result.exit_code == 0
    assert "VALIDATION_REF=target-ref" in result.stdout


def test_dp2_decision_readiness_cli_writes_evidence_under_assessment_root(tmp_path: Path) -> None:
    _minimal_decision_root(tmp_path)
    output = "docs/architecture/evidence/dpa/assessment/dp2-decision-current/results.json"

    result = runner.invoke(
        app,
        [
            "dpa",
            "dp2-decision-readiness",
            "--root",
            str(tmp_path),
            "--output",
            output,
            "--execute",
            "--json",
        ],
    )

    assert result.exit_code == 0
    assert (tmp_path / output).exists()
    payload = json.loads((tmp_path / output).read_text(encoding="utf-8"))
    assert payload["result_status"] == "READY_FOR_MAINTAINER_DECISION_DP2_BLOCKED"


def test_dp2_decision_readiness_cli_rejects_evidence_outside_assessment_root(tmp_path: Path) -> None:
    _minimal_decision_root(tmp_path)

    result = runner.invoke(
        app,
        [
            "dpa",
            "dp2-decision-readiness",
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
