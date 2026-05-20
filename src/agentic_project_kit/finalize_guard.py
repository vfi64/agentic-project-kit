from __future__ import annotations

import argparse
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
        status = FinalizeGuardStatus.PASS_ALREADY_ON_MAIN if marker_requested and marker_on_main else FinalizeGuardStatus.PASS_NOOP_BRANCH
        message = "Idempotent completion: requested finalization marker is already present on main." if status == FinalizeGuardStatus.PASS_ALREADY_ON_MAIN else "Idempotent completion: finalization branch has no commits ahead of main."
        return FinalizeGuardDecision(status=status, result="PASS", message=message)

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


def render_finalize_guard_decision(decision: FinalizeGuardDecision) -> str:
    return "\n".join((
        f"STATUS: {decision.status.value}",
        decision.message,
        f"### RESULT: {decision.result} ###",
    ))


def _parse_bool(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "y"}:
        return True
    if normalized in {"0", "false", "no", "n"}:
        return False
    raise argparse.ArgumentTypeError(f"expected boolean value, got {value!r}")


def _parse_optional_int(value: str) -> int | None:
    normalized = value.strip().lower()
    if normalized in {"none", "unknown", ""}:
        return None
    return int(value)


def _parse_optional_bool(value: str) -> bool | None:
    normalized = value.strip().lower()
    if normalized in {"none", "unknown", ""}:
        return None
    return _parse_bool(value)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Classify finalize-guard state.")
    parser.add_argument("--marker-requested", required=True, type=_parse_bool)
    parser.add_argument("--marker-on-main", required=True, type=_parse_bool)
    parser.add_argument("--local-branch-exists", required=True, type=_parse_bool)
    parser.add_argument("--remote-branch-exists", required=True, type=_parse_bool)
    parser.add_argument("--commits-ahead-of-main", required=True, type=_parse_optional_int)
    parser.add_argument("--merge-conflict", required=True, type=_parse_optional_bool)
    args = parser.parse_args(argv)
    decision = classify_finalize_guard_state(
        marker_requested=args.marker_requested,
        marker_on_main=args.marker_on_main,
        local_branch_exists=args.local_branch_exists,
        remote_branch_exists=args.remote_branch_exists,
        commits_ahead_of_main=args.commits_ahead_of_main,
        merge_conflict=args.merge_conflict,
    )
    print(render_finalize_guard_decision(decision))
    return 0 if decision.result == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
