from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.dpa_probe_004_readiness import (
    PROBE_004_SOURCE_PATHS,
    PROBE_004_TEST_GLOBS,
    evaluate_probe_004_migration_readiness,
)

runner = CliRunner()


def _touch(root: Path, path: str) -> None:
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("fixture\n", encoding="utf-8")


def _minimal_probe_004_root(root: Path) -> None:
    for path in PROBE_004_SOURCE_PATHS:
        _touch(root, path)
    for pattern in PROBE_004_TEST_GLOBS:
        _touch(root, pattern)
    _touch(root, "docs/architecture/dpa/probes/DP1_PROBE_MANUALS_20260727.md")
    _touch(root, "docs/architecture/dpa/probes/DP1_PROBE_EXECUTION_PACKAGE_DRAFT_20260727.md")
    readiness = root / "docs/architecture/evidence/dpa/assessment/dp1-assessment-readiness-20260728.json"
    readiness.parent.mkdir(parents=True, exist_ok=True)
    readiness.write_text(
        json.dumps(
            {
                "probe_family_status": {
                    "PROBE-004": "PARTIAL_BLOCKED_FOR_DP2",
                },
                "dp2_entry_status": {
                    "probe_004_full_evidence": "BLOCKED",
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def test_probe_004_readiness_reports_honest_partial_block(tmp_path: Path) -> None:
    _minimal_probe_004_root(tmp_path)

    result = evaluate_probe_004_migration_readiness(tmp_path, validation_ref="test-ref")

    assert result.structural_ok
    assert result.result_status == "PARTIAL_BLOCKED_FOR_DP2"
    assert not result.full_evidence_satisfied
    payload = result.as_dict()
    assert payload["validation_ref"] == "test-ref"
    assert "probe-004-migration-form-fixtures" in result.blockers
    assert "probe-004-rollback-package-fixtures" in result.blockers
    assert payload["claims"]["migration_probe_execution_claimed"] is False
    assert payload["claims"]["generated_outputs_manually_patched"] is False


def test_probe_004_readiness_blocks_missing_required_surface(tmp_path: Path) -> None:
    _minimal_probe_004_root(tmp_path)
    (tmp_path / "docs/reports/handoff-packages/latest/source_manifest.json").unlink()

    result = evaluate_probe_004_migration_readiness(tmp_path)

    assert result.result_status == "STRUCTURAL_BLOCK"
    assert [finding.code for finding in result.findings] == ["required-surface-missing"]


def test_probe_004_readiness_cli_reports_partial_without_failure(tmp_path: Path) -> None:
    _minimal_probe_004_root(tmp_path)

    result = runner.invoke(app, ["dpa", "probe-004-readiness", "--root", str(tmp_path)])

    assert result.exit_code == 0
    assert "DPA_PROBE_004_MIGRATION_READINESS" in result.stdout
    assert "STATUS=PARTIAL_BLOCKED_FOR_DP2" in result.stdout
    assert "BLOCKER=probe-004-rollback-package-fixtures" in result.stdout


def test_probe_004_readiness_cli_can_record_explicit_validation_ref(tmp_path: Path) -> None:
    _minimal_probe_004_root(tmp_path)

    result = runner.invoke(
        app,
        [
            "dpa",
            "probe-004-readiness",
            "--root",
            str(tmp_path),
            "--validation-ref",
            "target-ref",
        ],
    )

    assert result.exit_code == 0
    assert "VALIDATION_REF=target-ref" in result.stdout


def test_probe_004_readiness_cli_can_require_full_evidence(tmp_path: Path) -> None:
    _minimal_probe_004_root(tmp_path)

    result = runner.invoke(
        app,
        ["dpa", "probe-004-readiness", "--root", str(tmp_path), "--require-full-evidence"],
    )

    assert result.exit_code == 1
    assert "FULL_EVIDENCE_SATISFIED=false" in result.stdout


def test_probe_004_readiness_cli_writes_evidence_under_probe_root(tmp_path: Path) -> None:
    _minimal_probe_004_root(tmp_path)
    output = "docs/architecture/evidence/dpa/probes/probe-004-current/results.json"

    result = runner.invoke(
        app,
        [
            "dpa",
            "probe-004-readiness",
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
    assert payload["result_status"] == "PARTIAL_BLOCKED_FOR_DP2"


def test_probe_004_readiness_cli_rejects_evidence_outside_probe_root(tmp_path: Path) -> None:
    _minimal_probe_004_root(tmp_path)

    result = runner.invoke(
        app,
        [
            "dpa",
            "probe-004-readiness",
            "--root",
            str(tmp_path),
            "--output",
            "tmp/results.json",
            "--execute",
        ],
    )

    assert result.exit_code == 2
    assert not (tmp_path / "tmp/results.json").exists()
    assert "output_outside_dpa_probe_evidence_root" in result.stdout
