from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field

from agentic_project_kit.transfer_repo_actions import (
    RepoActionResult,
    admin_refresh_pr,
    post_merge_check,
    pr_merge_safe,
    pr_wait_ci,
    pull_current,
)


@dataclass(frozen=True)
class PostMergeLifecycleStep:
    name: str
    result: RepoActionResult

    def as_json_data(self) -> dict[str, object]:
        return {"name": self.name, "result": self.result.as_json_data()}


@dataclass(frozen=True)
class PostMergeLifecycleResult:
    after_pr: int
    result_status: str
    returncode: int
    lifecycle_state: str
    next_action: str
    refresh_pr: int | None = None
    refresh_loop_detected: bool = False
    steps: tuple[PostMergeLifecycleStep, ...] = field(default_factory=tuple)

    def as_json_data(self) -> dict[str, object]:
        data = asdict(self)
        data["steps"] = [step.as_json_data() for step in self.steps]
        return data


_REFRESH_REQUIRED = "result=REFRESH_REQUIRED"
_NOOP = "result=NOOP"
_REFRESH_ONLY_NOOP = "is already a refresh-only handoff PR"


def _post_merge_state(result: RepoActionResult) -> str:
    output = f"{result.stdout}\n{result.stderr}"
    if _NOOP in output:
        return "NOOP"
    if _REFRESH_REQUIRED in output:
        return "REFRESH_REQUIRED"
    if result.returncode != 0 or result.result_status != "PASS":
        return "CHECK_FAILED"
    return "UNKNOWN"


def _extract_pr_number(text: str) -> int | None:
    patterns = (
        r"existing_pr=(\d+)",
        r"/pull/(\d+)",
    )
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return int(match.group(1))
    return None


def _is_refresh_only_noop(text: str) -> bool:
    return _REFRESH_ONLY_NOOP in text and "NOOP:" in text


def _finish(
    *,
    after_pr: int,
    result_status: str,
    returncode: int,
    lifecycle_state: str,
    next_action: str,
    steps: list[PostMergeLifecycleStep],
    refresh_pr: int | None = None,
    refresh_loop_detected: bool = False,
) -> PostMergeLifecycleResult:
    return PostMergeLifecycleResult(
        after_pr=after_pr,
        result_status=result_status,
        returncode=returncode,
        lifecycle_state=lifecycle_state,
        next_action=next_action,
        refresh_pr=refresh_pr,
        refresh_loop_detected=refresh_loop_detected,
        steps=tuple(steps),
    )


def _finish_after_final_check(
    *,
    after_pr: int,
    refresh_pr: int,
    steps: list[PostMergeLifecycleStep],
    final_state: str,
    recovered_from_merge_block: bool = False,
) -> PostMergeLifecycleResult:
    if final_state == "NOOP":
        if recovered_from_merge_block:
            next_action = (
                "Post-merge lifecycle is complete after admin refresh merge recovery; "
                "publish or inspect the command evidence report."
            )
        else:
            next_action = "Post-merge lifecycle is complete after admin refresh."
        return _finish(
            after_pr=after_pr,
            result_status="PASS",
            returncode=0,
            lifecycle_state="COMPLETE",
            next_action=next_action,
            steps=steps,
            refresh_pr=refresh_pr,
        )

    if final_state == "REFRESH_REQUIRED":
        return _finish(
            after_pr=after_pr,
            result_status="BLOCKED",
            returncode=2,
            lifecycle_state="REFRESH_LOOP_DETECTED",
            next_action=(
                "Stop: REFRESH_REQUIRED persisted after one admin refresh; "
                "diagnose refresh loop before creating another refresh PR."
            ),
            steps=steps,
            refresh_pr=refresh_pr,
            refresh_loop_detected=True,
        )

    return _finish(
        after_pr=after_pr,
        result_status="BLOCKED",
        returncode=2,
        lifecycle_state=final_state,
        next_action="Inspect final post-merge-check output before continuing.",
        steps=steps,
        refresh_pr=refresh_pr,
    )


def _run_final_check(
    *,
    after_pr: int,
    refresh_pr: int,
    steps: list[PostMergeLifecycleStep],
    main_branch: str,
    recovered_from_merge_block: bool = False,
) -> PostMergeLifecycleResult:
    sync = pull_current()
    sync_step_name = (
        "merge-block-recovery-main-sync"
        if recovered_from_merge_block
        else "final-main-sync"
    )
    steps.append(PostMergeLifecycleStep(sync_step_name, sync))
    if sync.returncode != 0 or sync.result_status != "PASS":
        return _finish(
            after_pr=after_pr,
            result_status="BLOCKED",
            returncode=2,
            lifecycle_state="FINAL_MAIN_SYNC_BLOCKED",
            next_action="Synchronize main before running the final post-merge check.",
            steps=steps,
            refresh_pr=refresh_pr,
        )

    final_check = post_merge_check(main_branch=main_branch)
    step_name = (
        "merge-block-recovery-post-merge-check"
        if recovered_from_merge_block
        else "final-post-merge-check"
    )
    steps.append(PostMergeLifecycleStep(step_name, final_check))
    final_state = _post_merge_state(final_check)
    return _finish_after_final_check(
        after_pr=after_pr,
        refresh_pr=refresh_pr,
        steps=steps,
        final_state=final_state,
        recovered_from_merge_block=recovered_from_merge_block,
    )


