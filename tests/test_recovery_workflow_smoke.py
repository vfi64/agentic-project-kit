from __future__ import annotations

import subprocess
from pathlib import Path

from agentic_project_kit import transfer_repo_actions
from agentic_project_kit import transfer_workflow_next


class FakeTransferState:
    def __init__(self, payload):
        self._payload = payload

    def as_json_data(self):
        return self._payload


def test_smoke_pr_exists_recovery_returns_state_next(monkeypatch):
    class ContinueMonitor:
        decision = transfer_repo_actions.MonitorDecision.CONTINUE
        actual_branch = "feature/example"
        required_branch = "feature/example"
        reason = "test_continue"

    def fake_run(command, cwd=None):
        if command == ["git", "branch", "--show-current"]:
            return subprocess.CompletedProcess(command, 0, "feature/example\n", "")
        if command == ["git", "ls-remote", "--exit-code", "origin", "HEAD"]:
            return subprocess.CompletedProcess(command, 0, "ref\tHEAD\n", "")
        if command[:3] == ["gh", "pr", "create"]:
            return subprocess.CompletedProcess(command, 1, "", "a pull request already exists for feature/example\n")
        if command[:3] == ["gh", "pr", "list"]:
            return subprocess.CompletedProcess(
                command,
                0,
                '[{"number": 42, "state": "OPEN", "url": "https://example.invalid/pr/42", "headRefName": "feature/example", "baseRefName": "main", "title": "Existing"}]\n',
                "",
            )
        return subprocess.CompletedProcess(command, 99, "", f"unexpected command: {command}\n")

    monkeypatch.setattr(transfer_repo_actions, "_run", fake_run)
    monkeypatch.setattr(transfer_repo_actions, "guard_pr_create", lambda **kwargs: ContinueMonitor())

    result = transfer_repo_actions.pr_create(
        base="main",
        head="feature/example",
        title="Example",
        body="Body",
    )
    data = result.as_json_data()

    assert result.returncode == 0
    assert data["result_status"] == "PASS"
    assert "STATE=PR_EXISTS" in data["stdout"]
    assert "NEXT=run_pr_status_or_pr_complete" in data["next_action"]


def test_smoke_already_merged_recovery_returns_state_next(monkeypatch):
    def fake_run(command, cwd=None):
        if command[:4] == ["gh", "pr", "view", "42"]:
            return subprocess.CompletedProcess(
                command,
                0,
                '{"number": 42, "state": "MERGED", "merged": true, "headRefOid": "%s", "url": "https://example.invalid/pr/42", "title": "Merged"}\n' % ("a" * 40),
                "",
            )
        return subprocess.CompletedProcess(command, 99, "", f"unexpected command: {command}\n")

    monkeypatch.setattr(transfer_repo_actions, "_run", fake_run)

    result = transfer_repo_actions._already_merged_pr_result(
        42,
        action="pr-merge-safe",
        command=["agentic-kit", "pr", "merge-if-green", "42"],
    )
    assert result is not None
    data = result.as_json_data()

    assert data["result_status"] == "PASS"
    assert "STATE=ALREADY_MERGED" in data["stdout"]
    assert "NEXT=run_post_merge_check_or_handoff_refresh" in data["next_action"]


def test_smoke_remote_mutation_preflight_unreachable_returns_state_next(monkeypatch):
    def fake_run(command, cwd=None):
        if command == ["git", "ls-remote", "--exit-code", "origin", "HEAD"]:
            return subprocess.CompletedProcess(command, 128, "", "Could not resolve host\n")
        return subprocess.CompletedProcess(command, 99, "", f"unexpected command: {command}\n")

    monkeypatch.setattr(transfer_repo_actions, "_run", fake_run)

    result = transfer_repo_actions._remote_mutation_preflight(
        action="push-current",
        mutation="push-current",
        required_branch="",
    )
    assert result is not None
    data = result.as_json_data()

    assert data["result_status"] == "FAIL"
    assert data["returncode"] == 2
    assert "STATE=REMOTE_UNREACHABLE" in data["next_action"]
    assert "NEXT=retry_remote_check_later" in data["next_action"]


def test_smoke_remote_mutation_preflight_drift_returns_state_next(monkeypatch):
    def fake_run(command, cwd=None):
        if command == ["git", "ls-remote", "--exit-code", "origin", "HEAD"]:
            return subprocess.CompletedProcess(command, 0, "ref\tHEAD\n", "")
        if command == ["git", "branch", "--show-current"]:
            return subprocess.CompletedProcess(command, 0, "feature/other\n", "")
        return subprocess.CompletedProcess(command, 99, "", f"unexpected command: {command}\n")

    monkeypatch.setattr(transfer_repo_actions, "_run", fake_run)

    result = transfer_repo_actions._remote_mutation_preflight(
        action="push-current",
        mutation="push-current",
        required_branch="feature/expected",
    )
    assert result is not None
    data = result.as_json_data()

    assert data["result_status"] == "FAIL"
    assert "STATE=REMOTE_DRIFT" in data["next_action"]
    assert "NEXT=sync_or_regenerate_command" in data["next_action"]


def test_smoke_workflow_next_dirty_returns_state_next_command(monkeypatch, tmp_path):
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
    data = result.as_json_data()

    assert data["state"] == "DIRTY_WORKTREE"
    assert data["returncode"] == 2
    assert data["command"] == ["./.venv/bin/agentic-kit", "transfer", "repo-status", "--full"]
    assert data["next"] == "Inspect or normalize the dirty worktree before continuing."


def test_smoke_workflow_next_transfer_ready_returns_state_next_command(monkeypatch, tmp_path):
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

    assert data["state"] == "TRANSFER_READY"
    assert data["returncode"] == 0
    assert data["command"] == ["./.venv/bin/agentic-kit", "transfer", "remote-next"]
    assert data["next"] == "Run the queued command."
