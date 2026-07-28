from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.dpa_renderer_readiness import (
    RENDERER_SOURCE_PATHS,
    RENDERER_TEST_GLOBS,
    evaluate_renderer_probe_readiness,
)

runner = CliRunner()


def _touch(root: Path, path: str) -> None:
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("fixture\n", encoding="utf-8")


def _minimal_renderer_root(root: Path) -> None:
    for path in RENDERER_SOURCE_PATHS:
        _touch(root, path)
    for pattern in RENDERER_TEST_GLOBS:
        _touch(root, pattern)
    _touch(root, "docs/architecture/dpa/probes/DP1_PROBE_MANUALS_20260727.md")
    _touch(root, "docs/architecture/dpa/probes/DP1_PROBE_EXECUTION_PACKAGE_DRAFT_20260727.md")
    readiness = root / "docs/architecture/evidence/dpa/assessment/dp1-assessment-readiness-20260728.json"
    readiness.parent.mkdir(parents=True, exist_ok=True)
    readiness.write_text(
        json.dumps(
            {
                "probe_family_status": {
                    "RENDERER": "PARTIAL_BLOCKED_FOR_DP2",
                },
                "dp2_entry_status": {
                    "renderer_full_evidence": "BLOCKED",
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def test_renderer_readiness_reports_honest_partial_block(tmp_path: Path) -> None:
    _minimal_renderer_root(tmp_path)

    result = evaluate_renderer_probe_readiness(tmp_path, validation_ref="test-ref")

    assert result.structural_ok
    assert result.result_status == "PARTIAL_BLOCKED_FOR_DP2"
    assert not result.full_evidence_satisfied
    payload = result.as_dict()
    assert payload["validation_ref"] == "test-ref"
    assert "renderer-approved-map-and-identity-missing" in result.blockers
    assert "renderer-side-effect-fixtures" in result.blockers
    assert payload["claims"]["approved_dpa_renderer_identity_claimed"] is False
    assert payload["claims"]["renderer_conformance_claimed"] is False


def test_renderer_readiness_blocks_missing_required_surface(tmp_path: Path) -> None:
    _minimal_renderer_root(tmp_path)
    (tmp_path / "src/agentic_project_kit/gui_tkinter_renderer.py").unlink()

    result = evaluate_renderer_probe_readiness(tmp_path)

    assert result.result_status == "STRUCTURAL_BLOCK"
    assert [finding.code for finding in result.findings] == ["required-surface-missing"]


def test_renderer_readiness_cli_reports_partial_without_failure(tmp_path: Path) -> None:
    _minimal_renderer_root(tmp_path)

    result = runner.invoke(app, ["dpa", "renderer-readiness", "--root", str(tmp_path)])

    assert result.exit_code == 0
    assert "DPA_RENDERER_PROBE_READINESS" in result.stdout
    assert "STATUS=PARTIAL_BLOCKED_FOR_DP2" in result.stdout
    assert "BLOCKER=renderer-side-effect-fixtures" in result.stdout


def test_renderer_readiness_cli_can_record_explicit_validation_ref(tmp_path: Path) -> None:
    _minimal_renderer_root(tmp_path)

    result = runner.invoke(
        app,
        [
            "dpa",
            "renderer-readiness",
            "--root",
            str(tmp_path),
            "--validation-ref",
            "target-ref",
        ],
    )

    assert result.exit_code == 0
    assert "VALIDATION_REF=target-ref" in result.stdout


def test_renderer_readiness_cli_can_require_full_evidence(tmp_path: Path) -> None:
    _minimal_renderer_root(tmp_path)

    result = runner.invoke(
        app,
        ["dpa", "renderer-readiness", "--root", str(tmp_path), "--require-full-evidence"],
    )

    assert result.exit_code == 1
    assert "FULL_EVIDENCE_SATISFIED=false" in result.stdout


def test_renderer_readiness_cli_writes_evidence_under_probe_root(tmp_path: Path) -> None:
    _minimal_renderer_root(tmp_path)
    output = "docs/architecture/evidence/dpa/probes/renderer-current/results.json"

    result = runner.invoke(
        app,
        [
            "dpa",
            "renderer-readiness",
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


def test_renderer_readiness_cli_rejects_evidence_outside_probe_root(tmp_path: Path) -> None:
    _minimal_renderer_root(tmp_path)

    result = runner.invoke(
        app,
        [
            "dpa",
            "renderer-readiness",
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
