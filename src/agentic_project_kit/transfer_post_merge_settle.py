from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Callable

from agentic_project_kit.transfer_repo_actions import (
    RepoActionResult,
    admin_refresh_pr,
    post_merge_check,
    pr_merge_safe,
    pr_wait_ci,
    pull_current,
    successor_package_refresh_pr,
)


@dataclass(frozen=True)
class PostMergeSettleStep:
    name: str
    result: RepoActionResult

    def as_json_data(self) -> dict[str, object]:
        return {"name": self.name, "result": self.result.as_json_data()}


@dataclass(frozen=True)
class PostMergeSettleResult:
    after_pr: int
    result_status: str
    returncode: int
    lifecycle_state: str
    next_action: str
    refresh_limit: int
    refresh_prs: tuple[int, ...] = field(default_factory=tuple)
    refresh_kinds: tuple[str, ...] = field(default_factory=tuple)
    refresh_loop_detected: bool = False
    steps: tuple[PostMergeSettleStep, ...] = field(default_factory=tuple)

    def as_json_data(self) -> dict[str, object]:
        data = asdict(self)
        data["steps"] = [step.as_json_data() for step in self.steps]
        return data


RefreshFactory = Callable[[int], RepoActionResult]

_REFRESHABLE_STATES = {
    "NEEDS_HANDOFF_REFRESH": "handoff-refresh",
    "NEEDS_SUCCESSOR_PACKAGE_REFRESH": "successor-package-refresh",
}


def _post_merge_state(result: RepoActionResult) -> str:
    combined = f"{result.next_action}\n{result.stdout}\n{result.stderr}"
    for match in re.finditer(r"^STATE=([A-Z_]+)", combined, flags=re.MULTILINE):
        state = match.group(1)
        if state in {"READY", "NEEDS_HANDOFF_REFRESH", "NEEDS_SUCCESSOR_PACKAGE_REFRESH", "BLOCKED"}:
            return state

    if "result=NOOP" in combined and result.returncode == 0 and result.result_status == "PASS":
        return "READY"
    if "result=REFRESH_REQUIRED" in combined:
        return "NEEDS_HANDOFF_REFRESH"
    if result.returncode != 0 or result.result_status != "PASS":
        return "CHECK_FAILED"
    return "UNKNOWN"


def _extract_pr_number(text: str) -> int | None:
    for pattern in (r"existing_pr=(\d+)", r"\bPR=(\d+)\b", r"/pull/(\d+)"):
        match = re.search(pattern, text)
        if match:
            return int(match.group(1))
    return None


def _finish(
    *,
    after_pr: int,
    result_status: str,
    returncode: int,
    lifecycle_state: str,
    next_action: str,
    refresh_limit: int,
    refresh_prs: list[int],
    refresh_kinds: list[str],
    steps: list[PostMergeSettleStep],
    refresh_loop_detected: bool = False,
) -> PostMergeSettleResult:
    return PostMergeSettleResult(
        after_pr=after_pr,
        result_status=result_status,
        returncode=returncode,
        lifecycle_state=lifecycle_state,
        next_action=next_action,
        refresh_limit=refresh_limit,
        refresh_prs=tuple(refresh_prs),
        refresh_kinds=tuple(refresh_kinds),
        refresh_loop_detected=refresh_loop_detected,
        steps=tuple(steps),
    )


def _block(
    *,
    after_pr: int,
    lifecycle_state: str,
    next_action: str,
    refresh_limit: int,
    refresh_prs: list[int],
    refresh_kinds: list[str],
    steps: list[PostMergeSettleStep],
    returncode: int = 2,
    refresh_loop_detected: bool = False,
) -> PostMergeSettleResult:
    return _finish(
        after_pr=after_pr,
        result_status="BLOCKED",
        returncode=returncode,
        lifecycle_state=lifecycle_state,
        next_action=next_action,
        refresh_limit=refresh_limit,
        refresh_prs=refresh_prs,
        refresh_kinds=refresh_kinds,
        steps=steps,
        refresh_loop_detected=refresh_loop_detected,
    )


def _complete(
    *,
    after_pr: int,
    lifecycle_state: str,
    next_action: str,
    refresh_limit: int,
    refresh_prs: list[int],
    refresh_kinds: list[str],
    steps: list[PostMergeSettleStep],
) -> PostMergeSettleResult:
    return _finish(
        after_pr=after_pr,
        result_status="PASS",
        returncode=0,
        lifecycle_state=lifecycle_state,
        next_action=next_action,
        refresh_limit=refresh_limit,
        refresh_prs=refresh_prs,
        refresh_kinds=refresh_kinds,
        steps=steps,
    )


