from __future__ import annotations

import argparse
import json
import subprocess
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any
from typing import Literal

from agentic_project_kit.next_turn_pr_status import (
    PrStatusDecision,
    attach_failed_run_logs,
    classify_pr_status,
    fetch_pr_payload,
)

MergeDecision = Literal["merge", "refuse"]
MainRunFetcher = Callable[[str, str], dict[str, Any]]
FailedLogFetcher = Callable[[str], tuple[int, str, str]]
Sleep = Callable[[float], None]


@dataclass(frozen=True)
class MergeIfGreenResult:
    pr: str
    decision: MergeDecision
    reason: str
    status_decision: PrStatusDecision
    merged: bool
    merge_output: str
    merge_commit_sha: str = ""
    main_verification_required: bool = False
    main_status_decision: PrStatusDecision | None = None
    main_verification_error: str = ""


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


def _run_gh_json(args: list[str]) -> Any:
    completed = _run_gh(args)
    if completed.returncode != 0:
        raise RuntimeError((completed.stderr + completed.stdout).strip())
    return json.loads(completed.stdout)


def fetch_merge_commit_sha(pr: str) -> str:
    payload = _run_gh_json(["pr", "view", pr, "--json", "state,mergeCommit,mergedAt"])
    if not isinstance(payload, dict):
        raise RuntimeError("gh pr view did not return a JSON object")
    merge_commit = payload.get("mergeCommit") or {}
    if not isinstance(merge_commit, dict):
        return ""
    return str(merge_commit.get("oid") or "")


def fetch_main_run_payload(commit_sha: str, branch: str) -> dict[str, Any]:
    runs = _run_gh_json(
        [
            "run",
            "list",
            "--branch",
            branch,
            "--commit",
            commit_sha,
            "--limit",
            "20",
            "--json",
            "databaseId,status,conclusion,name,workflowName,url",
        ]
    )
    if not isinstance(runs, list):
        raise RuntimeError("gh run list did not return a JSON array")
    checks: list[dict[str, Any]] = []
    for run in runs:
        if not isinstance(run, dict):
            continue
        checks.append(
            {
                "name": run.get("name") or run.get("workflowName") or "workflow",
                "status": run.get("status"),
                "conclusion": run.get("conclusion"),
                "detailsUrl": run.get("url") or "",
            }
        )
    return {
        "state": "OPEN",
        "mergeStateStatus": "CLEAN",
        "headRefOid": commit_sha,
        "statusCheckRollup": checks,
    }


def verify_main_ci(
    commit_sha: str,
    *,
    branch: str = "main",
    timeout_seconds: int = 300,
    poll_seconds: int = 10,
    failed_log_lines: int = 120,
    fetcher: MainRunFetcher = fetch_main_run_payload,
    failed_log_fetcher: FailedLogFetcher | None = None,
    sleep: Sleep = time.sleep,
) -> PrStatusDecision:
    attempts = max(1, int(timeout_seconds / poll_seconds) if poll_seconds > 0 else 1)
    status: PrStatusDecision | None = None
    for attempt in range(1, attempts + 1):
        payload = fetcher(commit_sha, branch)
        status = classify_pr_status(payload, pr=f"{branch}@{commit_sha[:12]}")
        if status.decision not in {"pending", "no-checks"}:
            break
        if attempt < attempts and poll_seconds > 0:
            sleep(poll_seconds)
    if status is None:
        payload = fetcher(commit_sha, branch)
        status = classify_pr_status(payload, pr=f"{branch}@{commit_sha[:12]}")
    if status.decision == "red":
        if failed_log_fetcher is None:
            status = attach_failed_run_logs(status, max_lines=failed_log_lines)
        else:
            status = attach_failed_run_logs(status, max_lines=failed_log_lines, fetcher=failed_log_fetcher)
    return status


