from __future__ import annotations

import json
from pathlib import Path
import subprocess

from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.dpa_repo_adoption_assessment import (
    DPA_CAPABLE_STATUS,
    READY_STATUS,
    evaluate_dpa_repo_adoption_assessment,
    write_dpa_repo_adoption_assessment_json,
)

runner = CliRunner()


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _git_commit_all(root: Path) -> str:
    subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=root, check=True)
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=root, check=True, capture_output=True, text=True)
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def test_dpa_repo_adoption_assessment_inventories_authority_surfaces(tmp_path: Path) -> None:
    _write(tmp_path / "README.md", "# Demo\n")
    _write(tmp_path / "docs" / "STATUS.md", "# Status\n")
    _write(tmp_path / "docs" / "handoff" / "CURRENT_HANDOFF.md", "# Handoff\n")
    _write(tmp_path / ".agentic" / "config.yaml", "kit_schema_version: 1\n")
    _write(tmp_path / ".agentic" / "state" / "status.md", "# Workspace Status\n")
    _write(tmp_path / ".agentic" / "state" / "handoff" / "README.md", "# Workspace Handoff\n")
    _write(
        tmp_path / ".agentic" / "state" / "handoff" / "packages" / "latest" / "successor_context.yaml",
        "schema_version: 1\n",
    )
    _write(tmp_path / ".github" / "workflows" / "ci.yml", "name: ci\n")
    commit = _git_commit_all(tmp_path)

    result = evaluate_dpa_repo_adoption_assessment(tmp_path)
    payload = result.as_dict()
    surfaces = {surface["path"]: surface for surface in payload["surfaces"]}

    assert result.result_status == READY_STATUS
    assert payload["current_validation_ref"] == commit
    assert payload["foreign_repo_management"]["status"] == DPA_CAPABLE_STATUS
    assert payload["claims"]["external_repo_conformance_claimed"] is False
    assert payload["claims"]["automatic_migration_performed"] is False
    assert surfaces["docs/STATUS.md"]["classification"] == "status_authority"
    assert surfaces[".agentic/state/status.md"]["classification"] == "status_authority"
    assert surfaces["docs/handoff/CURRENT_HANDOFF.md"]["classification"] == "handoff_authority"
    assert surfaces[".agentic/state/handoff/README.md"]["classification"] == "handoff_authority"
    assert (
        surfaces[".agentic/state/handoff/packages/latest/successor_context.yaml"][
            "classification"
        ]
        == "generated_projection"
    )
    assert surfaces[".github/workflows/ci.yml"]["dpa_700_evidence"] == (
        "bounded rollout with rollback or no-migration adjudication"
    )


def test_dpa_repo_adoption_assessment_blocks_missing_exact_ref(tmp_path: Path) -> None:
    _write(tmp_path / "README.md", "# Demo\n")

    result = evaluate_dpa_repo_adoption_assessment(tmp_path)

    assert result.result_status == "BLOCKED_FOR_DPA_REPO_ADOPTION"
    assert result.current_validation_ref == "UNKNOWN"
    assert any(finding.code == "exact-ref-missing" for finding in result.findings)
    assert result.as_dict()["foreign_repo_management"]["fresh_per_repo_inventory_recorded"] is True


def test_dpa_repo_adoption_assessment_blocks_foreign_agentic_dir(tmp_path: Path) -> None:
    _write(tmp_path / ".agentic" / "other-tool.txt", "foreign\n")

    result = evaluate_dpa_repo_adoption_assessment(tmp_path, validation_ref="test-ref")

    assert result.result_status == "BLOCKED_FOR_DPA_REPO_ADOPTION"
    assert any(finding.code == "foreign-agentic-directory" for finding in result.findings)


def test_dpa_repo_adoption_assessment_writes_bounded_evidence(tmp_path: Path) -> None:
    _write(tmp_path / "README.md", "# Demo\n")
    result = evaluate_dpa_repo_adoption_assessment(tmp_path, validation_ref="test-ref")
    output = Path("docs/architecture/evidence/dpa/assessment/repo-adoption/results.json")

    dry_run = write_dpa_repo_adoption_assessment_json(
        result,
        tmp_path,
        output,
        execute=False,
    )
    written = write_dpa_repo_adoption_assessment_json(
        result,
        tmp_path,
        output,
        execute=True,
    )
    blocked = write_dpa_repo_adoption_assessment_json(
        result,
        tmp_path,
        "docs/reports/repo-adoption.json",
        execute=False,
    )

    assert dry_run["result_status"] == "PASS"
    assert dry_run["written"] is False
    assert written["result_status"] == "PASS"
    assert written["written"] is True
    payload = json.loads((tmp_path / output).read_text(encoding="utf-8"))
    assert payload["kind"] == "dpa_repo_adoption_assessment"
    assert blocked["result_status"] == "BLOCK"
    assert blocked["reason"] == "output_outside_dpa_assessment_evidence_root"


def test_dpa_repo_adoption_assessment_cli_reports_ready(tmp_path: Path) -> None:
    _write(tmp_path / "README.md", "# Demo\n")

    result = runner.invoke(
        app,
        [
            "dpa",
            "repo-adoption-assessment",
            "--root",
            str(tmp_path),
            "--validation-ref",
            "test-ref",
            "--require-ready",
        ],
    )

    assert result.exit_code == 0, result.stdout
    assert "DPA_REPO_ADOPTION_ASSESSMENT" in result.stdout
    assert f"STATUS={READY_STATUS}" in result.stdout
    assert "EXTERNAL_REPO_CONFORMANCE_CLAIMED=false" in result.stdout
    assert "AUTOMATIC_MIGRATION_PERFORMED=false" in result.stdout


def test_dpa_repo_adoption_assessment_cli_blocks_missing_ref_when_required(
    tmp_path: Path,
) -> None:
    _write(tmp_path / "README.md", "# Demo\n")

    result = runner.invoke(
        app,
        [
            "dpa",
            "repo-adoption-assessment",
            "--root",
            str(tmp_path),
            "--require-ready",
        ],
    )

    assert result.exit_code == 1
    assert "FINDING=blocker|exact-ref-missing" in result.stdout
