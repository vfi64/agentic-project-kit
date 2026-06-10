from __future__ import annotations

import json
import sys
import subprocess
from dataclasses import dataclass, asdict
from pathlib import Path

from agentic_project_kit.transfer_operation_monitor import MonitorDecision
from agentic_project_kit.transfer_operation_monitor import guard_branch
from agentic_project_kit.transfer_operation_monitor import guard_pr_create


@dataclass(frozen=True)
class RepoActionResult:
    action: str
    result_status: str
    returncode: int
    command: list[str]
    stdout: str
    stderr: str
    next_action: str

    def as_json_data(self) -> dict:
        return asdict(self)


def _agentic_kit_command() -> str:
    candidate = Path(sys.executable).parent / "agentic-kit"
    if candidate.exists():
        return str(candidate)
    return "agentic-kit"



def _full_sha_guard(action: str, expected_head_sha: str) -> RepoActionResult | None:
    if len(expected_head_sha) != 40:
        completed = subprocess.CompletedProcess(
            [action, "--expected-head-sha"],
            2,
            "",
            "Expected full 40-character head SHA. Short SHAs are refused for guarded PR actions.\n",
        )
        return _result(action, [action, "--expected-head-sha"], completed, "Re-run with the full PR head SHA.")
    return None



def _resolve_pr_head_sha(pr_number: int, *, action: str) -> tuple[str, RepoActionResult | None]:
    command = ["gh", "pr", "view", str(pr_number), "--json", "headRefOid", "--jq", ".headRefOid"]
    completed = _run(command)
    if completed.returncode != 0:
        return "", _result(action, command, completed, "Inspect PR head SHA lookup failure before continuing.")

    head_sha = completed.stdout.strip()
    if len(head_sha) != 40:
        bad = subprocess.CompletedProcess(
            command,
            2,
            completed.stdout,
            f"Resolved PR head SHA is not a full 40-character SHA: {head_sha}\n",
        )
        return "", _result(action, command, bad, "Inspect PR head SHA lookup failure before continuing.")

    return head_sha, None


def _existing_admin_refresh_pr(refresh_branch: str, *, action: str = "admin-refresh-pr") -> RepoActionResult | None:
    command = [
        "gh",
        "pr",
        "list",
        "--head",
        refresh_branch,
        "--state",
        "open",
        "--json",
        "number,url,headRefName,headRefOid,state,title",
    ]
    completed = _run(command)
    if completed.returncode != 0:
        return _result(action, command, completed, "Inspect existing admin refresh PR lookup failure.")

    try:
        prs = json.loads(completed.stdout or "[]")
    except json.JSONDecodeError as exc:
        bad = subprocess.CompletedProcess(
            command,
            2,
            completed.stdout,
            f"Could not parse existing admin refresh PR lookup JSON: {exc}\n",
        )
        return _result(action, command, bad, "Inspect existing admin refresh PR lookup output.")

    if not isinstance(prs, list):
        bad = subprocess.CompletedProcess(
            command,
            2,
            completed.stdout,
            "Existing admin refresh PR lookup did not return a JSON list.\n",
        )
        return _result(action, command, bad, "Inspect existing admin refresh PR lookup output.")

    if len(prs) > 1:
        bad = subprocess.CompletedProcess(
            command,
            2,
            completed.stdout,
            f"Multiple open admin refresh PRs found for branch {refresh_branch}.\n",
        )
        return _result(action, command, bad, "Resolve duplicate admin refresh PRs before continuing.")

    if not prs:
        return None

    pr = prs[0]
    number = pr.get("number", "")
    url = pr.get("url", "")
    head_ref_oid = pr.get("headRefOid", "")
    out = (
        "ADMIN_REFRESH_EXISTING_BRANCH_RECOVERY\n"
        f"refresh_branch={refresh_branch}\n"
        f"existing_pr={number}\n"
        f"head_ref_oid={head_ref_oid}\n"
        f"url={url}\n"
        "result=PASS\n"
    )
    ok = subprocess.CompletedProcess(command, 0, out, "")
    return _result(action, command, ok, "Run transfer pr-status on the existing admin refresh PR.")

