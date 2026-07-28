from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.dpa_maintainer_record_check import evaluate_dp2_maintainer_record

runner = CliRunner()


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _touch(root: Path, path: str) -> None:
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("fixture\n", encoding="utf-8")


def _template_payload() -> dict[str, object]:
    return {
        "schema_version": 1,
        "kind": "dpa_dp2_maintainer_assessment_record",
        "status": "TEMPLATE_NOT_ASSESSED",
        "template": True,
        "readiness_record": "docs/architecture/evidence/dpa/assessment/dp1-assessment-readiness-20260728.json",
        "decision_readiness_evidence": "docs/architecture/evidence/dpa/assessment/dp2-decision/results.json",
        "maintainer": "PENDING_MAINTAINER",
        "decision_token": "PENDING_DECISION",
        "probe_dispositions": {
            "PROBE-002": {"status": "BLOCKED", "evidence": []},
            "RENDERER": {"status": "BLOCKED", "evidence": []},
            "PROBE-003": {"status": "BLOCKED", "evidence": []},
            "PROBE-004": {"status": "BLOCKED", "evidence": []},
        },
        "first_dp2_target_scope": {
            "status": "UNSELECTED",
            "target_path": "docs/handoff/CURRENT_HANDOFF.md",
            "selected_writers": ["WRT-CH-001"],
            "deferred_writers": [],
            "excluded_writers": ["WRT-CH-005", "WRT-CH-006"],
        },
        "rollback_cleanup": {"status": "NOT_PROVEN", "evidence": []},
        "claims": {
            "maintainer_assessment_recorded": False,
            "maintainer_authorization_recorded": False,
            "dp2_authorized": False,
            "runtime_behavior_changed": False,
            "production_mutation_performed": False,
            "kit_conformance_claimed": False,
            "generated_outputs_manually_patched": False,
        },
    }


def _minimal_record_root(root: Path, payload: dict[str, object] | None = None) -> Path:
    _touch(root, "docs/handoff/CURRENT_HANDOFF.md")
    _touch(root, "docs/architecture/evidence/dpa/assessment/dp1-assessment-readiness-20260728.json")
    _touch(root, "docs/architecture/evidence/dpa/assessment/dp2-decision/results.json")
    record = root / "docs/architecture/evidence/dpa/assessment/maintainer-record.json"
    _write_json(record, payload or _template_payload())
    return record


def _authorized_payload() -> dict[str, object]:
    payload = _template_payload()
    payload.update(
        {
            "status": "DP2_AUTHORIZED",
            "template": False,
            "maintainer": "Maintainer",
            "decision_token": "DPA_DP2_AUTHORIZED",
            "probe_dispositions": {
                "PROBE-002": {
                    "status": "SATISFIED_FOR_CURRENT_KIT_REF",
                    "evidence": ["docs/architecture/evidence/dpa/probes/probe-002/results.json"],
                },
                "RENDERER": {
                    "status": "SATISFIED_FOR_CURRENT_KIT_REF",
                    "evidence": ["docs/architecture/evidence/dpa/probes/renderer/results.json"],
                },
                "PROBE-003": {
                    "status": "SATISFIED_FOR_CURRENT_KIT_REF",
                    "evidence": ["docs/architecture/evidence/dpa/probes/probe-003/results.json"],
                },
                "PROBE-004": {
                    "status": "SATISFIED_FOR_CURRENT_KIT_REF",
                    "evidence": ["docs/architecture/evidence/dpa/probes/probe-004/results.json"],
                },
            },
            "first_dp2_target_scope": {
                "status": "SELECTED",
                "target_path": "docs/handoff/CURRENT_HANDOFF.md",
                "selected_writers": ["WRT-CH-001"],
                "deferred_writers": ["WRT-CH-002", "WRT-CH-003", "WRT-CH-004"],
                "excluded_writers": ["WRT-CH-005", "WRT-CH-006"],
            },
            "rollback_cleanup": {
                "status": "PROVEN",
                "evidence": ["docs/architecture/evidence/dpa/assessment/rollback-cleanup.json"],
            },
            "claims": {
                "maintainer_assessment_recorded": True,
                "maintainer_authorization_recorded": True,
                "dp2_authorized": True,
                "runtime_behavior_changed": False,
                "production_mutation_performed": False,
                "kit_conformance_claimed": False,
                "generated_outputs_manually_patched": False,
            },
        }
    )
    return payload


def _blocked_assessment_payload() -> dict[str, object]:
    payload = _template_payload()
    payload.update(
        {
            "status": "DP2_BLOCKED",
            "template": False,
            "maintainer": "Maintainer",
            "decision_token": "DPA_DP2_BLOCKED_PENDING_PROBES",
            "first_dp2_target_scope": {
                "status": "SELECTED",
                "target_path": "docs/handoff/CURRENT_HANDOFF.md",
                "selected_writers": ["WRT-CH-001"],
                "deferred_writers": ["WRT-CH-002", "WRT-CH-003", "WRT-CH-004"],
                "excluded_writers": ["WRT-CH-005", "WRT-CH-006"],
            },
            "claims": {
                "maintainer_assessment_recorded": True,
                "maintainer_authorization_recorded": False,
                "dp2_authorized": False,
                "runtime_behavior_changed": False,
                "production_mutation_performed": False,
                "kit_conformance_claimed": False,
                "generated_outputs_manually_patched": False,
            },
        }
    )
    return payload


