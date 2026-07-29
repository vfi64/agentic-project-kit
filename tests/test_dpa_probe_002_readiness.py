from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.dpa_probe_002_readiness import (
    PROBE_002_SOURCE_PATHS,
    PROBE_002_TEST_GLOBS,
    evaluate_probe_002_lifecycle_readiness,
)

runner = CliRunner()


def _touch(root: Path, path: str) -> None:
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("fixture\n", encoding="utf-8")


def _minimal_probe_002_root(root: Path, *, satisfied: bool = False) -> None:
    for path in PROBE_002_SOURCE_PATHS:
        _touch(root, path)
    for pattern in PROBE_002_TEST_GLOBS:
        _touch(root, pattern.replace("*", "fixture"))
    _touch(root, "docs/architecture/dpa/probes/DP1_SELECTED_WRITER_FIXTURE_PLAN_20260727.md")
    _touch(root, "docs/architecture/dpa/probes/DP1_PROBE_MANUALS_20260727.md")
    _touch(root, "docs/architecture/dpa/probes/DP1_PROBE_EXECUTION_PACKAGE_DRAFT_20260727.md")
    readiness = root / "docs/architecture/evidence/dpa/assessment/dp1-assessment-readiness-20260728.json"
    readiness.parent.mkdir(parents=True, exist_ok=True)
    selected_writer_status = (
        {
            "WRT-CH-001": "FIXTURE_EVIDENCE_RECORDED_FOR_FIRST_DP2_TARGET",
            "WRT-CH-002": "AUTHORIZED_FOR_DP2_TARGET",
            "WRT-CH-003": "AUTHORIZED_FOR_DP2_TARGET",
            "WRT-CH-004": "AUTHORIZED_FOR_DP2_TARGET",
            "WRT-CH-005": "EXTERNAL_HABITABILITY_ONLY",
            "WRT-CH-006": "GENERATED_OUTPUT_CONTRACT_ONLY",
        }
        if satisfied
        else {
            "WRT-CH-001": "SELECTED_FOR_FIXTURE",
            "WRT-CH-002": "NEEDS_MAINTAINER_DECISION",
            "WRT-CH-003": "NEEDS_MAINTAINER_DECISION",
            "WRT-CH-004": "NEEDS_MAINTAINER_DECISION",
            "WRT-CH-005": "EXTERNAL_HABITABILITY_ONLY",
            "WRT-CH-006": "GENERATED_OUTPUT_CONTRACT_ONLY",
        }
    )
    probe_status = "SATISFIED_FOR_CURRENT_KIT_REF" if satisfied else "PARTIAL_BLOCKED_FOR_DP2"
    readiness.write_text(
        json.dumps(
            {
                "probe_family_status": {"PROBE-002": probe_status},
                "dp2_entry_status": {"probe_002_full_evidence": probe_status},
                "selected_writer_status": selected_writer_status,
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def test_probe_002_readiness_reports_honest_partial_block(tmp_path: Path) -> None:
    _minimal_probe_002_root(tmp_path)

    result = evaluate_probe_002_lifecycle_readiness(tmp_path, validation_ref="test-ref")

    assert result.structural_ok
    assert result.result_status == "PARTIAL_BLOCKED_FOR_DP2"
    assert not result.full_evidence_satisfied
    payload = result.as_dict()
    assert payload["validation_ref"] == "test-ref"
    assert "selected-writer-current-fixtures" in result.blockers
    assert "selected-writer-maintainer-decisions" in result.blockers
    assert payload["claims"]["production_mutation_performed"] is False


def test_probe_002_readiness_reports_satisfied_from_readiness_record(tmp_path: Path) -> None:
    _minimal_probe_002_root(tmp_path, satisfied=True)

    result = evaluate_probe_002_lifecycle_readiness(tmp_path, validation_ref="test-ref")

    assert result.structural_ok
    assert result.result_status == "SATISFIED_FOR_CURRENT_KIT_REF"
    assert result.full_evidence_satisfied
    assert result.blockers == ()
    assert {item["fixture_status"] for item in result.as_dict()["selected_writers"]} == {
        "SATISFIED_FOR_CURRENT_DP2_SCOPE",
        "OUT_OF_SCOPE_FOR_FIRST_SELF_HOSTING_TARGET",
        "DEFERRED_TO_PROBE_004_GENERATED_OUTPUT_CONTRACT",
    }


def test_probe_002_readiness_blocks_missing_required_surface(tmp_path: Path) -> None:
    _minimal_probe_002_root(tmp_path)
    (tmp_path / "src/agentic_project_kit/doc_lifecycle.py").unlink()

    result = evaluate_probe_002_lifecycle_readiness(tmp_path)

    assert result.result_status == "STRUCTURAL_BLOCK"
    assert [finding.code for finding in result.findings] == ["required-surface-missing"]


def test_probe_002_readiness_cli_reports_partial_without_failure(tmp_path: Path) -> None:
    _minimal_probe_002_root(tmp_path)

    result = runner.invoke(app, ["dpa", "probe-002-readiness", "--root", str(tmp_path)])

    assert result.exit_code == 0
    assert "DPA_PROBE_002_READINESS" in result.stdout
    assert "STATUS=PARTIAL_BLOCKED_FOR_DP2" in result.stdout
    assert "BLOCKER=selected-writer-maintainer-decisions" in result.stdout


def test_probe_002_readiness_cli_can_require_full_evidence(tmp_path: Path) -> None:
    _minimal_probe_002_root(tmp_path)

    result = runner.invoke(
        app,
        ["dpa", "probe-002-readiness", "--root", str(tmp_path), "--require-full-evidence"],
    )

    assert result.exit_code == 1
    assert "FULL_EVIDENCE_SATISFIED=false" in result.stdout


def test_probe_002_readiness_cli_writes_evidence_under_probe_root(tmp_path: Path) -> None:
    _minimal_probe_002_root(tmp_path)
    output = "docs/architecture/evidence/dpa/probes/probe-002-current/results.json"

    result = runner.invoke(
        app,
        [
            "dpa",
            "probe-002-readiness",
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


def test_probe_002_readiness_cli_rejects_evidence_outside_probe_root(tmp_path: Path) -> None:
    _minimal_probe_002_root(tmp_path)

    result = runner.invoke(
        app,
        [
            "dpa",
            "probe-002-readiness",
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
