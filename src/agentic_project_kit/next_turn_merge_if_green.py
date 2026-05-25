from __future__ import annotations

import argparse
import subprocess
from dataclasses import dataclass
from typing import Literal

from agentic_project_kit.next_turn_pr_status import PrStatusDecision, classify_pr_status, fetch_pr_payload

MergeDecision = Literal["merge", "refuse"]


@dataclass(frozen=True)
class MergeIfGreenResult:
    pr: str
    decision: MergeDecision
    reason: str
    status_decision: PrStatusDecision
    merged: bool
    merge_output: str


def decide_merge(status: PrStatusDecision) -> tuple[MergeDecision, str]:
    if status.state != "OPEN":
        return "refuse", "PR is not open"
    if status.decision != "green":
        return "refuse", f"PR checks are not green: {status.decision}"
    if status.merge_state_status not in {"CLEAN", "UNKNOWN"}:
        return "refuse", f"merge state is not clean: {status.merge_state_status}"
    return "merge", "PR is green"


def _run_gh(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["gh", *args], text=True, capture_output=True, check=False)


def merge_if_green(pr: str, *, merge_method: str = "squash", delete_branch: bool = True, dry_run: bool = False) -> MergeIfGreenResult:
    payload = fetch_pr_payload(pr)
    status = classify_pr_status(payload, pr=pr)
    decision, reason = decide_merge(status)

    if decision != "merge" or dry_run:
        return MergeIfGreenResult(
            pr=pr,
            decision=decision,
            reason=reason if not dry_run else f"DRY_RUN: {reason}",
            status_decision=status,
            merged=False,
            merge_output="",
        )

    args = ["pr", "merge", pr, f"--{merge_method}"]
    if delete_branch:
        args.append("--delete-branch")

    completed = _run_gh(args)
    if completed.returncode != 0:
        raise RuntimeError((completed.stderr + completed.stdout).strip())

    return MergeIfGreenResult(
        pr=pr,
        decision="merge",
        reason=reason,
        status_decision=status,
        merged=True,
        merge_output=(completed.stdout + completed.stderr).strip(),
    )


def render_result(result: MergeIfGreenResult) -> str:
    lines = [
        "NEXT_TURN_MERGE_IF_GREEN",
        f"pr={result.pr}",
        f"decision={result.decision}",
        f"reason={result.reason}",
        f"status_decision={result.status_decision.decision}",
        f"state={result.status_decision.state}",
        f"merge_state_status={result.status_decision.merge_state_status}",
        f"merged={str(result.merged).lower()}",
        "failed_checks:",
        *[f"- {item}" for item in result.status_decision.failed_checks],
        "pending_checks:",
        *[f"- {item}" for item in result.status_decision.pending_checks],
        "unknown_checks:",
        *[f"- {item}" for item in result.status_decision.unknown_checks],
        "### RESULT: PASS ###" if result.decision == "merge" or not result.merged else "### RESULT: PASS ###",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(prog="next-turn-merge-if-green")
    parser.add_argument("pr")
    parser.add_argument("--merge-method", choices=["squash", "merge", "rebase"], default="squash")
    parser.add_argument("--keep-branch", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    result = merge_if_green(
        args.pr,
        merge_method=args.merge_method,
        delete_branch=not args.keep_branch,
        dry_run=args.dry_run,
    )
    print(render_result(result))
    return 0 if result.decision == "merge" or args.dry_run else 1


if __name__ == "__main__":
    raise SystemExit(main())
