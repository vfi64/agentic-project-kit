from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.dpa_dp3_dp4_adjudication import (
    DEFAULT_DP3_DP4_ADJUDICATION_RECORD_PATH,
    evaluate_dp3_dp4_adjudication_record,
)
from agentic_project_kit.dpa_dp5_stage_adoption import (
    DEFAULT_DP5_STAGE_RECORD_PATH,
    evaluate_dp5_stage_record,
)
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


def _write_valid_dp3_dp4_adjudication_record(root: Path) -> None:
    post_dp2 = "docs/architecture/evidence/dpa/assessment/post-dp2-scope-6a59bf43-20260801/results.json"
    _write(root / post_dp2, {"schema_version": 1, "kind": "dpa_post_dp2_scope_assessment"})
    fixture_005 = "docs/architecture/evidence/dpa/probes/fixture-evidence-0b985a22-wrt-ch005-20260729/results.json"
    fixture_006 = "docs/architecture/evidence/dpa/probes/fixture-evidence-9cd4a7fc-wrt-ch006-20260729/results.json"
    dp2_record = "docs/architecture/evidence/dpa/assessment/DP2_MAINTAINER_ASSESSMENT_RECORD_20260728.json"
    claims = {
        "kit_wide_dpa_conformance_claimed": False,
        "dp5_strict_enforced": False,
        "production_mutation_performed": False,
        "generated_outputs_manually_patched": False,
        "stable_dpa_claimed": False,
    }
    _write(
        root / DEFAULT_DP3_DP4_ADJUDICATION_RECORD_PATH,
        {
            "schema_version": 1,
            "kind": "dpa_dp3_dp4_adjudication_record",
            "status": "DP3_DP4_BOUNDED_ADJUDICATION_ACCEPTED",
            "status_date": "2026-08-01",
            "validation_ref": "test-ref",
            "post_dp2_scope_assessment": post_dp2,
            "maintainer": "Maintainer instruction recorded in Codex chat, 2026-08-01: continue bounded DPA DP3-DP5 work.",
            "decision_token": "DPA_DP3_DP4_BOUNDED_ADJUDICATION_ACCEPTED",
            "dp3_scope": {
                "status": "ACCEPTED_FOR_BOUNDED_SLICE",
                "rollout_targets": [
                    _dp3_target(
                        writer_id="WRT-CH-005",
                        target_identity="EXTERNAL_WORKSPACE_INITIALIZATION_TEMPLATE",
                        target_path=".agentic/dpa/workspace_init_projection.json",
                        source_authority="DPA-WORKSPACE-INIT-HANDOFF-TEMPLATE-v1",
                        source_paths=list(DPA_WORKSPACE_INIT_SOURCE_PATHS),
                        document_form="external-generated-initialization-manifest",
                        implementation_result_ref="f653bbbb",
                        evidence=fixture_005,
                        claims=claims,
                    ),
                    _dp3_target(
                        writer_id="WRT-CH-006",
                        target_identity="GENERATED_SUCCESSOR_HANDOFF_PACKAGE_AND_PROMPT_PROJECTIONS",
                        target_path="docs/reports/handoff-packages/latest/",
                        source_authority="DPA-GENERATED-SUCCESSOR-HANDOFF-PROJECTION-v1",
                        source_paths=list(DPA_SUCCESSOR_PROJECTION_SOURCE_PATHS),
                        document_form="command-generated-successor-handoff-projection",
                        implementation_result_ref="644f470a",
                        evidence=fixture_006,
                        claims=claims,
                    ),
                ],
            },
            "dp4_scope": {
                "status": "ACCEPTED_FOR_BOUNDED_STATUS_AUTHORITY_SLICE",
                "status_authority_candidates": [
                    _dp4_candidate(
                        candidate_id="DP4-CURRENT-HANDOFF",
                        path="docs/handoff/CURRENT_HANDOFF.md",
                        decision="MANUAL_PRESERVATION_WITH_LIFECYCLE_OWNED_GENERATED_BLOCK",
                        document_form="hybrid-current-state-document",
                        target_identity="CURRENT_HANDOFF_SELF_HOSTING_TARGET",
                        dpa600_evidence=fixture_006,
                        dpa700_evidence=dp2_record,
                        preservation_status="MANUAL_PRESERVATION_RECORDED",
                        claims=claims,
                    ),
                    _dp4_candidate(
                        candidate_id="DP4-STATUS",
                        path="docs/STATUS.md",
                        decision="NO_MIGRATION_MANUAL_STATUS_DASHBOARD",
                        document_form="manual-current-state-dashboard",
                        target_identity="PROJECT_STATUS_CURRENT_STATE",
                        dpa600_evidence=fixture_006,
                        dpa700_evidence=post_dp2,
                        preservation_status="NO_MIGRATION_RECORDED",
                        claims=claims,
                    ),
                    _dp4_candidate(
                        candidate_id="DP4-SUCCESSOR-PROJECTIONS",
                        path="docs/reports/handoff-packages/latest/ and docs/handoff/NEXT_CHAT_BOOTSTRAP.md",
                        decision="NO_MIGRATION_COMMAND_GENERATED_OUTPUT_BOUNDARY",
                        document_form="command-generated-successor-handoff-projection-family",
                        target_identity="GENERATED_SUCCESSOR_HANDOFF_PACKAGE_AND_PROMPT_PROJECTIONS",
                        dpa600_evidence=fixture_006,
                        dpa700_evidence=fixture_006,
                        preservation_status="COMMAND_CONTRACT_BOUNDARY_RECORDED",
                        claims=claims,
                    ),
                ],
            },
            "dp5": {
                "next_stage_authorized": False,
                "stage_transition": "NOT_AUTHORIZED_IN_THIS_RECORD",
            },
            "claims": {
                "dp3_complete_for_bounded_slice": True,
                "dp4_complete_for_bounded_slice": True,
                **claims,
            },
        },
    )


