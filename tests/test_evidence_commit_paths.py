from __future__ import annotations

import subprocess
from pathlib import Path

from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.evidence_commit_paths import commit_paths


def git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=root, text=True, capture_output=True, check=False)


def init_repo(root: Path) -> None:
    git(root, "init")
    git(root, "config", "user.email", "test@example.invalid")
    git(root, "config", "user.name", "Test User")
    (root / "README.md").write_text("demo\n", encoding="utf-8")
    git(root, "add", "README.md")
    result = git(root, "commit", "-m", "init")
    assert result.returncode == 0, result.stderr


def test_commit_paths_commits_expected_paths_and_requires_clean_afterwards(tmp_path: Path) -> None:
    init_repo(tmp_path)
    rel = "docs/reports/terminal/demo.log"
    path = tmp_path / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("complete log\n### RESULT: PASS ###\n", encoding="utf-8")

    result = commit_paths(root=tmp_path, paths=(rel,), message="Record demo evidence")

    assert result.success
    assert result.commit_sha
    assert git(tmp_path, "status", "--short").stdout == ""


def test_commit_paths_accepts_expected_tracked_deletion(tmp_path: Path) -> None:
    init_repo(tmp_path)
    rel = "docs/reports/terminal/delete-me.log"
    path = tmp_path / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("old log\n", encoding="utf-8")
    git(tmp_path, "add", rel)
    assert git(tmp_path, "commit", "-m", "add log").returncode == 0
    path.unlink()

    result = commit_paths(root=tmp_path, paths=(rel,), message="Record deletion")

    assert result.success, result.findings
    assert git(tmp_path, "status", "--short").stdout == ""


def test_commit_paths_blocks_unexpected_dirty_paths(tmp_path: Path) -> None:
    init_repo(tmp_path)
    expected = "docs/reports/terminal/demo.log"
    other = "unexpected.txt"
    (tmp_path / expected).parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / expected).write_text("log\n", encoding="utf-8")
    (tmp_path / other).write_text("dirty\n", encoding="utf-8")

    result = commit_paths(root=tmp_path, paths=(expected,), message="Record demo evidence")

    assert not result.success
    assert any("unexpected dirty paths" in finding for finding in result.findings)


def test_commit_paths_rejects_venv_and_git_paths(tmp_path: Path) -> None:
    init_repo(tmp_path)

    for rel in (".git/config", ".venv/bin/python"):
        try:
            commit_paths(root=tmp_path, paths=(rel,), message="bad")
        except ValueError as exc:
            assert rel.split("/")[0] in str(exc)
        else:
            raise AssertionError("expected ValueError")


def test_evidence_commit_paths_cli(tmp_path: Path) -> None:
    init_repo(tmp_path)
    rel = "docs/reports/terminal/demo.log"
    path = tmp_path / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("complete log\n### RESULT: PASS ###\n", encoding="utf-8")

    result = CliRunner().invoke(
        app,
        [
            "evidence",
            "commit-paths",
            "--root",
            str(tmp_path),
            "--path",
            rel,
            "--message",
            "Record demo evidence",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "EVIDENCE_COMMIT_PATHS" in result.output
    assert "success=yes" in result.output
    assert git(tmp_path, "status", "--short").stdout == ""
