from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.dpa_readiness import evaluate_dpa_readiness

runner = CliRunner()


def _write(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _record(root: Path, overrides: dict[str, object] | None = None) -> Path:
    evidence_dir = root / "docs/architecture/evidence/dpa/probes/current"
    manifest = root / "docs/architecture/dpa/probes/fixtures/manifest.json"
    command_reference = root / "docs/reference/agentic-kit-commands.json"
    evidence_dir.mkdir(parents=True)
    manifest.parent.mkdir(parents=True)
    command_reference.parent.mkdir(parents=True)
    manifest.write_text("{}", encoding="utf-8")
    command_reference.write_text(
        json.dumps({"schema_version": 2, "meta": {"manifest_sha": "testsha"}}),
        encoding="utf-8",
    )
    payload: dict[str, object] = {
        "schema_version": 1,
        "kind": "dpa_dp1_assessment_readiness",
        "status": "DP2_BLOCKED",
        "command_manifest_ack": "COMMAND_MANIFEST_ACK testsha",
        "evidence_inputs": [
            {
                "id": "current",
                "path": "docs/architecture/evidence/dpa/probes/current/",
                "result": "PASS_WITH_LIMITATIONS",
            },
            {
                "id": "manifest",
                "path": "docs/architecture/dpa/probes/fixtures/manifest.json",
                "result": "PREPARED_NOT_EXECUTED",
            },
        ],
        "probe_family_status": {
            "PROBE-001": "PARTIAL_BLOCKED_FOR_DP2",
            "PROBE-002": "PARTIAL_BLOCKED_FOR_DP2",
            "RENDERER": "PARTIAL_BLOCKED_FOR_DP2",
            "PROBE-003": "PARTIAL_BLOCKED_FOR_DP2",
            "PROBE-004": "PARTIAL_BLOCKED_FOR_DP2",
        },
        "dp2_entry_status": {
            "architecture_staging": "SATISFIED_FOR_ARCHITECTURE_STAGING",
            "probe_001_full_evidence": "BLOCKED",
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
    }
    if overrides:
        payload.update(overrides)
    record = root / "readiness.json"
    _write(record, payload)
    return record


def test_dpa_readiness_accepts_honest_blocked_record(tmp_path: Path) -> None:
    record = _record(tmp_path)

    result = evaluate_dpa_readiness(tmp_path, readiness_path=record)

    assert result.ok
    assert result.status == "DP2_BLOCKED"
    assert not result.dp2_ready
    assert result.implementation_percent == 40
    assert "probe_001_full_evidence" in result.blockers


def test_dpa_readiness_rejects_unsafe_claim(tmp_path: Path) -> None:
    record = _record(
        tmp_path,
        {
            "claims": {
                "full_probe_pass_claimed": True,
                "dp2_authorized": False,
                "runtime_behavior_changed": False,
                "production_mutation_performed": False,
                "kit_conformance_claimed": False,
                "generated_outputs_manually_patched": False,
            }
        },
    )

    result = evaluate_dpa_readiness(tmp_path, readiness_path=record)

    assert not result.ok
    assert [finding.code for finding in result.findings] == ["unsafe-claim"]


def test_dpa_readiness_rejects_authorized_record_with_blockers(tmp_path: Path) -> None:
    record = _record(tmp_path, {"status": "DP2_AUTHORIZED"})

    result = evaluate_dpa_readiness(tmp_path, readiness_path=record)

    assert not result.ok
    assert [finding.code for finding in result.findings] == ["authorized-with-blockers"]


def test_dpa_readiness_rejects_missing_evidence_path(tmp_path: Path) -> None:
    record = _record(
        tmp_path,
        {
            "evidence_inputs": [
                {
                    "id": "missing",
                    "path": "docs/architecture/evidence/dpa/probes/missing/",
                    "result": "NOT_RUN",
                }
            ]
        },
    )

    result = evaluate_dpa_readiness(tmp_path, readiness_path=record)

    assert not result.ok
    assert [finding.code for finding in result.findings] == ["evidence-input-missing"]


def test_dpa_readiness_rejects_command_manifest_ack_drift(tmp_path: Path) -> None:
    record = _record(tmp_path, {"command_manifest_ack": "COMMAND_MANIFEST_ACK stale"})

    result = evaluate_dpa_readiness(tmp_path, readiness_path=record)

    assert not result.ok
    assert [finding.code for finding in result.findings] == ["command-manifest-ack-drift"]


def test_dpa_readiness_cli_reports_blocked_without_failure() -> None:
    result = runner.invoke(app, ["dpa", "readiness"])

    assert result.exit_code == 0
    assert "DPA readiness: DP2_BLOCKED" in result.stdout
    assert "implementation: 95%" in result.stdout
    assert "maintainer_authorization" in result.stdout


def test_dpa_readiness_cli_can_require_dp2_ready() -> None:
    result = runner.invoke(app, ["dpa", "readiness", "--require-dp2-ready"])

    assert result.exit_code == 1
    assert "DPA readiness: DP2_BLOCKED" in result.stdout
