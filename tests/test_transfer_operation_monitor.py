from __future__ import annotations

import subprocess
from pathlib import Path

from agentic_project_kit.transfer_operation_monitor import MonitorDecision
from agentic_project_kit.transfer_operation_monitor import guard_branch
from agentic_project_kit.transfer_operation_monitor import guard_pr_create
from agentic_project_kit.transfer_operation_monitor import read_git_state


def git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=repo, text=True, capture_output=True, check=False)


def init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-b", "main")
    git(repo, "config", "user.email", "test@example.invalid")
    git(repo, "config", "user.name", "Test User")
    (repo / "README.md").write_text("initial\n", encoding="utf-8")
    git(repo, "add", "README.md")
    git(repo, "commit", "-m", "initial")
    return repo


def test_guard_continues_when_already_on_required_branch(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)

    result = guard_branch(root=repo, command_kind="commit", required_branch="main", allow_main_mutation=True)

    assert result.decision == MonitorDecision.CONTINUE
    assert result.reason == "already_on_required_branch"


def test_guard_switches_to_existing_clean_required_branch(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    git(repo, "switch", "-c", "feature/demo")
    git(repo, "switch", "main")

    result = guard_branch(root=repo, command_kind="commit", required_branch="feature/demo")

    assert result.decision == MonitorDecision.SWITCH
    assert result.switched is True
    assert read_git_state(repo).branch == "feature/demo"


def test_guard_blocks_branch_switch_when_worktree_dirty(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    git(repo, "switch", "-c", "feature/demo")
    git(repo, "switch", "main")
    (repo / "README.md").write_text("dirty\n", encoding="utf-8")

    result = guard_branch(root=repo, command_kind="commit", required_branch="feature/demo")

    assert result.decision == MonitorDecision.BLOCK
    assert result.reason == "dirty_worktree_blocks_branch_switch"
    assert read_git_state(repo).branch == "main"


def test_git_state_ignores_workspace_runtime_lock_file(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    lock = repo / ".agentic" / "tmp" / "workspace.lock"
    lock.parent.mkdir(parents=True)
    lock.write_text('{"pid": 1}\n', encoding="utf-8")

    state = read_git_state(repo)

    assert state.dirty_status == ""


def test_guard_blocks_feature_mutation_on_main_without_explicit_allowance(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)

    result = guard_branch(root=repo, command_kind="commit", required_branch="main")

    assert result.decision == MonitorDecision.BLOCK
    assert result.reason == "main_mutation_not_allowed"


def test_pr_create_blocks_missing_head(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)

    result = guard_pr_create(root=repo, base_branch="main", head_branch="")

    assert result.decision == MonitorDecision.BLOCK
    assert result.reason == "pr_create_missing_head_branch"


def test_pr_create_blocks_head_equal_base(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)

    result = guard_pr_create(root=repo, base_branch="main", head_branch="main")

    assert result.decision == MonitorDecision.BLOCK
    assert result.reason == "pr_create_head_equals_base"


def test_pr_create_blocks_no_commits_between_base_and_head(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    git(repo, "switch", "-c", "feature/empty")

    result = guard_pr_create(root=repo, base_branch="main", head_branch="feature/empty")

    assert result.decision == MonitorDecision.BLOCK
    assert result.reason == "pr_create_no_commits_between_base_and_head"


def test_pr_create_passes_when_head_has_commit(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    git(repo, "switch", "-c", "feature/change")
    (repo / "file.txt").write_text("change\n", encoding="utf-8")
    git(repo, "add", "file.txt")
    git(repo, "commit", "-m", "change")
    git(repo, "switch", "main")

    result = guard_pr_create(root=repo, base_branch="main", head_branch="feature/change")

    assert result.decision == MonitorDecision.CONTINUE
    assert result.reason == "pr_create_preflight_passed"
    assert read_git_state(repo).branch == "feature/change"
