from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class FinalizeGuardStatus(StrEnum):
    PASS_ALREADY_ON_MAIN = "PASS_ALREADY_ON_MAIN"
    PASS_NOOP_BRANCH = "PASS_NOOP_BRANCH"
    PASS_NEEDS_PR = "PASS_NEEDS_PR"
    PASS_SUPERSEDED = "PASS_SUPERSEDED"
    FAIL_CONFLICT_RELEVANT = "FAIL_CONFLICT_RELEVANT"
    FAIL_NEEDS_HUMAN_REVIEW = "FAIL_NEEDS_HUMAN_REVIEW"


@dataclass(frozen=True)
class FinalizeGuardDecision:
    status: FinalizeGuardStatus
    result: str
    message: str
    needs_pr: bool = False
    needs_human_review: bool = False


def classify_finalize_guard_state(
    *,
    marker_requested: bool,
    marker_on_main: bool,
    local_branch_exists: bool,
    remote_branch_exists: bool,
    commits_ahead_of_main: int | None,
    merge_conflict: bool | None,
) -> FinalizeGuardDecision:
    if marker_requested and marker_on_main:
        return FinalizeGuardDecision(
            status=FinalizeGuardStatus.PASS_ALREADY_ON_MAIN,
            result="PASS",
            message="Idempotent completion: requested finalization marker is already present on main.",
        )

    if not local_branch_exists and not remote_branch_exists:
        return FinalizeGuardDecision(
            status=FinalizeGuardStatus.PASS_NOOP_BRANCH,
            result="PASS",
            message="Finalization branch does not exist; no cleanup or PR action is needed.",
        )

    if commits_ahead_of_main is None:
        return FinalizeGuardDecision(
            status=FinalizeGuardStatus.FAIL_NEEDS_HUMAN_REVIEW,
            result="FAIL",
            message="Cannot classify branch without ahead/behind information.",
            needs_human_review=True,
        )

    if commits_ahead_of_main == 0:
        return FinalizeGuardDecision(
            status=FinalizeGuardStatus.PASS_NOOP_BRANCH,
            result="PASS",
            message="Idempotent completion: finalization branch has no commits ahead of main.",
        )

    if merge_conflict is None:
        return FinalizeGuardDecision(
            status=FinalizeGuardStatus.FAIL_NEEDS_HUMAN_REVIEW,
            result="FAIL",
            message="Cannot classify relevant branch without merge conflict information.",
            needs_human_review=True,
        )
    if not merge_conflict:
        return FinalizeGuardDecision(
            status=FinalizeGuardStatus.PASS_NEEDS_PR,
            result="PASS",
            message="Finalization branch has relevant commits and appears mergeable; continue normal PR path.",
            needs_pr=True,
        )

    if marker_requested and marker_on_main:
        return FinalizeGuardDecision(
            status=FinalizeGuardStatus.PASS_SUPERSEDED,
            result="PASS",
            message="Finalization branch conflicts but requested marker is already represented on main.",
        )
    return FinalizeGuardDecision(
        status=FinalizeGuardStatus.FAIL_CONFLICT_RELEVANT,
        result="FAIL",
        message="Finalization branch has commits ahead of main and conflicts; human review is required.",
        needs_human_review=True,
    )
