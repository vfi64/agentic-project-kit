from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import subprocess


class MonitorDecision(str, Enum):
    CONTINUE = "continue"
    SWITCH = "switch"
    BLOCK = "block"


@dataclass(frozen=True)
class MonitorResult:
    decision: MonitorDecision
    actual_branch: str
    required_branch: str
    reason: str
    command_kind: str
    switched: bool = False


@dataclass(frozen=True)
class GitState:
    branch: str
    dirty_status: str
    head: str


MUTATING_COMMAND_KINDS = {
    "commit",
    "push-current",
    "pr-create",
    "pr-merge-safe",
    "admin-refresh-pr",
    "branch-create",
    "branch-switch",
    "handoff-refresh",
    "evidence-finalize-log",
}

MAIN_MUTATION_ALLOWLIST = {
    "admin-refresh-pr",
    "handoff-refresh",
    "pull-current",
    "repo-status",
    "post-merge-check",
    "branch-switch",
}

IGNORED_RUNTIME_STATUS_PATHS = {
    ".agentic/tmp/workspace.lock",
}


def _run_git(root: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=root, text=True, capture_output=True, check=False)


def read_git_state(root: Path | str = ".") -> GitState:
    root_path = Path(root)
    branch = _run_git(root_path, ["branch", "--show-current"]).stdout.strip()
    status_lines = _run_git(root_path, ["status", "--short", "--untracked-files=all"]).stdout.splitlines()
    dirty_status = "\n".join(
        line for line in status_lines if line[3:] not in IGNORED_RUNTIME_STATUS_PATHS
    ).strip()
    head = _run_git(root_path, ["rev-parse", "HEAD"]).stdout.strip()
    return GitState(branch=branch, dirty_status=dirty_status, head=head)


def branch_exists(root: Path | str, branch: str) -> bool:
    root_path = Path(root)
    local = _run_git(root_path, ["rev-parse", "--verify", "--quiet", branch])
    if local.returncode == 0:
        return True
    remote = _run_git(root_path, ["rev-parse", "--verify", "--quiet", f"origin/{branch}"])
    return remote.returncode == 0


def guard_branch(
    *,
    root: Path | str = ".",
    command_kind: str,
    required_branch: str,
    allow_main_mutation: bool = False,
    auto_switch: bool = True,
) -> MonitorResult:
    root_path = Path(root)
    if not required_branch.strip():
        state = read_git_state(root_path)
        return MonitorResult(
            decision=MonitorDecision.BLOCK,
            actual_branch=state.branch,
            required_branch=required_branch,
            reason="missing_required_branch",
            command_kind=command_kind,
        )

    state = read_git_state(root_path)

    if required_branch == "main" and command_kind in MUTATING_COMMAND_KINDS and not allow_main_mutation:
        if command_kind not in MAIN_MUTATION_ALLOWLIST:
            return MonitorResult(
                decision=MonitorDecision.BLOCK,
                actual_branch=state.branch,
                required_branch=required_branch,
                reason="main_mutation_not_allowed",
                command_kind=command_kind,
            )

    if state.branch == required_branch:
        return MonitorResult(
            decision=MonitorDecision.CONTINUE,
            actual_branch=state.branch,
            required_branch=required_branch,
            reason="already_on_required_branch",
            command_kind=command_kind,
        )

    if state.dirty_status:
        return MonitorResult(
            decision=MonitorDecision.BLOCK,
            actual_branch=state.branch,
            required_branch=required_branch,
            reason="dirty_worktree_blocks_branch_switch",
            command_kind=command_kind,
        )

    if not branch_exists(root_path, required_branch):
        return MonitorResult(
            decision=MonitorDecision.BLOCK,
            actual_branch=state.branch,
            required_branch=required_branch,
            reason="required_branch_missing",
            command_kind=command_kind,
        )

    if not auto_switch:
        return MonitorResult(
            decision=MonitorDecision.SWITCH,
            actual_branch=state.branch,
            required_branch=required_branch,
            reason="branch_switch_required",
            command_kind=command_kind,
        )

    switch = _run_git(root_path, ["switch", required_branch])
    if switch.returncode != 0:
        return MonitorResult(
            decision=MonitorDecision.BLOCK,
            actual_branch=state.branch,
            required_branch=required_branch,
            reason="git_switch_failed",
            command_kind=command_kind,
        )

    new_state = read_git_state(root_path)
    if new_state.branch != required_branch:
        return MonitorResult(
            decision=MonitorDecision.BLOCK,
            actual_branch=new_state.branch,
            required_branch=required_branch,
            reason="post_switch_branch_mismatch",
            command_kind=command_kind,
        )

    return MonitorResult(
        decision=MonitorDecision.SWITCH,
        actual_branch=new_state.branch,
        required_branch=required_branch,
        reason="switched_to_required_branch",
        command_kind=command_kind,
        switched=True,
    )


def guard_pr_create(*, root: Path | str = ".", base_branch: str, head_branch: str) -> MonitorResult:
    if not head_branch.strip():
        state = read_git_state(root)
        return MonitorResult(
            decision=MonitorDecision.BLOCK,
            actual_branch=state.branch,
            required_branch=head_branch,
            reason="pr_create_missing_head_branch",
            command_kind="pr-create",
        )

    if head_branch == base_branch:
        state = read_git_state(root)
        return MonitorResult(
            decision=MonitorDecision.BLOCK,
            actual_branch=state.branch,
            required_branch=head_branch,
            reason="pr_create_head_equals_base",
            command_kind="pr-create",
        )

    result = guard_branch(
        root=root,
        command_kind="pr-create",
        required_branch=head_branch,
        allow_main_mutation=False,
        auto_switch=True,
    )
    if result.decision == MonitorDecision.BLOCK:
        return result

    root_path = Path(root)
    diff = _run_git(root_path, ["rev-list", "--count", f"{base_branch}..{head_branch}"])
    if diff.returncode != 0:
        return MonitorResult(
            decision=MonitorDecision.BLOCK,
            actual_branch=read_git_state(root_path).branch,
            required_branch=head_branch,
            reason="pr_create_diff_check_failed",
            command_kind="pr-create",
        )

    if diff.stdout.strip() == "0":
        return MonitorResult(
            decision=MonitorDecision.BLOCK,
            actual_branch=read_git_state(root_path).branch,
            required_branch=head_branch,
            reason="pr_create_no_commits_between_base_and_head",
            command_kind="pr-create",
        )

    return MonitorResult(
        decision=MonitorDecision.CONTINUE,
        actual_branch=read_git_state(root_path).branch,
        required_branch=head_branch,
        reason="pr_create_preflight_passed",
        command_kind="pr-create",
    )
