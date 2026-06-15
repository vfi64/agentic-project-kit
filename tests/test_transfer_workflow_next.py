from __future__ import annotations

from pathlib import Path

from agentic_project_kit import transfer_workflow_next


class FakeTransferState:
    def __init__(self, payload):
        self._payload = payload

    def as_json_data(self):
        return self._payload


def test_workflow_next_blocks_dirty_worktree(monkeypatch, tmp_path):
    def fake_git(root: Path, *args: str) -> str:
        if args == ("branch", "--show-current"):
            return "main"
        if args == ("rev-parse", "HEAD"):
            return "abc"
        if args == ("rev-parse", "origin/main"):
            return "abc"
        if args == ("status", "--porcelain=v1"):
            return " M src/example.py"
        return ""

    monkeypatch.setattr(transfer_workflow_next, "_git_text", fake_git)

    result = transfer_workflow_next.run_workflow_next(tmp_path)

    assert result.returncode == 2
    assert result.state == "DIRTY_WORKTREE"
    assert result.command == ("./.venv/bin/agentic-kit", "transfer", "repo-status", "--full")


def test_workflow_next_continues_feature_branch(monkeypatch, tmp_path):
    def fake_git(root: Path, *args: str) -> str:
        if args == ("branch", "--show-current"):
            return "feature/example"
        if args == ("rev-parse", "HEAD"):
            return "abc"
        if args == ("rev-parse", "origin/main"):
            return "abc"
        if args == ("status", "--porcelain=v1"):
            return ""
        return ""

    monkeypatch.setattr(transfer_workflow_next, "_git_text", fake_git)

    result = transfer_workflow_next.run_workflow_next(tmp_path)

    assert result.returncode == 0
    assert result.state == "ON_FEATURE_BRANCH"
    assert result.command == ("./.venv/bin/agentic-kit", "transfer", "continue", "feature/example")


def test_workflow_next_reports_transfer_ready(monkeypatch, tmp_path):
    def fake_git(root: Path, *args: str) -> str:
        if args == ("branch", "--show-current"):
            return "main"
        if args == ("rev-parse", "HEAD"):
            return "abc"
        if args == ("rev-parse", "origin/main"):
            return "abc"
        if args == ("status", "--porcelain=v1"):
            return ""
        return ""

    monkeypatch.setattr(transfer_workflow_next, "_git_text", fake_git)
    monkeypatch.setattr(
        transfer_workflow_next,
        "build_transfer_state",
        lambda root: FakeTransferState(
            {
                "primary_state": "COMMAND_READY",
                "next_action": "Run the queued command.",
                "capabilities": {"run_next_command": True},
                "reasons": [],
            }
        ),
    )

    result = transfer_workflow_next.run_workflow_next(tmp_path)
    data = result.as_json_data()

    assert result.returncode == 0
    assert result.state == "TRANSFER_READY"
    assert result.command == ("./.venv/bin/agentic-kit", "transfer", "remote-next")
    assert data["state"] == "TRANSFER_READY"
    assert data["next"] == "Run the queued command."


def test_workflow_next_reports_ready_for_planned_work(monkeypatch, tmp_path):
    def fake_git(root: Path, *args: str) -> str:
        if args == ("branch", "--show-current"):
            return "main"
        if args == ("rev-parse", "HEAD"):
            return "abc"
        if args == ("rev-parse", "origin/main"):
            return "abc"
        if args == ("status", "--porcelain=v1"):
            return ""
        return ""

    monkeypatch.setattr(transfer_workflow_next, "_git_text", fake_git)
    monkeypatch.setattr(
        transfer_workflow_next,
        "build_transfer_state",
        lambda root: FakeTransferState(
            {
                "primary_state": "NO_COMMAND",
                "next_action": "No queued transfer command.",
                "capabilities": {"run_next_command": False},
                "reasons": [],
            }
        ),
    )

    result = transfer_workflow_next.run_workflow_next(tmp_path)

    assert result.returncode == 0
    assert result.state == "READY_FOR_PLANNED_WORK"
    assert result.command == ()
