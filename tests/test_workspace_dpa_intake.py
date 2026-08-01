from __future__ import annotations

import json
from pathlib import Path
import subprocess

from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.workspace_dpa_intake import (
    DPA_WORKSPACE_INTAKE_KIND,
    READY_STATUS,
    build_workspace_dpa_intake_report,
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


def _snapshot(root: Path) -> tuple[tuple[str, ...], dict[str, bytes]]:
    dirs = tuple(
        sorted(
            path.relative_to(root).as_posix()
            for path in root.rglob("*")
            if path.is_dir() and ".git" not in path.relative_to(root).parts
        )
    )
    files = {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file() and ".git" not in path.relative_to(root).parts
    }
    return dirs, files


def test_workspace_dpa_intake_combines_adopt_assessment_and_decision_groups(
    tmp_path: Path,
) -> None:
    _write(tmp_path / "README.md", "# Demo\n")
    _write(tmp_path / "docs" / "STATUS.md", "# Status\n")
    _write(tmp_path / ".github" / "workflows" / "ci.yml", "name: ci\n")
    commit = _git_commit_all(tmp_path)

    report = build_workspace_dpa_intake_report(tmp_path)
    payload = report.as_json_data()
    groups = {
        group["classification"]: group
        for group in payload["adjudication_plan"]["groups"]
    }

    assert report.result_status == READY_STATUS
    assert payload["kind"] == DPA_WORKSPACE_INTAKE_KIND
    assert payload["validation_ref"] == commit
    assert payload["validation_ref_source"] == "git_head"
    assert payload["workspace_adoption"]["agentic"]["status"] == "ready_for_workspace_init"
    assert payload["dpa_repo_adoption_assessment"]["current_validation_ref"] == commit
    assert payload["claims"]["external_repo_conformance_claimed"] is False
    assert payload["claims"]["automatic_migration_performed"] is False
    assert payload["automation"]["migration_performed"] is False
    assert groups["ci_workflow"]["default_decision"] == "bounded-rollout-with-rollback-required"
    assert groups["onboarding_document"]["default_decision"] == "maintainer-adjudication-required"


def test_workspace_dpa_intake_cli_is_read_only_by_default(tmp_path: Path) -> None:
    _write(tmp_path / "README.md", "# Demo\n")
    _git_commit_all(tmp_path)
    before = _snapshot(tmp_path)

    result = runner.invoke(
        app,
        [
            "workspace",
            "dpa-intake",
            "--root",
            str(tmp_path),
            "--require-ready",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    assert _snapshot(tmp_path) == before
    payload = json.loads(result.output)
    assert payload["result_status"] == READY_STATUS
    assert payload["automation"]["evidence_write_requested"] is False


def test_workspace_dpa_intake_writes_default_bounded_evidence(tmp_path: Path) -> None:
    _write(tmp_path / "README.md", "# Demo\n")

    result = runner.invoke(
        app,
        [
            "workspace",
            "dpa-intake",
            "--root",
            str(tmp_path),
            "--validation-ref",
            "test-ref",
            "--write-evidence",
            "--execute",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    evidence_path = (
        tmp_path
        / "docs"
        / "architecture"
        / "evidence"
        / "dpa"
        / "assessment"
        / "workspace-dpa-intake-test-ref.json"
    )
    assert payload["evidence_write"]["result_status"] == "PASS"
    assert payload["evidence_write"]["written"] is True
    record = json.loads(evidence_path.read_text(encoding="utf-8"))
    assert record["kind"] == DPA_WORKSPACE_INTAKE_KIND
    assert record["automation"]["evidence_write_requested"] is True
    assert record["automation"]["evidence_execute_requested"] is True
    assert record["claims"]["external_repo_conformance_claimed"] is False


def test_workspace_dpa_intake_blocks_output_outside_evidence_root(tmp_path: Path) -> None:
    _write(tmp_path / "README.md", "# Demo\n")

    result = runner.invoke(
        app,
        [
            "workspace",
            "dpa-intake",
            "--root",
            str(tmp_path),
            "--validation-ref",
            "test-ref",
            "--output",
            "docs/reports/intake.json",
            "--json",
        ],
    )

    assert result.exit_code == 2
    payload = json.loads(result.output)
    assert payload["result_status"] == "BLOCKED_FOR_DPA_INTAKE"
    assert payload["evidence_write"]["reason"] == "output_outside_dpa_assessment_evidence_root"
    assert not (tmp_path / "docs" / "reports" / "intake.json").exists()


def test_workspace_dpa_intake_require_ready_blocks_missing_exact_ref(tmp_path: Path) -> None:
    _write(tmp_path / "README.md", "# Demo\n")

    result = runner.invoke(
        app,
        [
            "workspace",
            "dpa-intake",
            "--root",
            str(tmp_path),
            "--require-ready",
        ],
    )

    assert result.exit_code == 1
    assert "WORKSPACE_DPA_INTAKE" in result.output
    assert "VALIDATION_REF=UNKNOWN" in result.output
    assert "FINDING=blocker|exact-ref-missing" in result.output