def test_maintainer_record_template_is_ready_but_blocked(tmp_path: Path) -> None:
    record = _minimal_record_root(tmp_path)

    result = evaluate_dp2_maintainer_record(tmp_path, record_path=record, validation_ref="test-ref")

    assert result.structural_ok
    assert result.result_status == "TEMPLATE_READY_DP2_BLOCKED"
    payload = result.as_dict()
    assert payload["validation_ref"] == "test-ref"
    assert payload["record_summary"]["decision_token"] == "PENDING_DECISION"
    assert payload["claims"]["dp2_authorized"] is False
    assert any(item["id"] == "record-maintainer-authorization" for item in payload["action_items"])


def test_maintainer_record_check_accepts_recorded_blocked_assessment(tmp_path: Path) -> None:
    record = _minimal_record_root(tmp_path, _blocked_assessment_payload())

    result = evaluate_dp2_maintainer_record(tmp_path, record_path=record, validation_ref="test-ref")

    assert result.structural_ok
    assert result.result_status == "VALID_BLOCKED_RECORD"
    payload = result.as_dict()
    assert payload["record_status"] == "DP2_BLOCKED"
    assert payload["record_summary"]["target_scope_status"] == "SELECTED"
    assert payload["claims"]["maintainer_assessment_recorded"] is True
    assert payload["claims"]["maintainer_authorization_recorded"] is False
    assert payload["claims"]["dp2_authorized"] is False
    assert payload["action_item_count"] == 3
    assert not any(item["id"] == "select-or-defer-writers" for item in payload["action_items"])


def test_maintainer_record_check_reports_missing_record(tmp_path: Path) -> None:
    result = evaluate_dp2_maintainer_record(tmp_path, record_path="missing.json")

    assert result.result_status == "STRUCTURAL_BLOCK"
    assert [finding.code for finding in result.findings] == ["maintainer-record-missing"]


def test_maintainer_record_check_rejects_premature_authorization_claim(tmp_path: Path) -> None:
    payload = _template_payload()
    claims = dict(payload["claims"])  # type: ignore[arg-type]
    claims["dp2_authorized"] = True
    payload["claims"] = claims
    record = _minimal_record_root(tmp_path, payload)

    result = evaluate_dp2_maintainer_record(tmp_path, record_path=record)

    assert result.result_status == "STRUCTURAL_BLOCK"
    assert any(finding.code == "premature-authorization-claim" for finding in result.findings)


def test_maintainer_record_check_rejects_template_assessment_claim(tmp_path: Path) -> None:
    payload = _template_payload()
    claims = dict(payload["claims"])  # type: ignore[arg-type]
    claims["maintainer_assessment_recorded"] = True
    payload["claims"] = claims
    record = _minimal_record_root(tmp_path, payload)

    result = evaluate_dp2_maintainer_record(tmp_path, record_path=record)

    assert result.result_status == "STRUCTURAL_BLOCK"
    assert any(finding.code == "premature-assessment-claim" for finding in result.findings)


def test_maintainer_record_check_accepts_complete_authorization_record(tmp_path: Path) -> None:
    record = _minimal_record_root(tmp_path, _authorized_payload())

    result = evaluate_dp2_maintainer_record(tmp_path, record_path=record)

    assert result.structural_ok
    assert result.result_status == "VALID_AUTHORIZATION_RECORD"
    assert result.action_items == ()


def test_maintainer_record_check_rejects_authorized_record_with_blocked_probe(tmp_path: Path) -> None:
    payload = _authorized_payload()
    dispositions = dict(payload["probe_dispositions"])  # type: ignore[arg-type]
    dispositions["PROBE-004"] = {"status": "BLOCKED", "evidence": []}
    payload["probe_dispositions"] = dispositions
    record = _minimal_record_root(tmp_path, payload)

    result = evaluate_dp2_maintainer_record(tmp_path, record_path=record)

    assert result.result_status == "STRUCTURAL_BLOCK"
    assert any(finding.code == "authorized-with-blocked-probe" for finding in result.findings)


def test_maintainer_record_check_cli_requires_authorization(tmp_path: Path) -> None:
    record = _minimal_record_root(tmp_path)

    result = runner.invoke(
        app,
        ["dpa", "maintainer-record-check", "--root", str(tmp_path), "--record", str(record), "--require-authorization"],
    )

    assert result.exit_code == 1
    assert "STATUS=TEMPLATE_READY_DP2_BLOCKED" in result.stdout


def test_maintainer_record_check_cli_writes_evidence_under_assessment_root(tmp_path: Path) -> None:
    record = _minimal_record_root(tmp_path)
    output = "docs/architecture/evidence/dpa/assessment/maintainer-record-check/results.json"

    result = runner.invoke(
        app,
        [
            "dpa",
            "maintainer-record-check",
            "--root",
            str(tmp_path),
            "--record",
            str(record),
            "--output",
            output,
            "--execute",
            "--json",
        ],
    )

    assert result.exit_code == 0
    assert (tmp_path / output).exists()
    payload = json.loads((tmp_path / output).read_text(encoding="utf-8"))
    assert payload["result_status"] == "TEMPLATE_READY_DP2_BLOCKED"


def test_maintainer_record_check_cli_rejects_evidence_outside_assessment_root(tmp_path: Path) -> None:
    record = _minimal_record_root(tmp_path)

    result = runner.invoke(
        app,
        [
            "dpa",
            "maintainer-record-check",
            "--root",
            str(tmp_path),
            "--record",
            str(record),
            "--output",
            "tmp/results.json",
            "--execute",
        ],
    )

    assert result.exit_code == 2
    assert not (tmp_path / "tmp/results.json").exists()
    assert "output_outside_dpa_assessment_evidence_root" in result.stdout
