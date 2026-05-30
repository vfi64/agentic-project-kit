from __future__ import annotations

import json
import subprocess
from pathlib import Path

from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.transfer_closeout import closeout_transfer


def _init_repo(root: Path) -> None:
    subprocess.run(["git", "init"], cwd=root, check=True, stdout=subprocess.PIPE)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=root, check=True)
    subprocess.run(["git", "remote", "add", "origin", "git@github.com:vfi64/agentic-project-kit.git"], cwd=root, check=True)
    subprocess.run(["git", "commit", "--allow-empty", "-m", "init"], cwd=root, check=True, stdout=subprocess.PIPE)


def _write_latest_report(root: Path, report: str = "docs/reports/command_runs/example.md") -> None:
    report_path = root / report
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("example report\n", encoding="utf-8")
    latest = root / "docs/reports/command_runs/LATEST_COMMAND_RUN.txt"
    latest.write_text(report + "\n", encoding="utf-8")


def test_closeout_removes_transfer_dir_and_allows_latest_evidence(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    _write_latest_report(tmp_path)
    transfer_dir = tmp_path / ".agentic/transfer/inbox"
    transfer_dir.mkdir(parents=True)
    (transfer_dir / "current.yaml").write_text("id: example\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    result = closeout_transfer(tmp_path)

    assert result.removed_transfer_dir is True
    assert not (tmp_path / ".agentic/transfer").exists()
    assert result.latest_command_run_path == "docs/reports/command_runs/example.md"
    assert result.latest_report_exists is True
    assert result.blocked_dirty_paths == []
    assert result.result_status == "PASS"


def test_closeout_blocks_unexpected_dirty_path(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    _write_latest_report(tmp_path)
    (tmp_path / "unexpected.txt").write_text("dirty\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    result = closeout_transfer(tmp_path)

    assert result.result_status == "BLOCKED"
    assert result.returncode == 1
    assert "unexpected.txt" in result.blocked_dirty_paths


def test_closeout_cli_emits_json(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    _write_latest_report(tmp_path)
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(app, ["transfer", "closeout"])

    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["schema_version"] == 1
    assert data["result_status"] == "PASS"
    assert data["latest_command_run_path"] == "docs/reports/command_runs/example.md"


def test_transfer_help_lists_closeout():
    result = CliRunner().invoke(app, ["transfer", "--help"])

    assert result.exit_code == 0
    assert "closeout" in result.stdout