def _write_valid_dp5_stage_record(root: Path) -> None:
    post_dp2 = "docs/architecture/evidence/dpa/assessment/post-dp2-scope-6a59bf43-20260801/results.json"
    dp3_dp4 = DEFAULT_DP3_DP4_ADJUDICATION_RECORD_PATH.as_posix()
    _write(
        root / DEFAULT_DP5_STAGE_RECORD_PATH,
        {
            "schema_version": 1,
            "kind": "dpa_dp5_stage_record",
            "status": "DP5_OBSERVE_STAGE_ADOPTED",
            "stage": "observe",
            "status_date": "2026-08-01",
            "validation_ref": "test-ref",
            "maintainer": "Maintainer instruction recorded in Codex chat, 2026-08-01: continue bounded DP5 work.",
            "decision_token": "DPA_DP5_OBSERVE_STAGE_AUTHORIZED",
            "target_scope": {
                "id": "DPA_POST_DP2_DP3_DP4_ACCEPTED_SCOPE",
                "enforcement_stage": "observe",
                "evidence": [post_dp2, dp3_dp4],
            },
            "gate_set": {
                "id": "DPA_DP5_OBSERVE_GATE_SET_V1",
                "stage_behavior": "observe-only",
                "blocks_unrelated_work": False,
                "commands": [
                    {
                        "command": "agentic-kit dpa dp3-dp4-adjudication-check --require-valid",
                        "evidence": [dp3_dp4],
                    },
                    {
                        "command": "agentic-kit dpa post-dp2-scope-assessment",
                        "evidence": [post_dp2],
                    },
                ],
            },
            "findings_mapping": {
                "unknown_mutation_safety_finding": {
                    "disposition": "fail_closed_for_mutation_safety",
                },
                "stage_decision": "record_only_no_new_blocking",
            },
            "rollback": {
                "less_strict_stage": "pre-dp5",
                "tested_or_adjudicated": True,
                "evidence": [post_dp2],
            },
            "claims": {
                "observe_stage_active": True,
                "warn_stage_active": False,
                "block_new_stage_active": False,
                "strict_stage_active": False,
                "kit_wide_dpa_conformance_claimed": False,
                "production_mutation_performed": False,
                "generated_outputs_manually_patched": False,
                "stable_dpa_claimed": False,
            },
        },
    )


