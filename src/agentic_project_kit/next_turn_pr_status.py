from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import dataclass
from typing import Any, Literal

Decision = Literal["green", "red", "pending", "unknown", "not-open"]


@dataclass(frozen=True)
class PrStatusDecision:
    pr: str
    state: str
    merge_state_status: str
    head_ref_oid: str
    decision: Decision
    successful_checks: tuple[str, ...]
    pending_checks: tuple[str, ...]
    failed_checks: tuple[str, ...]
    unknown_checks: tuple[str, ...]
    failed_run_log_hint: str


def _check_name(item: dict[str, Any]) -> str:
    return str(item.get("name") or item.get("workflowName") or item.get("__typename") or "unknown")


def classify_pr_status(payload: dict[str, Any], *, pr: str = "") -> PrStatusDecision:
    state = str(payload.get("state") or "UNKNOWN")
    checks = payload.get("statusCheckRollup") or []
    successful: list[str] = []
    pending: list[str] = []
    failed: list[str] = []
    unknown: list[str] = []

    if state != "OPEN":
        decision: Decision = "not-open"
    elif not isinstance(checks, list) or not checks:
        decision = "pending"
    else:
        for item in checks:
            if not isinstance(item, dict):
                unknown.append("unknown")
                continue
            name = _check_name(item)
            status = str(item.get("status") or "").upper()
            conclusion = str(item.get("conclusion") or "").upper()
            if status != "COMPLETED":
                pending.append(name)
            elif conclusion == "SUCCESS":
                successful.append(name)
            elif conclusion in {"FAILURE", "CANCELLED", "TIMED_OUT", "ACTION_REQUIRED"}:
                failed.append(name)
            else:
                unknown.append(name)

        if failed:
            decision = "red"
        elif pending:
            decision = "pending"
        elif unknown:
            decision = "unknown"
        else:
            decision = "green"

    hint = "none"
    if decision == "red":
        hint = "run: gh run view <failed-run-id> --log-failed"

    return PrStatusDecision(
        pr=pr,
        state=state,
        merge_state_status=str(payload.get("mergeStateStatus") or "UNKNOWN"),
        head_ref_oid=str(payload.get("headRefOid") or ""),
        decision=decision,
        successful_checks=tuple(successful),
        pending_checks=tuple(pending),
        failed_checks=tuple(failed),
        unknown_checks=tuple(unknown),
        failed_run_log_hint=hint,
    )


def render_decision(decision: PrStatusDecision) -> str:
    lines = [
        "NEXT_TURN_PR_STATUS",
        f"pr={decision.pr}",
        f"state={decision.state}",
        f"merge_state_status={decision.merge_state_status}",
        f"head_ref_oid={decision.head_ref_oid}",
        f"decision={decision.decision}",
        "successful_checks:",
        *[f"- {item}" for item in decision.successful_checks],
        "pending_checks:",
        *[f"- {item}" for item in decision.pending_checks],
        "failed_checks:",
        *[f"- {item}" for item in decision.failed_checks],
        "unknown_checks:",
        *[f"- {item}" for item in decision.unknown_checks],
        f"failed_run_log_hint={decision.failed_run_log_hint}",
        "### RESULT: PASS ###",
    ]
    return "\n".join(lines)


def _run_gh(args: list[str]) -> str:
    completed = subprocess.run(["gh", *args], text=True, capture_output=True, check=False)
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip())
    return completed.stdout


def fetch_pr_payload(pr: str) -> dict[str, Any]:
    raw = _run_gh([
        "pr",
        "view",
        pr,
        "--json",
        "state,mergeStateStatus,headRefOid,statusCheckRollup,url",
    ])
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise RuntimeError("gh pr view did not return a JSON object")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(prog="next-turn-pr-status")
    parser.add_argument("pr")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    payload = fetch_pr_payload(args.pr)
    decision = classify_pr_status(payload, pr=args.pr)
    if args.json:
        print(json.dumps(decision.__dict__, indent=2, sort_keys=True))
    else:
        print(render_decision(decision))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
