from __future__ import annotations

import json
import subprocess
from pathlib import Path

from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.transfer_state import PRIMARY_BLOCKED, PRIMARY_WAIT, build_transfer_state


def _init_repo(root: Path) -> None:
    subprocess.run(["git", "init"], cwd=root, check=True, stdout=subprocess.PIPE)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=root, check=True)
    subprocess.run(["git", "remote", "add", "origin", "git@github.com:vfi64/agentic-project-kit.git"], cwd=root, check=True)


def test_transfer_state_waits_without_pending_order(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    snapshot = build_transfer_state(tmp_path)

    assert snapshot.schema_version == 1
    assert snapshot.repo == "vfi64/agentic-project-kit"
    assert snapshot.primary_state == PRIMARY_WAIT
    assert snapshot.capabilities["diagnose"] is True
    assert snapshot.capabilities["run_next_command"] is False


def test_transfer_state_blocks_dirty_worktree(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    (tmp_path / "dirty.txt").write_text("dirty\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    snapshot = build_transfer_state(tmp_path)

    assert snapshot.primary_state == PRIMARY_BLOCKED
    assert "dirty_worktree" in snapshot.reasons
    assert snapshot.capabilities["run_next_command"] is False


def test_transfer_state_ready_with_pending_order(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    inbox = tmp_path / ".agentic/transfer/inbox/current.yaml"
    inbox.parent.mkdir(parents=True)
    inbox.write_text("id: example\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-m", "Add pending transfer order"], cwd=tmp_path, check=True, stdout=subprocess.PIPE)
    monkeypatch.chdir(tmp_path)

    snapshot = build_transfer_state(tmp_path)

    assert snapshot.primary_state == "READY"
    assert snapshot.capabilities["run_next_command"] is True


def test_transfer_state_cli_emits_json(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(app, ["transfer", "state"])

    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["schema_version"] == 1
    assert data["primary_state"] == "WAIT"
    assert "capabilities" in data