def _dp3_target(
    *,
    writer_id: str,
    target_identity: str,
    target_path: str,
    source_authority: str,
    source_paths: list[str],
    document_form: str,
    implementation_result_ref: str,
    evidence: str,
    claims: dict[str, bool],
) -> dict[str, object]:
    return {
        "writer_id": writer_id,
        "target_identity": target_identity,
        "target_path": target_path,
        "source_authority": source_authority,
        "source_paths": source_paths,
        "document_form": document_form,
        "implementation_result_ref": implementation_result_ref,
        "reader_inventory": [{"id": f"{writer_id}-reader", "path": "tests/test_dpa_post_dp2_scope_assessment.py"}],
        "writer_inventory": [{"id": f"{writer_id}-writer", "path": source_paths[0]}],
        "dpa_600": {"status": "SATISFIED_FOR_CURRENT_KIT_REF", "evidence": [evidence]},
        "dpa_700": {"status": "SATISFIED_FOR_CURRENT_KIT_REF", "evidence": [evidence]},
        "tests": {
            "positive": ["tests/test_dpa_post_dp2_scope_assessment.py::positive"],
            "negative": ["tests/test_dpa_post_dp2_scope_assessment.py::negative"],
        },
        "rollout_evidence": [evidence],
        "rollback": {"status": "NO_PRODUCTION_MIGRATION", "independently_revertible": True},
        "adjudication": {
            "status": "ACCEPTED_FOR_BOUNDED_DP3_ROLLOUT",
            "maintainer_accepted": True,
        },
        "claims": claims,
    }


def _dp4_candidate(
    *,
    candidate_id: str,
    path: str,
    decision: str,
    document_form: str,
    target_identity: str,
    dpa600_evidence: str,
    dpa700_evidence: str,
    preservation_status: str,
    claims: dict[str, bool],
) -> dict[str, object]:
    return {
        "id": candidate_id,
        "path": path,
        "decision": decision,
        "document_form": document_form,
        "target_identity": target_identity,
        "reader_inventory": [{"id": f"{candidate_id}-reader", "path": "AGENTS.md"}],
        "writer_inventory": [{"id": f"{candidate_id}-writer", "path": "src/agentic_project_kit"}],
        "generator_inventory": [{"id": f"{candidate_id}-generator", "path": "src/agentic_project_kit"}],
        "command_update_inventory": [{"command": "agentic-kit transfer post-merge-settle --after-pr"}],
        "dpa_600": {"status": "SATISFIED_FOR_CURRENT_KIT_REF", "evidence": [dpa600_evidence]},
        "dpa_700": {"status": "NO_MIGRATION_OR_MANUAL_PRESERVATION", "evidence": [dpa700_evidence]},
        "rollback_or_preservation": {
            "status": preservation_status,
            "evidence": [dpa700_evidence],
        },
        "status_authority_consequences": "Manual/status authority is preserved for this bounded candidate.",
        "adjudication": {
            "status": "ACCEPTED_FOR_BOUNDED_DP4_NO_MIGRATION_OR_MANUAL_PRESERVATION",
            "maintainer_accepted": True,
        },
        "claims": claims,
    }


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


def test_dp3_dp4_adjudication_record_clears_only_dp3_dp4_blockers(tmp_path: Path) -> None:
    _fixture_root(tmp_path)
    _write_valid_dp3_dp4_adjudication_record(tmp_path)

    record = evaluate_dp3_dp4_adjudication_record(tmp_path, validation_ref="test-ref")
    result = evaluate_post_dp2_scope_assessment(tmp_path, validation_ref="test-ref")
    payload = result.as_dict()

    assert record.result_status == "VALID_DP3_DP4_ADJUDICATION_RECORD"
    assert payload["dp3"]["status"] == "ADJUDICATED_FOR_BOUNDED_SLICE"
    assert payload["dp4"]["status"] == "ADJUDICATED_FOR_BOUNDED_STATUS_AUTHORITY_SLICE"
    assert payload["dp3"]["blockers"] == []
    assert payload["dp4"]["blockers"] == []
    assert payload["kit_wide_dpa_status"] == "DP5_NOT_COMPLETE"
    assert {candidate["status"] for candidate in payload["dp3"]["rollout_candidates"]} == {
        "ADJUDICATED_FOR_BOUNDED_DP3_ROLLOUT"
    }
    assert {candidate["status"] for candidate in payload["dp4"]["status_authority_candidates"]} == {
        "ADJUDICATED_FOR_BOUNDED_DP4_EXIT"
    }
    assert "strict:accepted-dp3-and-dp4-results-missing" not in payload["dp5"]["blockers"]
    assert "strict:exact-stage-authorization-record-missing" in payload["dp5"]["blockers"]
    assert payload["final_closeout_ready"] is False
    assert payload["kit_wide_dpa_conformance_claimed"] is False


