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

    def as_json_data(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "action": self.action,
            "pr_number": self.pr_number,
            "result_status": self.result_status,
            "returncode": self.returncode,
            "decision": self.decision,
            "report": self.report,
        }


def pr_status_transfer(
    pr_number: int,
    *,
    no_failed_log_fetch: bool = False,
    failed_log_lines: int = 120,
) -> TransferPrStatusResult:
    payload = fetch_pr_payload(str(pr_number))
    decision = classify_pr_status(payload, pr=str(pr_number))
    if decision.decision == "red" and not no_failed_log_fetch:
        decision = attach_failed_run_logs(decision, max_lines=failed_log_lines)

    ok = decision.decision == "green"
    return TransferPrStatusResult(
        schema_version=1,
        action="pr-status",
        pr_number=pr_number,
        result_status="PASS" if ok else "FAIL",
        returncode=0 if ok else 1,
        decision=decision.decision,
        report=render_decision(decision),
    )


def pr_status_transfer_json(
    pr_number: int,
    *,
    no_failed_log_fetch: bool = False,
    failed_log_lines: int = 120,
) -> str:
    result = pr_status_transfer(
        pr_number,
        no_failed_log_fetch=no_failed_log_fetch,
        failed_log_lines=failed_log_lines,
    )
    return json.dumps(result.as_json_data(), indent=2, sort_keys=True)