def post_merge_complete(
    after_pr: int,
    *,
    main_branch: str = "main",
    merge_method: str = "squash",
    refresh_expected_head_sha: str = "",
    ci_timeout_seconds: int = 300,
    ci_poll_seconds: int = 10,
    merge_state_timeout_seconds: int = 60,
    merge_state_poll_seconds: int = 5,
) -> PostMergeLifecycleResult:
    """Complete the post-merge lifecycle after a PR merge.

    This composes existing transfer actions instead of reimplementing them.
    REFRESH_REQUIRED is a typed lifecycle state. Exactly one administrative
    refresh round is allowed; a second REFRESH_REQUIRED stops as a loop.
    """

    steps: list[PostMergeLifecycleStep] = []

    initial_check = post_merge_check(main_branch=main_branch)
    steps.append(PostMergeLifecycleStep("initial-post-merge-check", initial_check))
    initial_state = _post_merge_state(initial_check)

    if initial_check.result_status != "PASS" and initial_state != "REFRESH_REQUIRED":
        return _finish(
            after_pr=after_pr,
            result_status="BLOCKED",
            returncode=initial_check.returncode or 1,
            lifecycle_state="INITIAL_POST_MERGE_CHECK_FAILED",
            next_action=(
                initial_check.next_action
                or "Inspect failing post-merge-check before continuing."
            ),
            steps=steps,
        )

    if initial_state == "NOOP":
        return _finish(
            after_pr=after_pr,
            result_status="PASS",
            returncode=0,
            lifecycle_state="NOOP",
            next_action=(
                "Post-merge lifecycle is complete; "
                "continue with the next planned slice."
            ),
            steps=steps,
        )

    if initial_state != "REFRESH_REQUIRED":
        return _finish(
            after_pr=after_pr,
            result_status="BLOCKED",
            returncode=2,
            lifecycle_state=initial_state,
            next_action=(
                "Inspect post-merge-check output before creating any "
                "administrative refresh."
            ),
            steps=steps,
        )

    refresh_create = admin_refresh_pr(after_pr, main_branch=main_branch)
    steps.append(PostMergeLifecycleStep("admin-refresh-pr", refresh_create))
    if refresh_create.returncode != 0 or refresh_create.result_status != "PASS":
        return _finish(
            after_pr=after_pr,
            result_status="BLOCKED",
            returncode=2,
            lifecycle_state="ADMIN_REFRESH_PR_BLOCKED",
            next_action="Inspect admin-refresh-pr output before continuing.",
            steps=steps,
        )

    refresh_create_output = f"{refresh_create.stdout}\n{refresh_create.stderr}"
    if _is_refresh_only_noop(refresh_create_output):
        return _finish(
            after_pr=after_pr,
            result_status="PASS",
            returncode=0,
            lifecycle_state="REFRESH_ONLY_PR_NOOP",
            next_action=(
                "PR is already an administrative handoff refresh; "
                "no chained refresh PR is allowed."
            ),
            steps=steps,
        )

    refresh_pr = _extract_pr_number(refresh_create_output)
    if refresh_pr is None:
        return _finish(
            after_pr=after_pr,
            result_status="BLOCKED",
            returncode=2,
            lifecycle_state="ADMIN_REFRESH_PR_UNKNOWN",
            next_action=(
                "Admin refresh PR number was not found; "
                "inspect admin-refresh-pr output."
            ),
            steps=steps,
        )

    refresh_wait = pr_wait_ci(
        refresh_pr,
        expected_head_sha=refresh_expected_head_sha,
        timeout_seconds=ci_timeout_seconds,
        poll_seconds=ci_poll_seconds,
    )
    steps.append(PostMergeLifecycleStep("admin-refresh-pr-wait-ci", refresh_wait))
    if refresh_wait.returncode != 0 or refresh_wait.result_status != "PASS":
        return _finish(
            after_pr=after_pr,
            result_status="BLOCKED",
            returncode=2,
            lifecycle_state="ADMIN_REFRESH_CI_BLOCKED",
            next_action="Inspect admin refresh PR CI before merging.",
            steps=steps,
            refresh_pr=refresh_pr,
        )

    refresh_merge = pr_merge_safe(
        refresh_pr,
        expected_head_sha=refresh_expected_head_sha,
        main_branch=main_branch,
        merge_method=merge_method,
        no_verify_main=False,
        merge_state_timeout_seconds=merge_state_timeout_seconds,
        merge_state_poll_seconds=merge_state_poll_seconds,
    )
    steps.append(PostMergeLifecycleStep("admin-refresh-pr-merge-safe", refresh_merge))
    if refresh_merge.returncode != 0 or refresh_merge.result_status != "PASS":
        recovery = _run_final_check(
            after_pr=after_pr,
            refresh_pr=refresh_pr,
            steps=steps,
            main_branch=main_branch,
            recovered_from_merge_block=True,
        )
        if recovery.lifecycle_state in {"COMPLETE", "REFRESH_LOOP_DETECTED"}:
            return recovery
        return _finish(
            after_pr=after_pr,
            result_status="BLOCKED",
            returncode=2,
            lifecycle_state="ADMIN_REFRESH_MERGE_BLOCKED",
            next_action="Inspect admin refresh merge result and main CI evidence.",
            steps=steps,
            refresh_pr=refresh_pr,
        )

    return _run_final_check(
        after_pr=after_pr,
        refresh_pr=refresh_pr,
        steps=steps,
        main_branch=main_branch,
    )
