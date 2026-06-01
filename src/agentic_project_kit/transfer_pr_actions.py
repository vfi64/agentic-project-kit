from __future__ import annotations

import json
from dataclasses import dataclass

from agentic_project_kit.next_turn_pr_status import (
    attach_failed_run_logs,
    classify_pr_status,
    fetch_pr_payload,
    render_decision,
)


@dataclass(frozen=True)
class TransferPrStatusResult:
    schema_version: int
    action: str
    pr_number: int
    result_status: str
    returncode: int
    decision: str
    report: str
    head_ref_oid: str = ""

    def as_json_data(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "action": self.action,
            "pr_number": self.pr_number,
            "result_status": self.result_status,
            "returncode": self.returncode,
            "decision": self.decision,
            "report": self.report,
            "head_ref_oid": self.head_ref_oid,
        }


def _final_signal(returncode: int) -> str:
    return "d" if returncode == 0 else "f"


def _with_final_signal(report: str, *, returncode: int, next_action: str) -> str:
    return "\n".join(
        (
            report.rstrip(),
            f"FINAL_SIGNAL={_final_signal(returncode)}",
            f"FINAL_NEXT={next_action}",
        )
    )


def _final_next(decision: str) -> str:
    if decision == "green":
        return "Run transfer pr-wait-ci or pr-merge-safe with the verified head SHA."
    return "Inspect failed or pending PR status before merge."


def pr_status_transfer(
    pr_number: int,
    *,
    no_failed_log_fetch: bool = False,
    failed_log_lines: int = 120,
    expected_head_sha: str = "",
) -> TransferPrStatusResult:
    if expected_head_sha and len(expected_head_sha) != 40:
        returncode = 2
        return TransferPrStatusResult(
            schema_version=1,
            action="pr-status",
            pr_number=pr_number,
            result_status="FAIL",
            returncode=returncode,
            decision="red",
            report=_with_final_signal(
                "HEAD_GUARD\n"
                f"expected_head_sha={expected_head_sha}\n"
                "actual_head_sha=(not-fetched)\n"
                "result=FAIL\n"
                "message=Expected full 40-character head SHA. Short SHAs are refused for guarded PR actions.\n"
                "### RESULT: FAIL ###",
                returncode=returncode,
                next_action="Re-run with the full PR head SHA.",
            ),
            head_ref_oid="",
        )
    try:
        payload = fetch_pr_payload(str(pr_number))
    except RuntimeError as exc:
        returncode = 1
        message = str(exc).strip() or "PR status lookup failed."
        return TransferPrStatusResult(
            schema_version=1,
            action="pr-status",
            pr_number=pr_number,
            result_status="FAIL",
            returncode=returncode,
            decision="red",
            report=_with_final_signal(
                "PR_STATUS_LOOKUP_FAILED\n"
                f"pr={pr_number}\n"
                "decision=red\n"
                f"message={message}\n"
                "### RESULT: FAIL ###",
                returncode=returncode,
                next_action="Inspect the PR number or discover the existing PR before continuing.",
            ),
            head_ref_oid="",
        )

    decision = classify_pr_status(payload, pr=str(pr_number))
    head_ref_oid = str(payload.get("headRefOid") or "")
    if expected_head_sha and head_ref_oid != expected_head_sha:
        returncode = 1
        report = _with_final_signal(
            render_decision(decision)
            + f"\nHEAD_GUARD\nexpected_head_sha={expected_head_sha}\nactual_head_sha={head_ref_oid}\nresult=FAIL\n### RESULT: FAIL ###",
            returncode=returncode,
            next_action="Stop and inspect the PR head SHA mismatch before continuing.",
        )
        return TransferPrStatusResult(
            schema_version=1,
            action="pr-status",
            pr_number=pr_number,
            result_status="FAIL",
            returncode=returncode,
            decision="red",
            report=report,
            head_ref_oid=head_ref_oid,
        )
    if decision.decision == "red" and not no_failed_log_fetch:
        decision = attach_failed_run_logs(decision, max_lines=failed_log_lines)

    ok = decision.decision == "green"
    returncode = 0 if ok else 1
    return TransferPrStatusResult(
        schema_version=1,
        action="pr-status",
        pr_number=pr_number,
        result_status="PASS" if ok else "FAIL",
        returncode=returncode,
        decision=decision.decision,
        report=_with_final_signal(
            render_decision(decision),
            returncode=returncode,
            next_action=_final_next(decision.decision),
        ),
        head_ref_oid=head_ref_oid,
    )


def pr_status_transfer_json(
    pr_number: int,
    *,
    no_failed_log_fetch: bool = False,
    failed_log_lines: int = 120,
    expected_head_sha: str = "",
) -> str:
    result = pr_status_transfer(
        pr_number,
        no_failed_log_fetch=no_failed_log_fetch,
        failed_log_lines=failed_log_lines,
        expected_head_sha=expected_head_sha,
    )
    return json.dumps(result.as_json_data(), indent=2, sort_keys=True)