def test_dp3_dp4_adjudication_check_blocks_missing_evidence(tmp_path: Path) -> None:
    _fixture_root(tmp_path)
    _write_valid_dp3_dp4_adjudication_record(tmp_path)
    (
        tmp_path
        / "docs/architecture/evidence/dpa/probes/fixture-evidence-0b985a22-wrt-ch005-20260729/results.json"
    ).unlink()

    result = evaluate_dp3_dp4_adjudication_record(tmp_path, validation_ref="test-ref")

    assert result.result_status == "INVALID_DP3_DP4_ADJUDICATION_RECORD"
    assert any(finding.code == "dp3-rollout-evidence-missing" for finding in result.findings)


def test_dp3_dp4_adjudication_check_cli_reports_valid_record(tmp_path: Path) -> None:
    _fixture_root(tmp_path)
    _write_valid_dp3_dp4_adjudication_record(tmp_path)

    result = runner.invoke(
        app,
        [
            "dpa",
            "dp3-dp4-adjudication-check",
            "--root",
            str(tmp_path),
            "--validation-ref",
            "test-ref",
            "--require-valid",
        ],
    )

    assert result.exit_code == 0
    assert "DPA_DP3_DP4_ADJUDICATION_CHECK" in result.stdout
    assert "STATUS=VALID_DP3_DP4_ADJUDICATION_RECORD" in result.stdout
    assert "DP5_NEXT_STAGE_AUTHORIZED=false" in result.stdout


def test_dp5_observe_record_clears_only_observe_stage_blockers(tmp_path: Path) -> None:
    _fixture_root(tmp_path)
    _write_valid_dp3_dp4_adjudication_record(tmp_path)
    _write_valid_dp5_stage_record(tmp_path)

    stage = evaluate_dp5_stage_record(tmp_path, validation_ref="test-ref")
    result = evaluate_post_dp2_scope_assessment(tmp_path, validation_ref="test-ref")
    payload = result.as_dict()

    assert stage.result_status == "VALID_DP5_STAGE_RECORD"
    assert payload["kit_wide_dpa_status"] == "DP5_OBSERVE_ADOPTED_STRICT_NOT_COMPLETE"
    assert payload["dp5"]["status"] == "OBSERVE_ADOPTED_STRICT_LIFECYCLE_NOT_COMPLETE"
    assert payload["dp5"]["strict_lifecycle_stages"][0]["stage"] == "observe"
    assert payload["dp5"]["strict_lifecycle_stages"][0]["status"] == "ADOPTED_OBSERVE"
    assert not any(blocker.startswith("observe:") for blocker in payload["dp5"]["blockers"])
    assert "strict:exact-stage-authorization-record-missing" in payload["dp5"]["blockers"]
    assert payload["blocker_count"] == 6


def test_dp5_stage_check_cli_reports_observe_only(tmp_path: Path) -> None:
    _fixture_root(tmp_path)
    _write_valid_dp3_dp4_adjudication_record(tmp_path)
    _write_valid_dp5_stage_record(tmp_path)

    result = runner.invoke(
        app,
        [
            "dpa",
            "dp5-stage-check",
            "--root",
            str(tmp_path),
            "--validation-ref",
            "test-ref",
            "--require-valid",
        ],
    )

    assert result.exit_code == 0
    assert "DPA_DP5_STAGE_CHECK" in result.stdout
    assert "STATUS=VALID_DP5_STAGE_RECORD" in result.stdout
    assert "DP5_STAGE=observe|status=ADOPTED" in result.stdout
    assert "DP5_STAGE=strict|status=BLOCKED" in result.stdout


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
