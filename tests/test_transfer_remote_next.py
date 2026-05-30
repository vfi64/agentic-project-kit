from __future__ import annotations

import subprocess
from pathlib import Path

from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.transfer_remote_next import _validate_branch_name


def _init_repo(root: Path) -> None:
    subprocess.run(["git", "init"], cwd=root, check=True, stdout=subprocess.PIPE)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=root, check=True)
    subprocess.run(["git", "commit", "--allow-empty", "-m", "init"], cwd=root, check=True, stdout=subprocess.PIPE)


def test_validate_branch_name_accepts_transfer_branch():
    assert _validate_branch_name("transfer/example-1") == "transfer/example-1"


def test_validate_branch_name_rejects_unsafe_branch():
    for value in ["", "-bad", "bad..name", "bad name", "bad.lock"]:
        try:
            _validate_branch_name(value)
        except ValueError:
            continue
        raise AssertionError(f"unsafe branch accepted: {value!r}")


def test_remote_next_blocks_dirty_worktree_before_fetch(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    (tmp_path / "dirty.txt").write_text("dirty\n", encoding="utf-8")

    result = CliRunner().invoke(app, ["transfer", "remote-next", "transfer/example"])

    assert result.exit_code == 1
    assert "worktree must be clean before transfer remote-next" in result.stdout


def test_transfer_help_lists_remote_next():
    result = CliRunner().invoke(app, ["transfer", "--help"])

    assert result.exit_code == 0
    assert "remote-next" in result.stdout