def merge_if_green(
    pr: str,
    *,
    merge_method: str = "squash",
    delete_branch: bool = True,
    dry_run: bool = False,
    verify_main: bool = True,
    main_branch: str = "main",
    main_ci_timeout_seconds: int = 300,
    main_ci_poll_seconds: int = 10,
) -> MergeIfGreenResult:
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
            main_verification_required=False,
        )

    args = ["pr", "merge", pr, f"--{merge_method}"]
    if delete_branch:
        args.append("--delete-branch")

    completed = _run_gh(args)
    if completed.returncode != 0:
        raise RuntimeError((completed.stderr + completed.stdout).strip())

    merge_commit_sha = ""
    main_status: PrStatusDecision | None = None
    main_error = ""
    if verify_main:
        try:
            merge_commit_sha = fetch_merge_commit_sha(pr)
            if not merge_commit_sha:
                main_error = "merged PR did not expose mergeCommit.oid"
            else:
                main_status = verify_main_ci(
                    merge_commit_sha,
                    branch=main_branch,
                    timeout_seconds=main_ci_timeout_seconds,
                    poll_seconds=main_ci_poll_seconds,
                )
        except RuntimeError as exc:
            main_error = str(exc)

    return MergeIfGreenResult(
        pr=pr,
        decision="merge",
        reason=reason,
        status_decision=status,
        merged=True,
        merge_output=(completed.stdout + completed.stderr).strip(),
        merge_commit_sha=merge_commit_sha,
        main_verification_required=verify_main,
        main_status_decision=main_status,
        main_verification_error=main_error,
    )


def main_verification_passed(result: MergeIfGreenResult) -> bool:
    if not result.main_verification_required:
        return True
    return result.main_status_decision is not None and result.main_status_decision.decision == "green"


def _render_failed_run_diagnostics(status: PrStatusDecision | None) -> list[str]:
    if status is None:
        return []
    lines: list[str] = []
    for diagnostic in status.failed_run_diagnostics:
        lines.extend(
            [
                (
                    f"- check={diagnostic.check_name} conclusion={diagnostic.conclusion} "
                    f"run_id={diagnostic.run_id or '(missing)'} log_status={diagnostic.log_status}"
                ),
                f"  command={diagnostic.command or '(unavailable)'}",
                f"  details_url={diagnostic.details_url or '(missing)'}",
            ]
        )
        if diagnostic.error:
            lines.append(f"  error={diagnostic.error}")
        if diagnostic.log_excerpt:
            lines.append("  log_excerpt:")
            lines.extend(f"    {line}" for line in diagnostic.log_excerpt.splitlines())
    return lines


def render_result(result: MergeIfGreenResult) -> str:
    main_status = result.main_status_decision
    main_decision = main_status.decision if main_status is not None else "not-run"
    main_failed_hint = main_status.failed_run_log_hint if main_status is not None else "none"
    final_marker = "### RESULT: PASS ###" if main_verification_passed(result) else "### RESULT: FAIL ###"
    lines = [
        "NEXT_TURN_MERGE_IF_GREEN",
        f"pr={result.pr}",
        f"decision={result.decision}",
        f"reason={result.reason}",
        f"status_decision={result.status_decision.decision}",
        f"state={result.status_decision.state}",
        f"merge_state_status={result.status_decision.merge_state_status}",
        f"merged={str(result.merged).lower()}",
        f"merge_commit_sha={result.merge_commit_sha or '(unknown)'}",
        f"main_verification_required={str(result.main_verification_required).lower()}",
        f"main_verification_decision={main_decision}",
        f"main_verification_passed={str(main_verification_passed(result)).lower()}",
        f"main_failed_run_log_hint={main_failed_hint}",
        f"main_verification_error={result.main_verification_error or 'none'}",
        "failed_checks:",
        *[f"- {item}" for item in result.status_decision.failed_checks],
        "pending_checks:",
        *[f"- {item}" for item in result.status_decision.pending_checks],
        "unknown_checks:",
        *[f"- {item}" for item in result.status_decision.unknown_checks],
        "main_failed_run_diagnostics:",
        *_render_failed_run_diagnostics(main_status),
        final_marker,
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(prog="next-turn-merge-if-green")
    parser.add_argument("pr")
    parser.add_argument("--merge-method", choices=["squash", "merge", "rebase"], default="squash")
    parser.add_argument("--keep-branch", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--skip-main-verification", action="store_true")
    parser.add_argument("--main-branch", default="main")
    parser.add_argument("--main-ci-timeout-seconds", type=int, default=300)
    parser.add_argument("--main-ci-poll-seconds", type=int, default=10)
    args = parser.parse_args()

    result = merge_if_green(
        args.pr,
        merge_method=args.merge_method,
        delete_branch=not args.keep_branch,
        dry_run=args.dry_run,
        verify_main=not args.skip_main_verification,
        main_branch=args.main_branch,
        main_ci_timeout_seconds=args.main_ci_timeout_seconds,
        main_ci_poll_seconds=args.main_ci_poll_seconds,
    )
    print(render_result(result))
    if args.dry_run:
        return 0
    return 0 if result.decision == "merge" and main_verification_passed(result) else 1


if __name__ == "__main__":
    raise SystemExit(main())
