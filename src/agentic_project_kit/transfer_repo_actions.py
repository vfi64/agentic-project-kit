from __future__ import annotations

import json
import sys
import subprocess
from dataclasses import dataclass, asdict
from pathlib import Path


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


def branch_create(branch: str, *, start_point: str = "main", push: bool = False) -> RepoActionResult:
    command = ["git", "switch", "-c", branch, start_point]
    completed = _run(command)
    if completed.returncode != 0:
        return _result("branch-create", command, completed, "Inspect branch state before continuing.")
    if push:
        push_command = ["git", "push", "-u", "origin", branch]
        pushed = _run(push_command)
        return _result("branch-create", push_command, pushed, "Run transfer state or continue with queued work.")
    return _result("branch-create", command, completed, "Run transfer state or continue with queued work.")


def branch_switch(branch: str, *, pull: bool = False) -> RepoActionResult:
    command = ["git", "switch", branch]
    completed = _run(command)
    if completed.returncode != 0:
        return _result("branch-switch", command, completed, "Inspect branch state before continuing.")
    if pull:
        pull_command = ["git", "pull", "--ff-only", "origin", branch]
        pulled = _run(pull_command)
        return _result("branch-switch", pull_command, pulled, "Run transfer state or continue with queued work.")
    return _result("branch-switch", command, completed, "Run transfer state or continue with queued work.")


def commit_paths(message: str, paths: list[str], *, allow_main: bool = False) -> RepoActionResult:
    if not paths:
        completed = subprocess.CompletedProcess(["git", "add"], 2, "", "No paths supplied.\n")
        return _result("commit", ["git", "add"], completed, "Provide explicit paths for commit.")

    branch_command = ["git", "branch", "--show-current"]
    branch_completed = _run(branch_command)
    if branch_completed.returncode != 0:
        return _result("commit", branch_command, branch_completed, "Inspect repository branch state before committing.")

    branch = branch_completed.stdout.strip()
    if branch == "main" and not allow_main:
        completed = subprocess.CompletedProcess(
            ["git", "commit", "-m", message],
            2,
            "",
            "Refusing to commit directly on main. Use a branch or pass --allow-main explicitly.\n",
        )
        return _result("commit", completed.args, completed, "Create a feature/admin branch before committing.")

    add_command = ["git", "add", *paths]
    added = _run(add_command)
    if added.returncode != 0:
        return _result("commit", add_command, added, "Inspect path list and worktree before continuing.")
    commit_command = ["git", "commit", "-m", message]
    committed = _run(commit_command)
    return _result("commit", commit_command, committed, "Push current branch or inspect status.")


def push_current() -> RepoActionResult:
    branch_completed = _run(["git", "branch", "--show-current"])
    if branch_completed.returncode != 0:
        return _result("push-current", ["git", "branch", "--show-current"], branch_completed, "Inspect repository state.")
    branch = branch_completed.stdout.strip()
    if not branch:
        completed = subprocess.CompletedProcess(["git", "push"], 2, "", "No current branch detected.\n")
        return _result("push-current", ["git", "push"], completed, "Switch to a named branch first.")
    command = ["git", "push", "-u", "origin", branch]
    completed = _run(command)
    return _result("push-current", command, completed, "Create or inspect pull request.")


def pr_create(*, base: str, head: str, title: str, body: str) -> RepoActionResult:
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
    command = [
        _agentic_kit_command(),
        "pr",
        "wait-ci",
        str(pr_number),
        "--timeout-seconds",
        str(timeout_seconds),
        "--interval-seconds",
        str(poll_seconds),
    ]
    if expected_head_sha:
        command.extend(["--expected-head-sha", expected_head_sha])
    completed = _run(command)
    return _result("pr-wait-ci", command, completed, "Run transfer pr-status or merge-if-green after CI is green.")


def pr_merge_safe(
    pr_number: int,
    *,
    expected_head_sha: str,
    main_branch: str = "main",
    merge_method: str = "squash",
    no_verify_main: bool = False,
) -> RepoActionResult:
    guarded = _full_sha_guard("pr-merge-safe", expected_head_sha)
    if guarded is not None:
        return guarded
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
    branch_command = ["git", "branch", "--show-current"]
    branch_completed = _run(branch_command)
    if branch_completed.returncode != 0:
        return _result("admin-refresh-pr", branch_command, branch_completed, "Inspect repository branch state.")

    branch = branch_completed.stdout.strip()
    if branch != main_branch:
        completed = subprocess.CompletedProcess(
            branch_command,
            2,
            branch_completed.stdout,
            f"Expected branch {main_branch} before admin refresh. Current branch: {branch}\n",
        )
        return _result("admin-refresh-pr", branch_command, completed, f"Switch to {main_branch} and sync before admin refresh.")

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
        return _result("admin-refresh-pr", status_command, completed, "Start admin refresh from a clean main worktree.")

    refresh_branch = f"docs/post-pr{after_pr}-handoff-refresh"
    transcript: list[str] = []

    steps = [
        ["git", "switch", "-c", refresh_branch, main_branch],
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
