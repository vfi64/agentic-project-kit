from __future__ import annotations

from contextlib import contextmanager
import json
import os
from pathlib import Path
import re

import pytest

from agentic_project_kit.transfer_repo_actions import RepoActionResult
import agentic_project_kit.transfer_repo_actions as transfer_repo_actions
from agentic_project_kit.workspace import UNEXPECTED_WORKSPACE_MANIFEST_MESSAGE, load_workspace
from agentic_project_kit.workspace_lock import WorkspaceLockBusy, acquire_workspace_lock


def _rel(path: Path) -> str:
    return path.as_posix()


def test_legacy_workspace_paths_match_todays_literals() -> None:
    ws = load_workspace(Path("."))

    assert _rel(ws.docs_root()) == "docs"
    assert _rel(ws.tmp()) == "tmp"
    assert _rel(ws.agentic_root()) == ".agentic"
    assert _rel(ws.agentic_file("handoff_state.yaml")) == ".agentic/handoff_state.yaml"
    assert _rel(ws.agentic_tmp()) == ".agentic/tmp"
    assert _rel(ws.workspace_lock_path()) == ".agentic/tmp/workspace.lock"
    assert _rel(ws.transfer_inbox()) == ".agentic/transfer/inbox"
    assert _rel(ws.transfer_outbox()) == ".agentic/transfer/outbox"
    assert _rel(ws.handoff_state_path()) == ".agentic/handoff_state.yaml"
    assert _rel(ws.operational_handoff_state_path()) == ".agentic/operational_handoff_state.yaml"
    assert _rel(ws.status_path()) == "docs/STATUS.md"
    assert _rel(ws.test_gates_path()) == "docs/TEST_GATES.md"
    assert _rel(ws.documentation_coverage_path()) == "docs/DOCUMENTATION_COVERAGE.yaml"
    assert _rel(ws.doc_registry_path()) == "docs/DOCUMENTATION_REGISTRY.yaml"
    assert _rel(ws.reports_dir()) == "docs/reports"
    assert _rel(ws.terminal_reports_dir()) == "docs/reports/terminal"
    assert ws.post_pr_successor_chat_handoff_prefix() == "docs/reports/terminal/post-pr"
    assert (
        _rel(ws.post_pr_successor_chat_handoff_path(123))
        == "docs/reports/terminal/post-pr123-successor-chat-handoff.md"
    )
    assert (
        _rel(ws.transfer_handoff_report_file("latest-transfer-handoff-report.json"))
        == "docs/reports/terminal/transfer_handoff_reports/latest-transfer-handoff-report.json"
    )
    assert _rel(ws.handoff_dir()) == "docs/handoff"
    assert _rel(ws.handoff_file("CURRENT_HANDOFF.md")) == "docs/handoff/CURRENT_HANDOFF.md"
    assert _rel(ws.handoff_packages_latest()) == "docs/reports/handoff-packages/latest"
    assert _rel(ws.package_file("validation_report.json")) == "docs/reports/handoff-packages/latest/validation_report.json"
    assert _rel(ws.planning_dir()) == "docs/planning"
    assert _rel(ws.planning_file("project_direction.yaml")) == "docs/planning/project_direction.yaml"
    assert _rel(ws.governance_dir()) == "docs/governance"
    assert _rel(ws.governance_file("FINAL_SUMMARY_CONTRACT.md")) == "docs/governance/FINAL_SUMMARY_CONTRACT.md"
    assert _rel(ws.reference_dir()) == "docs/reference"
    assert _rel(ws.reference_file("AGENTIC_KIT_COMMANDS.md")) == "docs/reference/AGENTIC_KIT_COMMANDS.md"
    assert _rel(ws.source_root()) == "src/agentic_project_kit"
    assert _rel(ws.pyproject_path()) == "pyproject.toml"
    assert ws.admin_refresh_branch_prefix() == "docs/post-pr"
    assert ws.admin_refresh_branch(123) == "docs/post-pr123-handoff-refresh"


def test_load_workspace_fails_loud_on_unexpected_manifest(tmp_path: Path) -> None:
    manifest = tmp_path / ".agentic" / "config.yaml"
    manifest.parent.mkdir(parents=True)
    manifest.write_text("kit_schema_version: 1\n", encoding="utf-8")

    with pytest.raises(RuntimeError, match=re.escape(UNEXPECTED_WORKSPACE_MANIFEST_MESSAGE)):
        load_workspace(tmp_path)


