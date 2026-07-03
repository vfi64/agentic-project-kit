from __future__ import annotations

import json
import subprocess
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from agentic_project_kit.transfer_post_merge_lifecycle import post_merge_complete
from agentic_project_kit.transfer_repo_actions import (
    RepoActionResult,
    pr_merge_safe,
    pr_wait_ci,
    repo_status,
)


@dataclass(frozen=True)
class PrCloseoutStep:
    name: str
    result_status: str
    returncode: int
    next_action: str
    stdout: str = ""
    stderr: str = ""

    def as_json_data(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class PrCloseoutCompleteResult:
    after_pr: int
    result_status: str
    returncode: int
    lifecycle_state: str
    next_action: str
    merged_pr: bool
    refresh_pr: int | None = None
    steps: tuple[PrCloseoutStep, ...] = field(default_factory=tuple)

    def as_json_data(self) -> dict[str, object]:
        data = asdict(self)
        data["steps"] = [step.as_json_data() for step in self.steps]
        return data


def _run_command(command: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _completed_step(name: str, completed: subprocess.CompletedProcess[str], next_action: str) -> PrCloseoutStep:
    return PrCloseoutStep(
        name=name,
        result_status="PASS" if completed.returncode == 0 else "FAIL",
        returncode=completed.returncode,
        next_action=next_action,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )


def _repo_step(name: str, result: RepoActionResult) -> PrCloseoutStep:
    return PrCloseoutStep(
        name=name,
        result_status=result.result_status,
        returncode=result.returncode,
        next_action=result.next_action,
        stdout=result.stdout,
        stderr=result.stderr,
    )


def _lifecycle_step(name: str, result: Any) -> PrCloseoutStep:
    payload = result.as_json_data() if hasattr(result, "as_json_data") else {}
    stdout = json.dumps(payload, indent=2, sort_keys=True)
    return PrCloseoutStep(
        name=name,
        result_status=str(getattr(result, "result_status", "UNKNOWN")),
        returncode=int(getattr(result, "returncode", 2)),
        next_action=str(getattr(result, "next_action", "Inspect lifecycle result.")),
        stdout=stdout,
        stderr="",
    )


def _finish(
    *,
    after_pr: int,
    result_status: str,
    returncode: int,
    lifecycle_state: str,
    next_action: str,
    merged_pr: bool,
    steps: list[PrCloseoutStep],
    refresh_pr: int | None = None,
) -> PrCloseoutCompleteResult:
    return PrCloseoutCompleteResult(
        after_pr=after_pr,
        result_status=result_status,
        returncode=returncode,
        lifecycle_state=lifecycle_state,
        next_action=next_action,
        merged_pr=merged_pr,
        refresh_pr=refresh_pr,
        steps=tuple(steps),
    )


def _load_pr_info(after_pr: int) -> tuple[dict[str, Any], subprocess.CompletedProcess[str]]:
    command = [
        "gh",
        "pr",
        "view",
        str(after_pr),
        "--json",
        "number,state,merged,headRefOid,url,title",
    ]
    completed = _run_command(command)
    if completed.returncode != 0:
        return {}, completed
    try:
        parsed = json.loads(completed.stdout or "{}")
    except json.JSONDecodeError as exc:
        bad = subprocess.CompletedProcess(
            command,
            2,
            completed.stdout,
            f"Could not parse PR info JSON: {exc}\n",
        )
        return {}, bad
    if not isinstance(parsed, dict):
        bad = subprocess.CompletedProcess(command, 2, completed.stdout, "PR info did not return an object.\n")
        return {}, bad
    return parsed, completed


def _is_worktree_clean() -> tuple[bool, subprocess.CompletedProcess[str]]:
    completed = _run_command(["git", "status", "--porcelain"])
    return completed.returncode == 0 and not completed.stdout.strip(), completed


def pr_closeout_complete(
    after_pr: int,
    *,
    main_branch: str = "main",
    merge_method: str = "squash",
    timeout_seconds: int = 300,
    poll_seconds: int = 10,
    merge_state_timeout_seconds: int = 60,
    merge_state_poll_seconds: int = 5,
) -> PrCloseoutCompleteResult:
    """Complete a substantive PR and its post-merge handoff lifecycle.

    This is the high-level wrapper that LLM-facing command composition should
    prefer over manually chaining PR wait, merge, main sync, post-merge-check,
    post-merge-complete, and repo-status commands.

    The function is intentionally idempotent:
    - if the PR is already merged, it resumes at post-merge closeout;
    - if the handoff refresh is already complete, post_merge_complete returns NOOP;
    - if a refresh PR already exists, the lower lifecycle handles the recovery path.
    """

    steps: list[PrCloseoutStep] = []

    clean, status = _is_worktree_clean()
    steps.append(_completed_step("local-clean-preflight", status, "Clean the worktree before PR closeout."))
    if not clean:
        return _finish(
            after_pr=after_pr,
            result_status="BLOCKED",
            returncode=2,
            lifecycle_state="DIRTY_WORKTREE",
            next_action="Clean or commit local changes before running pr-closeout-complete.",
            merged_pr=False,
            steps=steps,
        )

    switch = _run_command(["git", "switch", main_branch])
    steps.append(_completed_step("switch-main", switch, "Switch to main before PR closeout."))
    if switch.returncode != 0:
        return _finish(
            after_pr=after_pr,
            result_status="BLOCKED",
            returncode=2,
            lifecycle_state="MAIN_SWITCH_BLOCKED",
            next_action="Inspect main branch switch failure.",
            merged_pr=False,
            steps=steps,
        )

    pull = _run_command(["git", "pull", "--ff-only", "origin", main_branch])
    steps.append(_completed_step("sync-main-before-pr-closeout", pull, "Synchronize main before PR closeout."))
    if pull.returncode != 0:
        return _finish(
            after_pr=after_pr,
            result_status="BLOCKED",
            returncode=2,
            lifecycle_state="MAIN_SYNC_BLOCKED",
            next_action="Inspect main pull failure before PR closeout.",
            merged_pr=False,
            steps=steps,
        )

    pr_info, pr_lookup = _load_pr_info(after_pr)
    steps.append(_completed_step("pr-state-lookup", pr_lookup, "Inspect PR state lookup failure."))
    if pr_lookup.returncode != 0:
        return _finish(
            after_pr=after_pr,
            result_status="BLOCKED",
            returncode=2,
            lifecycle_state="PR_STATE_LOOKUP_BLOCKED",
            next_action="Inspect PR state lookup before continuing.",
            merged_pr=False,
            steps=steps,
        )

    merged = bool(pr_info.get("merged"))
    expected_head_sha = str(pr_info.get("headRefOid") or "")

    if not merged:
        wait_ci = pr_wait_ci(
            after_pr,
            expected_head_sha=expected_head_sha,
            timeout_seconds=timeout_seconds,
            poll_seconds=poll_seconds,
        )
        steps.append(_repo_step("pr-wait-ci", wait_ci))
        if wait_ci.returncode != 0 or wait_ci.result_status != "PASS":
            return _finish(
                after_pr=after_pr,
                result_status="BLOCKED",
                returncode=2,
                lifecycle_state="PR_CI_BLOCKED",
                next_action="Inspect PR CI before merging.",
                merged_pr=False,
                steps=steps,
            )

        merge = pr_merge_safe(
            after_pr,
            expected_head_sha=expected_head_sha,
            main_branch=main_branch,
            merge_method=merge_method,
            merge_state_timeout_seconds=merge_state_timeout_seconds,
            merge_state_poll_seconds=merge_state_poll_seconds,
        )
        steps.append(_repo_step("pr-merge-safe", merge))
        if merge.returncode != 0 or merge.result_status != "PASS":
            return _finish(
                after_pr=after_pr,
                result_status="BLOCKED",
                returncode=2,
                lifecycle_state="PR_MERGE_BLOCKED",
                next_action="Inspect guarded PR merge before post-merge closeout.",
                merged_pr=False,
                steps=steps,
            )
        merged = True

        sync_after_merge = _run_command(["git", "switch", main_branch])
        steps.append(_completed_step("switch-main-after-pr-merge", sync_after_merge, "Switch to main after PR merge."))
        if sync_after_merge.returncode != 0:
            return _finish(
                after_pr=after_pr,
                result_status="BLOCKED",
                returncode=2,
                lifecycle_state="MAIN_SWITCH_AFTER_MERGE_BLOCKED",
                next_action="Inspect main switch after merge.",
                merged_pr=merged,
                steps=steps,
            )

        pull_after_merge = _run_command(["git", "pull", "--ff-only", "origin", main_branch])
        steps.append(_completed_step("sync-main-after-pr-merge", pull_after_merge, "Synchronize main after PR merge."))
        if pull_after_merge.returncode != 0:
            return _finish(
                after_pr=after_pr,
                result_status="BLOCKED",
                returncode=2,
                lifecycle_state="MAIN_SYNC_AFTER_MERGE_BLOCKED",
                next_action="Inspect main pull after PR merge.",
                merged_pr=merged,
                steps=steps,
            )

    closeout = post_merge_complete(
        after_pr,
        main_branch=main_branch,
        merge_method=merge_method,
        ci_timeout_seconds=timeout_seconds,
        ci_poll_seconds=poll_seconds,
        merge_state_timeout_seconds=merge_state_timeout_seconds,
        merge_state_poll_seconds=merge_state_poll_seconds,
    )
    steps.append(_lifecycle_step("post-merge-complete", closeout))

    refresh_pr = getattr(closeout, "refresh_pr", None)
    if int(getattr(closeout, "returncode", 2)) != 0 or str(getattr(closeout, "result_status", "")) != "PASS":
        return _finish(
            after_pr=after_pr,
            result_status="BLOCKED",
            returncode=2,
            lifecycle_state=str(getattr(closeout, "lifecycle_state", "POST_MERGE_CLOSEOUT_BLOCKED")),
            next_action=str(getattr(closeout, "next_action", "Inspect post-merge closeout result.")),
            merged_pr=merged,
            refresh_pr=refresh_pr,
            steps=steps,
        )

    final_status = repo_status()
    steps.append(_repo_step("repo-status", final_status))
    if final_status.returncode != 0 or final_status.stdout.strip():
        return _finish(
            after_pr=after_pr,
            result_status="BLOCKED",
            returncode=2,
            lifecycle_state="FINAL_REPO_STATUS_BLOCKED",
            next_action="Inspect final repo status after PR closeout.",
            merged_pr=merged,
            refresh_pr=refresh_pr,
            steps=steps,
        )

    return _finish(
        after_pr=after_pr,
        result_status="PASS",
        returncode=0,
        lifecycle_state="COMPLETE",
        next_action="PR closeout complete; continue with the next governed slice.",
        merged_pr=merged,
        refresh_pr=refresh_pr,
        steps=steps,
    )
