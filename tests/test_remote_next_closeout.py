from __future__ import annotations

import subprocess
from pathlib import Path

from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.remote_next_closeout import run_remote_next_closeout


def git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=root, text=True, capture_output=True, check=False)


def init_repo(root: Path) -> None:
    git(root, "init")
    git(root, "config", "user.email", "test@example.invalid")
    git(root, "config", "user.name", "Test User")
    git(root, "checkout", "-b", "main")
    (root / ".agentic/typed_work_orders/inbox").mkdir(parents=True)
    (root / ".agentic/typed_work_orders/inbox/example.yaml").write_text("id: example\n", encoding="utf-8")
    git(root, "add", ".")
    assert git(root, "commit", "-m", "init").returncode == 0


def test_rnc_commits_expected_closeout_paths_including_deletion(tmp_path: Path) -> None:
    init_repo(tmp_path)
    (tmp_path / ".agentic/handoff_state.yaml").write_text("state: refreshed\n", encoding="utf-8")
    (tmp_path / ".agentic/typed_work_orders/inbox/example.yaml").unlink()
    (tmp_path / ".agentic/typed_work_orders/executed").mkdir(parents=True)
    (tmp_path / ".agentic/typed_work_orders/executed/example.yaml").write_text("id: example\n", encoding="utf-8")
    (tmp_path / "docs/reports/terminal").mkdir(parents=True)
    (tmp_path / "docs/reports/terminal/example.log").write_text("PASS\n", encoding="utf-8")

    result = run_remote_next_closeout(tmp_path, push=False)

    assert result.success, result.findings
    assert result.closeout_branch == "docs/example-evidence"
    assert git(tmp_path, "status", "--short").stdout == ""


def test_rnc_blocks_unexpected_dirty_path(tmp_path: Path) -> None:
    init_repo(tmp_path)
    (tmp_path / "unexpected.txt").write_text("dirty\n", encoding="utf-8")

    result = run_remote_next_closeout(tmp_path, push=False)

    assert not result.success
    assert any("unexpected dirty path" in finding for finding in result.findings)


def test_rn_and_rnc_cli_are_registered(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        "agentic_project_kit.cli_commands.remote_next.run_remote_next",
        lambda root: type("R", (), {"sync_status": "synced", "returncode": 0, "message": "ok", "typed_next": None})(),
    )
    rn = CliRunner().invoke(app, ["rn"])
    assert rn.exit_code == 0, rn.output
    assert "REMOTE_NEXT_RESULT" in rn.output

    init_repo(tmp_path)
    (tmp_path / "docs/reports/terminal").mkdir(parents=True)
    (tmp_path / "docs/reports/terminal/example.log").write_text("PASS\n", encoding="utf-8")
    rnc = CliRunner().invoke(app, ["rnc", "--root", str(tmp_path), "--no-push"])
    assert rnc.exit_code == 0, rnc.output
    assert "REMOTE_NEXT_CLOSEOUT_RESULT" in rnc.output