def test_lock_busy_fails_fast_with_holder_info(tmp_path: Path) -> None:
    lock = tmp_path / ".agentic" / "tmp" / "workspace.lock"
    lock.parent.mkdir(parents=True)
    lock.write_text(
        json.dumps({"pid": os.getpid(), "command": "holder-command", "acquired_at": "2026-07-04T00:00:00Z"}),
        encoding="utf-8",
    )

    with pytest.raises(
        WorkspaceLockBusy,
        match=r"workspace is busy: holder-command pid \d+ since 2026-07-04T00:00:00Z",
    ):
        with acquire_workspace_lock(tmp_path, "next-command"):
            raise AssertionError("busy lock should fail before entering")


def test_lock_stale_pid_is_taken_over_with_warning(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog) -> None:
    lock = tmp_path / ".agentic" / "tmp" / "workspace.lock"
    lock.parent.mkdir(parents=True)
    lock.write_text(
        json.dumps({"pid": 999999, "command": "old-command", "acquired_at": "2026-07-04T00:00:00Z"}),
        encoding="utf-8",
    )
    monkeypatch.setattr("agentic_project_kit.workspace_lock._pid_is_alive", lambda pid: False)

    with caplog.at_level("WARNING"):
        with acquire_workspace_lock(tmp_path, "new-command") as acquired:
            assert acquired == lock
            payload = json.loads(lock.read_text(encoding="utf-8"))
            assert payload["pid"] == os.getpid()
            assert payload["command"] == "new-command"

    assert not lock.exists()
    assert "stale workspace lock takeover: old-command pid 999999 since 2026-07-04T00:00:00Z" in caplog.text


def test_lock_released_on_success_and_on_exception(tmp_path: Path) -> None:
    lock = tmp_path / ".agentic" / "tmp" / "workspace.lock"

    with acquire_workspace_lock(tmp_path, "success"):
        assert lock.exists()
    assert not lock.exists()

    with pytest.raises(ValueError, match="boom"):
        with acquire_workspace_lock(tmp_path, "failure"):
            assert lock.exists()
            raise ValueError("boom")
    assert not lock.exists()


def test_commit_paths_and_push_current_acquire_lock(monkeypatch: pytest.MonkeyPatch) -> None:
    events: list[str] = []

    @contextmanager
    def fake_lock(root: Path, command: str):
        events.append(f"enter:{command}:{root.as_posix()}")
        try:
            yield root / ".agentic" / "tmp" / "workspace.lock"
        finally:
            events.append(f"exit:{command}:{root.as_posix()}")

    def fake_commit_unlocked(
        message: str,
        paths: list[str],
        *,
        allow_main: bool = False,
        required_branch: str = "",
    ) -> RepoActionResult:
        assert message == "message"
        assert paths == ["file.txt"]
        assert allow_main is True
        assert required_branch == "feature/demo"
        return RepoActionResult("commit", "PASS", 0, ["git", "commit"], "", "", "next")

    def fake_push_unlocked(*, required_branch: str = "") -> RepoActionResult:
        assert required_branch == "feature/demo"
        return RepoActionResult("push-current", "PASS", 0, ["git", "push"], "", "", "next")

    monkeypatch.setattr(transfer_repo_actions, "acquire_workspace_lock", fake_lock)
    monkeypatch.setattr(transfer_repo_actions, "_commit_paths_unlocked", fake_commit_unlocked)
    monkeypatch.setattr(transfer_repo_actions, "_push_current_unlocked", fake_push_unlocked)

    commit_result = transfer_repo_actions.commit_paths(
        "message",
        ["file.txt"],
        allow_main=True,
        required_branch="feature/demo",
    )
    push_result = transfer_repo_actions.push_current(required_branch="feature/demo")

    assert commit_result.result_status == "PASS"
    assert push_result.result_status == "PASS"
    assert events == [
        "enter:commit_paths:.",
        "exit:commit_paths:.",
        "enter:push_current:.",
        "exit:push_current:.",
    ]