def _run(command: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _result(action: str, command: list[str], completed: subprocess.CompletedProcess[str], next_action: str) -> RepoActionResult:
    status = "PASS" if completed.returncode == 0 else "FAIL"
    return RepoActionResult(
        action=action,
        result_status=status,
        returncode=completed.returncode,
        command=command,
        stdout=completed.stdout,
        stderr=completed.stderr,
        next_action=next_action,
    )


def final_signal(result: RepoActionResult) -> str:
    return "d" if result.result_status == "PASS" and result.returncode == 0 else "f"


def result_terminal(result: RepoActionResult) -> str:
    signal = final_signal(result)
    return "\n".join(
        (
            result_json(result),
            f"FINAL_SIGNAL={signal}",
            f"FINAL_NEXT={result.next_action}",
            f"CHAT_REPLY={signal} | NEXT={result.next_action}",
        )
    )


def _monitor_block_result(
    *,
    action: str,
    command_kind: str,
    required_branch: str,
    monitor,
    next_action: str,
) -> RepoActionResult:
    completed = subprocess.CompletedProcess(
        ["transfer-monitor", command_kind, "--branch", required_branch],
        2,
        "",
        (
            f"Transfer operation monitor blocked {command_kind}: "
            f"{monitor.reason}; actual_branch={monitor.actual_branch}; "
            f"required_branch={monitor.required_branch}\n"
        ),
    )
    return _result(action, list(completed.args), completed, next_action)



def _recover_known_volatile_branch_switch_block(
    *,
    command_kind: str,
    required_branch: str,
    monitor,
    allow_main_mutation: bool,
    auto_switch: bool = True,
):
    if monitor.reason != "dirty_worktree_blocks_branch_switch":
        return monitor

    repair_command = [
        _agentic_kit_command(),
        "transfer",
        "normalize-session",
        "--repair-known-volatile",
    ]
    repair = _run(repair_command)
    if repair.returncode != 0:
        return monitor

    return guard_branch(
        command_kind=command_kind,
        required_branch=required_branch,
        allow_main_mutation=allow_main_mutation,
        auto_switch=auto_switch,
    )


def _verify_current_branch(action: str, expected_branch: str, *, command: list[str]) -> RepoActionResult | None:
    branch_command = ["git", "branch", "--show-current"]
    branch_completed = _run(branch_command)
    if branch_completed.returncode != 0:
        return _result(action, branch_command, branch_completed, "Inspect repository branch state.")

    actual_branch = branch_completed.stdout.strip()
    if actual_branch != expected_branch:
        completed = subprocess.CompletedProcess(
            command,
            2,
            branch_completed.stdout,
            (
                f"Refusing to continue {action} because the current branch drifted: "
                f"expected {expected_branch}, got {actual_branch}\n"
            ),
        )
        return _result(action, command, completed, "Inspect branch drift before continuing.")
    return None


def branch_create(branch: str, *, start_point: str = "main", push: bool = False) -> RepoActionResult:
    monitor = guard_branch(
        command_kind="branch-create",
        required_branch=start_point,
        allow_main_mutation=True,
        auto_switch=True,
    )
    if monitor.decision == MonitorDecision.BLOCK:
        return _monitor_block_result(
            action="branch-create",
            command_kind="branch-create",
            required_branch=start_point,
            monitor=monitor,
            next_action="Inspect transfer operation monitor block before creating branch.",
        )

    command = ["git", "switch", "-c", branch, start_point]
    completed = _run(command)
    if completed.returncode != 0:
        return _result("branch-create", command, completed, "Inspect branch state before continuing.")

    drift = _verify_current_branch("branch-create", branch, command=command)
    if drift is not None:
        return drift

    if push:
        push_command = ["git", "push", "-u", "origin", branch]
        pushed = _run(push_command)
        if pushed.returncode != 0:
            return _result("branch-create", push_command, pushed, "Inspect branch push failure before continuing.")
        drift = _verify_current_branch("branch-create", branch, command=push_command)
        if drift is not None:
            return drift
        return _result("branch-create", push_command, pushed, "Run transfer state or continue with queued work.")

    return _result("branch-create", command, completed, "Run transfer state or continue with queued work.")


def branch_switch(branch: str, *, pull: bool = False) -> RepoActionResult:
    monitor = guard_branch(
        command_kind="branch-switch",
        required_branch=branch,
        allow_main_mutation=True,
        auto_switch=True,
    )
    if monitor.decision == MonitorDecision.BLOCK:
        return _monitor_block_result(
            action="branch-switch",
            command_kind="branch-switch",
            required_branch=branch,
            monitor=monitor,
            next_action="Inspect transfer operation monitor block before switching branch.",
        )

    command = ["git", "switch", branch]
    completed = _run(command)
    if completed.returncode != 0:
        return _result("branch-switch", command, completed, "Inspect branch state before continuing.")

    drift = _verify_current_branch("branch-switch", branch, command=command)
    if drift is not None:
        return drift

    if pull:
        pull_command = ["git", "pull", "--ff-only", "origin", branch]
        pulled = _run(pull_command)
        if pulled.returncode != 0:
            return _result("branch-switch", pull_command, pulled, "Inspect pull failure before continuing.")
        drift = _verify_current_branch("branch-switch", branch, command=pull_command)
        if drift is not None:
            return drift
        return _result("branch-switch", pull_command, pulled, "Run transfer state or continue with queued work.")

    return _result("branch-switch", command, completed, "Run transfer state or continue with queued work.")


def _current_branch_result(action: str = "commit") -> tuple[str, RepoActionResult | None]:
    branch_command = ["git", "branch", "--show-current"]
    branch_completed = _run(branch_command)
    if branch_completed.returncode != 0:
        return "", _result(
            action,
            branch_command,
            branch_completed,
            "Inspect repository branch state before committing.",
        )
    return branch_completed.stdout.strip(), None


def _main_commit_refusal(message: str) -> RepoActionResult:
    completed = subprocess.CompletedProcess(
        ["git", "commit", "-m", message],
        2,
        "",
        "Refusing to commit directly on main. Use a branch or pass --allow-main explicitly.\n",
    )
    return _result("commit", completed.args, completed, "Create a feature/admin branch before committing.")


def commit_paths(message: str, paths: list[str], *, allow_main: bool = False, required_branch: str = "") -> RepoActionResult:
    if not paths:
        completed = subprocess.CompletedProcess(["git", "add"], 2, "", "No paths supplied.\n")
        return _result("commit", ["git", "add"], completed, "Provide explicit paths for commit.")

    if required_branch:
        monitor = guard_branch(
            command_kind="commit",
            required_branch=required_branch,
            allow_main_mutation=allow_main,
            auto_switch=True,
        )
        if monitor.decision == MonitorDecision.BLOCK:
            return _monitor_block_result(
                action="commit",
                command_kind="commit",
                required_branch=required_branch,
                monitor=monitor,
                next_action="Inspect transfer operation monitor block before committing.",
            )

    branch_before_add, branch_error = _current_branch_result()
    if branch_error is not None:
        return branch_error

    if branch_before_add == "main" and not allow_main:
        return _main_commit_refusal(message)

    if required_branch and branch_before_add != required_branch:
        completed = subprocess.CompletedProcess(
            ["transfer-monitor", "commit", "--branch", required_branch],
            2,
            "",
            (
                "Transfer operation monitor branch mismatch before commit: "
                f"actual_branch={branch_before_add}; required_branch={required_branch}\n"
            ),
        )
        return _result(
            "commit",
            list(completed.args),
            completed,
            "Inspect transfer operation monitor branch mismatch before committing.",
        )

    add_command = ["git", "add", *paths]
    added = _run(add_command)
    if added.returncode != 0:
        return _result("commit", add_command, added, "Inspect path list and worktree before continuing.")

    branch_before_commit, branch_error = _current_branch_result()
    if branch_error is not None:
        return branch_error

    if branch_before_commit != branch_before_add:
        completed = subprocess.CompletedProcess(
            ["git", "commit", "-m", message],
            2,
            "",
            (
                "Refusing to commit because the current branch changed during transfer commit: "
                f"{branch_before_add} -> {branch_before_commit}\n"
            ),
        )
        return _result(
            "commit",
            completed.args,
            completed,
            "Inspect branch drift before committing.",
        )

    if branch_before_commit == "main" and not allow_main:
        return _main_commit_refusal(message)

    commit_command = ["git", "commit", "-m", message]
    committed = _run(commit_command)
    return _result("commit", commit_command, committed, "Push current branch or inspect status.")


def push_current(*, required_branch: str = "") -> RepoActionResult:
    if required_branch:
        monitor = guard_branch(
            command_kind="push-current",
            required_branch=required_branch,
            allow_main_mutation=False,
            auto_switch=True,
        )
        if monitor.decision == MonitorDecision.BLOCK:
            completed = subprocess.CompletedProcess(
                ["transfer-monitor", "push-current", "--branch", required_branch],
                2,
                "",
                (
                    "Transfer operation monitor blocked push-current: "
                    f"{monitor.reason}; actual_branch={monitor.actual_branch}; "
                    f"required_branch={monitor.required_branch}\n"
                ),
            )
            return _result(
                "push-current",
                list(completed.args),
                completed,
                "Inspect transfer operation monitor block before pushing.",
            )

    branch_completed = _run(["git", "branch", "--show-current"])
    if branch_completed.returncode != 0:
        return _result("push-current", ["git", "branch", "--show-current"], branch_completed, "Inspect repository state.")
    branch = branch_completed.stdout.strip()
    if not branch:
        completed = subprocess.CompletedProcess(["git", "push"], 2, "", "No current branch detected.\n")
        return _result("push-current", ["git", "push"], completed, "Switch to a named branch first.")

    if branch == "main":
        completed = subprocess.CompletedProcess(
            ["transfer-monitor", "push-current", "--branch", branch],
            2,
            "",
            (
                "Transfer operation monitor blocked push-current: "
                "main_mutation_not_allowed; actual_branch=main; required_branch=main\n"
            ),
        )
        return _result(
            "push-current",
            list(completed.args),
            completed,
            "Switch to a feature/admin branch before pushing.",
        )

    if required_branch and branch != required_branch:
        completed = subprocess.CompletedProcess(
            ["transfer-monitor", "push-current", "--branch", required_branch],
            2,
            "",
            (
                "Transfer operation monitor branch mismatch after guard: "
                f"actual_branch={branch}; required_branch={required_branch}\n"
            ),
        )
        return _result(
            "push-current",
            list(completed.args),
            completed,
            "Inspect transfer operation monitor branch mismatch before pushing.",
        )

    command = ["git", "push", "-u", "origin", branch]
    completed = _run(command)
    if completed.returncode != 0:
        return _result("push-current", command, completed, "Inspect push failure before continuing.")

    drift = _verify_current_branch("push-current", branch, command=command)
    if drift is not None:
        return drift

    return _result("push-current", command, completed, "Create or inspect pull request.")


def pr_create(*, base: str, head: str, title: str, body: str) -> RepoActionResult:
    if head == "current":
        branch_result = _run(["git", "branch", "--show-current"])
        resolved_head = branch_result.stdout.strip()
        if branch_result.returncode != 0 or not resolved_head:
            completed = subprocess.CompletedProcess(
                ["transfer-monitor", "pr-create", "--base", base, "--head", head],
                2,
                "",
                "Transfer operation monitor blocked pr-create: current_branch_missing; actual_branch=; required_branch=current\n",
            )
            return _result("pr-create", list(completed.args), completed, "Inspect current branch resolution before creating a PR.")
        head = resolved_head

    monitor = guard_pr_create(base_branch=base, head_branch=head)
    if monitor.decision == MonitorDecision.BLOCK:
        completed = subprocess.CompletedProcess(
            ["transfer-monitor", "pr-create", "--base", base, "--head", head],
            2,
            "",
            f"Transfer operation monitor blocked pr-create: {monitor.reason}; actual_branch={monitor.actual_branch}; required_branch={monitor.required_branch}\n",
        )
        return _result("pr-create", list(completed.args), completed, "Inspect transfer operation monitor block before creating a PR.")

    command = [
        "gh",
        "pr",
        "create",
        "--base",
        base,
        "--head",
        head,
        "--title",
        title,
        "--body",
        body,
    ]
    completed = _run(command)
    return _result("pr-create", command, completed, "Run agentic-kit transfer pr-status on the created PR.")



def repo_status(*, short: bool = True) -> RepoActionResult:
    command = ["git", "status", "--short"] if short else ["git", "status"]
    completed = _run(command)
    return _result("repo-status", command, completed, "Inspect changes, commit explicit paths, or clean the worktree.")


def repo_log(limit: int = 5) -> RepoActionResult:
    command = ["git", "log", f"-{limit}", "--oneline"]
    completed = _run(command)
    return _result("repo-log", command, completed, "Use commit SHAs for guarded PR or merge work.")


def head_sha(*, full: bool = False) -> RepoActionResult:
    command = ["git", "rev-parse", "HEAD"] if full else ["git", "rev-parse", "--short", "HEAD"]
    completed = _run(command)
    return _result("head-sha", command, completed, "Use this SHA for guarded PR or merge work.")


def repo_diff(*, cached: bool = False, name_only: bool = False) -> RepoActionResult:
    command = ["git", "diff"]
    if cached:
        command.append("--cached")
    if name_only:
        command.append("--name-only")
    completed = _run(command)
    return _result("repo-diff", command, completed, "Review the actual diff before committing or protected planning.")


def fetch_origin(branch: str = "main") -> RepoActionResult:
    command = ["git", "fetch", "origin", branch]
    completed = _run(command)
    return _result("fetch-origin", command, completed, "Fast-forward pull, switch branch, or inspect PR state.")


def pull_current() -> RepoActionResult:
    branch_completed = _run(["git", "branch", "--show-current"])
    if branch_completed.returncode != 0:
        return _result("pull-current", ["git", "branch", "--show-current"], branch_completed, "Inspect repository state.")
    branch = branch_completed.stdout.strip()
    if not branch:
        completed = subprocess.CompletedProcess(["git", "pull"], 2, "", "No current branch detected.\n")
        return _result("pull-current", ["git", "pull"], completed, "Switch to a named branch first.")
    command = ["git", "pull", "--ff-only", "origin", branch]
    completed = _run(command)
    return _result("pull-current", command, completed, "Run transfer state or continue with queued work.")


def branch_delete(branch: str, *, remote: bool = False, force: bool = False) -> RepoActionResult:
    if remote:
        command = ["git", "push", "origin", "--delete", branch]
        completed = _run(command)
        return _result("branch-delete", command, completed, "Inspect local and remote branch state.")
    command = ["git", "branch", "-D" if force else "-d", branch]
    completed = _run(command)
    return _result("branch-delete", command, completed, "Inspect local branch state.")


def pr_wait_ci(
    pr_number: int,
    *,
    expected_head_sha: str = "",
    timeout_seconds: int = 300,
    poll_seconds: int = 10,
) -> RepoActionResult:
    if expected_head_sha:
        guarded = _full_sha_guard("pr-wait-ci", expected_head_sha)
        if guarded is not None:
            return guarded
    else:
        expected_head_sha, failure = _resolve_pr_head_sha(pr_number, action="pr-wait-ci")
        if failure is not None:
            return failure

    command = [
        _agentic_kit_command(),
        "pr",
        "wait-ci",
        str(pr_number),
        "--timeout-seconds",
        str(timeout_seconds),
        "--interval-seconds",
        str(poll_seconds),
        "--expected-head-sha",
        expected_head_sha,
    ]
    completed = _run(command)
    return _result("pr-wait-ci", command, completed, "Run transfer pr-status or merge-if-green after CI is green.")


def pr_merge_safe(
    pr_number: int,
    *,
    expected_head_sha: str = "",
    main_branch: str = "main",
    merge_method: str = "squash",
    no_verify_main: bool = False,
    merge_state_timeout_seconds: int = 60,
    merge_state_poll_seconds: int = 5,
) -> RepoActionResult:
    monitor = guard_branch(
        command_kind="pr-merge-safe",
        required_branch=main_branch,
        allow_main_mutation=True,
        auto_switch=True,
    )
    if monitor.decision == MonitorDecision.BLOCK:
        monitor = _recover_known_volatile_branch_switch_block(
            command_kind="pr-merge-safe",
            required_branch=main_branch,
            monitor=monitor,
            allow_main_mutation=True,
            auto_switch=True,
        )
    if monitor.decision == MonitorDecision.BLOCK:
        return _monitor_block_result(
            action="pr-merge-safe",
            command_kind="pr-merge-safe",
            required_branch=main_branch,
            monitor=monitor,
            next_action="Inspect transfer operation monitor block before merging PR.",
        )

    if expected_head_sha:
        guarded = _full_sha_guard("pr-merge-safe", expected_head_sha)
        if guarded is not None:
            return guarded
    else:
        expected_head_sha, failure = _resolve_pr_head_sha(pr_number, action="pr-merge-safe")
        if failure is not None:
            return failure
    command = [
        _agentic_kit_command(),
        "pr",
        "merge-if-green",
        str(pr_number),
        "--expected-head-sha",
        expected_head_sha,
        "--main-branch",
        main_branch,
        "--merge-method",
        merge_method,
        "--merge-state-timeout-seconds",
        str(merge_state_timeout_seconds),
        "--merge-state-poll-seconds",
        str(merge_state_poll_seconds),
    ]
    if no_verify_main:
        command.append("--no-verify-main")
    completed = _run(command)
    return _result("pr-merge-safe", command, completed, "Sync main and run post-merge handoff refresh status.")


def post_merge_check(*, main_branch: str = "main") -> RepoActionResult:
    branch_command = ["git", "branch", "--show-current"]
    branch_completed = _run(branch_command)
    if branch_completed.returncode != 0:
        return _result("post-merge-check", branch_command, branch_completed, "Inspect repository branch state.")

    branch = branch_completed.stdout.strip()
    if branch != main_branch:
        completed = subprocess.CompletedProcess(
            branch_command,
            2,
            branch_completed.stdout,
            f"Expected branch {main_branch} before post-merge lifecycle check. Current branch: {branch}\n",
        )
        return _result("post-merge-check", branch_command, completed, f"Switch to {main_branch} and sync before post-merge check.")

    command = [_agentic_kit_command(), "handoff", "post-merge-refresh-status"]
    completed = _run(command)
    if completed.returncode != 0:
        return _result("post-merge-check", command, completed, "Inspect handoff refresh status failure before product work.")

    if "result=NOOP" in completed.stdout:
        next_action = "Continue without administrative handoff refresh."
    elif "result=REFRESH_REQUIRED" in completed.stdout:
        next_action = (
            "Run transfer admin-refresh-pr --after-pr <merged-pr-number>. "
            "Do not commit directly on main unless --allow-main is explicit."
        )
    else:
        next_action = "Inspect post-merge handoff refresh status output before continuing."

    return _result("post-merge-check", command, completed, next_action)


def admin_refresh_pr(after_pr: int, *, main_branch: str = "main") -> RepoActionResult:
    monitor = guard_branch(
        command_kind="admin-refresh-pr",
        required_branch=main_branch,
        allow_main_mutation=True,
        auto_switch=True,
    )
    if monitor.decision == MonitorDecision.BLOCK:
        return _monitor_block_result(
            action="admin-refresh-pr",
            command_kind="admin-refresh-pr",
            required_branch=main_branch,
            monitor=monitor,
            next_action="Inspect transfer operation monitor block before admin refresh.",
        )

    status_command = ["git", "status", "--short"]
    status_completed = _run(status_command)
    if status_completed.returncode != 0:
        return _result("admin-refresh-pr", status_command, status_completed, "Inspect worktree status.")
    if status_completed.stdout.strip():
        completed = subprocess.CompletedProcess(
            status_command,
            2,
            status_completed.stdout,
            "Refusing admin refresh with dirty worktree. Commit, clean, or inspect first.\n",
        )
        return _result("admin-refresh-pr", completed.args, completed, "Start admin refresh from a clean main worktree.")

    refresh_branch = f"docs/post-pr{after_pr}-handoff-refresh"
    transcript: list[str] = []

    branch_create_step = ["git", "switch", "-c", refresh_branch, main_branch]
    completed = _run(branch_create_step)
    transcript.append(f"$ {' '.join(branch_create_step)}\n{completed.stdout}{completed.stderr}")
    if completed.returncode != 0:
        combined = f"{completed.stdout}{completed.stderr}"
        if "already exists" in combined:
            existing = _existing_admin_refresh_pr(refresh_branch)
            if existing is not None:
                return existing
        return _result(
            "admin-refresh-pr",
            branch_create_step,
            completed,
            "Inspect admin refresh branch state or existing PR before continuing.",
        )

    steps = [
        [_agentic_kit_command(), "handoff", "refresh", ".agentic/handoff_state.yaml", "--write"],
        [_agentic_kit_command(), "handoff", "check"],
        [_agentic_kit_command(), "handoff", "post-merge-refresh-status"],
        ["git", "status", "--short"],
    ]

    for step in steps:
        completed = _run(step)
        transcript.append(f"$ {' '.join(step)}\n{completed.stdout}{completed.stderr}")
        if completed.returncode != 0:
            return _result("admin-refresh-pr", step, completed, "Inspect admin refresh step failure before continuing.")

    final_status = _run(["git", "status", "--short"])
    changed = tuple(line.strip() for line in final_status.stdout.splitlines() if line.strip())
    allowed = ("M .agentic/handoff_state.yaml",)
    if changed != allowed:
        completed = subprocess.CompletedProcess(
            ["git", "status", "--short"],
            2,
            final_status.stdout,
            "Admin refresh must change only .agentic/handoff_state.yaml.\n",
        )
        return _result("admin-refresh-pr", completed.args, completed, "Inspect unexpected admin refresh diff before committing.")

    commit_message = f"Refresh handoff state after PR{after_pr}"
    more_steps = [
        ["git", "add", ".agentic/handoff_state.yaml"],
        ["git", "commit", "-m", commit_message],
        ["git", "push", "-u", "origin", refresh_branch],
        [
            "gh",
            "pr",
            "create",
            "--base",
            main_branch,
            "--head",
            refresh_branch,
            "--title",
            commit_message,
            "--body",
            f"Administrative handoff-state refresh after PR{after_pr}. No product-code changes.",
        ],
    ]
    for step in more_steps:
        completed = _run(step)
        transcript.append(f"$ {' '.join(step)}\n{completed.stdout}{completed.stderr}")
        if completed.returncode != 0:
            return _result("admin-refresh-pr", step, completed, "Inspect admin refresh PR creation failure.")

    completed = subprocess.CompletedProcess(
        ["agentic-kit", "transfer", "admin-refresh-pr", "--after-pr", str(after_pr)],
        0,
        "\n".join(transcript),
        "",
    )
    return _result("admin-refresh-pr", completed.args, completed, "Run transfer pr-status on the created admin refresh PR.")


def result_json(result: RepoActionResult) -> str:
    return json.dumps(result.as_json_data(), indent=2, sort_keys=True)