def _refresh_factory(
    *,
    state: str,
    main_branch: str,
) -> RefreshFactory | None:
    if state == "NEEDS_SUCCESSOR_PACKAGE_REFRESH":
        return lambda after_pr: successor_package_refresh_pr(after_pr, main_branch=main_branch)
    if state == "NEEDS_HANDOFF_REFRESH":
        return lambda after_pr: admin_refresh_pr(after_pr, main_branch=main_branch)
    return None


def _sync_and_check(
    *,
    steps: list[PostMergeSettleStep],
    main_branch: str,
    prefix: str,
) -> str:
    sync = pull_current()
    steps.append(PostMergeSettleStep(f"{prefix}-main-sync", sync))
    if sync.returncode != 0 or sync.result_status != "PASS":
        return "SYNC_FAILED"

    check = post_merge_check(main_branch=main_branch)
    steps.append(PostMergeSettleStep(f"{prefix}-post-merge-check", check))
    return _post_merge_state(check)


def post_merge_settle(
    after_pr: int,
    *,
    main_branch: str = "main",
    merge_method: str = "squash",
    ci_timeout_seconds: int = 300,
    ci_poll_seconds: int = 10,
    merge_state_timeout_seconds: int = 60,
    merge_state_poll_seconds: int = 5,
    refresh_limit: int = 2,
) -> PostMergeSettleResult:
    """Settle post-merge generated handoff state with a deterministic hard cap."""

    steps: list[PostMergeSettleStep] = []
    refresh_prs: list[int] = []
    refresh_kinds: list[str] = []
    current_after_pr = after_pr

    while True:
        check_name = "initial-post-merge-check" if not steps else "next-post-merge-check"
        check = post_merge_check(main_branch=main_branch)
        steps.append(PostMergeSettleStep(check_name, check))
        state = _post_merge_state(check)

        if state == "READY":
            return _complete(
                after_pr=after_pr,
                lifecycle_state="COMPLETE" if refresh_prs else "READY",
                next_action="Post-merge lifecycle is settled; stop refresh work and continue from fresh main.",
                refresh_limit=refresh_limit,
                refresh_prs=refresh_prs,
                refresh_kinds=refresh_kinds,
                steps=steps,
            )

        refresh_kind = _REFRESHABLE_STATES.get(state)
        if refresh_kind is None:
            return _block(
                after_pr=after_pr,
                lifecycle_state=state,
                next_action="Inspect post-merge-check output before creating any refresh PR.",
                refresh_limit=refresh_limit,
                refresh_prs=refresh_prs,
                refresh_kinds=refresh_kinds,
                steps=steps,
                returncode=check.returncode or 2,
            )

        if refresh_kind in refresh_kinds:
            return _block(
                after_pr=after_pr,
                lifecycle_state="REFRESH_LOOP_DETECTED",
                next_action=(
                    f"Stop: {refresh_kind} was requested more than once after PR{after_pr}; "
                    "diagnose the generated-output refresh loop before continuing."
                ),
                refresh_limit=refresh_limit,
                refresh_prs=refresh_prs,
                refresh_kinds=refresh_kinds,
                steps=steps,
                refresh_loop_detected=True,
            )

        if len(refresh_prs) >= refresh_limit:
            return _block(
                after_pr=after_pr,
                lifecycle_state="REFRESH_LIMIT_EXCEEDED",
                next_action=(
                    f"Stop: refresh limit {refresh_limit} reached after PR{after_pr}; "
                    "do not create another refresh PR without diagnosis."
                ),
                refresh_limit=refresh_limit,
                refresh_prs=refresh_prs,
                refresh_kinds=refresh_kinds,
                steps=steps,
                refresh_loop_detected=True,
            )

        create_refresh = _refresh_factory(state=state, main_branch=main_branch)
        if create_refresh is None:
            return _block(
                after_pr=after_pr,
                lifecycle_state="REFRESH_ACTION_UNKNOWN",
                next_action=f"No refresh action is registered for state {state}.",
                refresh_limit=refresh_limit,
                refresh_prs=refresh_prs,
                refresh_kinds=refresh_kinds,
                steps=steps,
            )

        create = create_refresh(current_after_pr)
        steps.append(PostMergeSettleStep(f"{refresh_kind}-pr", create))
        if create.returncode != 0 or create.result_status != "PASS":
            return _block(
                after_pr=after_pr,
                lifecycle_state=f"{refresh_kind.upper().replace('-', '_')}_PR_BLOCKED",
                next_action=f"Inspect {refresh_kind} PR creation output before continuing.",
                refresh_limit=refresh_limit,
                refresh_prs=refresh_prs,
                refresh_kinds=refresh_kinds,
                steps=steps,
            )

        create_output = f"{create.stdout}\n{create.stderr}"
        if "NOOP:" in create_output and "refresh-only handoff PR" in create_output:
            return _block(
                after_pr=after_pr,
                lifecycle_state="REFRESH_ONLY_CHAIN_BLOCKED",
                next_action="Stop: a handoff-refresh PR must not spawn a chained refresh PR.",
                refresh_limit=refresh_limit,
                refresh_prs=refresh_prs,
                refresh_kinds=refresh_kinds,
                steps=steps,
                refresh_loop_detected=True,
            )

        refresh_pr = _extract_pr_number(create_output)
        if refresh_pr is None:
            return _block(
                after_pr=after_pr,
                lifecycle_state=f"{refresh_kind.upper().replace('-', '_')}_PR_UNKNOWN",
                next_action=f"{refresh_kind} PR number was not found; inspect PR creation output.",
                refresh_limit=refresh_limit,
                refresh_prs=refresh_prs,
                refresh_kinds=refresh_kinds,
                steps=steps,
            )

        refresh_prs.append(refresh_pr)
        refresh_kinds.append(refresh_kind)

        wait = pr_wait_ci(
            refresh_pr,
            timeout_seconds=ci_timeout_seconds,
            poll_seconds=ci_poll_seconds,
        )
        steps.append(PostMergeSettleStep(f"{refresh_kind}-pr-wait-ci", wait))
        if wait.returncode != 0 or wait.result_status != "PASS":
            return _block(
                after_pr=after_pr,
                lifecycle_state=f"{refresh_kind.upper().replace('-', '_')}_CI_BLOCKED",
                next_action=f"Inspect {refresh_kind} PR CI before merging.",
                refresh_limit=refresh_limit,
                refresh_prs=refresh_prs,
                refresh_kinds=refresh_kinds,
                steps=steps,
            )

        merge = pr_merge_safe(
            refresh_pr,
            main_branch=main_branch,
            merge_method=merge_method,
            no_verify_main=False,
            merge_state_timeout_seconds=merge_state_timeout_seconds,
            merge_state_poll_seconds=merge_state_poll_seconds,
        )
        steps.append(PostMergeSettleStep(f"{refresh_kind}-pr-merge-safe", merge))

        current_after_pr = refresh_pr
        if merge.returncode == 0 and merge.result_status == "PASS":
            sync = pull_current()
            steps.append(PostMergeSettleStep(f"{refresh_kind}-post-merge-main-sync", sync))
            if sync.returncode != 0 or sync.result_status != "PASS":
                return _block(
                    after_pr=after_pr,
                    lifecycle_state="POST_REFRESH_MAIN_SYNC_BLOCKED",
                    next_action="Synchronize main before running the next post-merge check.",
                    refresh_limit=refresh_limit,
                    refresh_prs=refresh_prs,
                    refresh_kinds=refresh_kinds,
                    steps=steps,
                )
            continue

        recovery_state = _sync_and_check(
            steps=steps,
            main_branch=main_branch,
            prefix=f"{refresh_kind}-merge-recovery",
        )
        if recovery_state == "READY":
            return _complete(
                after_pr=after_pr,
                lifecycle_state="COMPLETE",
                next_action="Post-merge lifecycle is settled after refresh merge recovery.",
                refresh_limit=refresh_limit,
                refresh_prs=refresh_prs,
                refresh_kinds=refresh_kinds,
                steps=steps,
            )
        if recovery_state in _REFRESHABLE_STATES:
            continue
        return _block(
            after_pr=after_pr,
            lifecycle_state=f"{refresh_kind.upper().replace('-', '_')}_MERGE_BLOCKED",
            next_action=f"Inspect {refresh_kind} merge result and main recovery check.",
            refresh_limit=refresh_limit,
            refresh_prs=refresh_prs,
            refresh_kinds=refresh_kinds,
            steps=steps,
        )
