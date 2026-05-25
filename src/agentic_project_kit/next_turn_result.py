from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

WorkResult = Literal["PASS", "FAIL", "PENDING", "HARD_FAIL", "PASS_ALREADY_DONE", "NOOP"]
EvidenceResult = Literal["PASS", "FAIL", "PARTIAL", "CHAT_ONLY", "NOT_REQUIRED", "LOCAL_LOG"]
RemoteEvidence = Literal["PASS", "FAIL", "PARTIAL", "NOT_REQUIRED"]


@dataclass(frozen=True)
class NextTurnResult:
    run_id: str
    work_result: WorkResult
    evidence_result: EvidenceResult
    overall_result: WorkResult
    remote_evidence: RemoteEvidence
    terminal_log: str
    remote_terminal_log: str
    command_report: str
    next_chat_reply: str
    timestamp_utc: str
    reason: str = ""


def classify_next_chat_reply(overall_result: str, remote_evidence: str) -> str:
    if overall_result in {"PASS", "PASS_ALREADY_DONE", "NOOP"}:
        return "d"
    if remote_evidence in {"PASS", "PARTIAL"}:
        return "f"
    return "paste-output"


def build_result(
    *,
    run_id: str,
    work_result: WorkResult,
    evidence_result: EvidenceResult,
    remote_evidence: RemoteEvidence,
    terminal_log: str = "NONE",
    remote_terminal_log: str = "NONE",
    command_report: str = "NONE",
    reason: str = "",
) -> NextTurnResult:
    next_chat_reply = classify_next_chat_reply(work_result, remote_evidence)
    return NextTurnResult(
        run_id=run_id,
        work_result=work_result,
        evidence_result=evidence_result,
        overall_result=work_result,
        remote_evidence=remote_evidence,
        terminal_log=terminal_log,
        remote_terminal_log=remote_terminal_log,
        command_report=command_report,
        next_chat_reply=next_chat_reply,
        timestamp_utc=datetime.now(UTC).isoformat(),
        reason=reason,
    )


def result_paths(run_id: str, root: Path | str = ".") -> tuple[Path, Path, Path]:
    root_path = Path(root)
    report = root_path / "docs" / "reports" / "command_runs" / f"{run_id}.json"
    latest = root_path / "docs" / "reports" / "command_runs" / "next-turn-latest.json"
    terminal = root_path / "docs" / "reports" / "terminal" / f"{run_id}.log"
    return report, latest, terminal


def write_result(result: NextTurnResult, root: Path | str = ".") -> tuple[Path, Path]:
    report, latest, _terminal = result_paths(result.run_id, root)
    report.parent.mkdir(parents=True, exist_ok=True)
    payload = asdict(result)
    report.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    latest.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report, latest


def render_summary(result: NextTurnResult) -> str:
    return "\n".join(
        [
            "================================================================",
            "SUMMARY",
            f"WORK RESULT: {result.work_result}",
            f"EVIDENCE RESULT: {result.evidence_result}",
            f"OVERALL RESULT: {result.overall_result}",
            f"REMOTE_EVIDENCE: {result.remote_evidence}",
            f"terminal_log={result.terminal_log}",
            f"remote_terminal_log={result.remote_terminal_log}",
            f"command_report={result.command_report}",
            f"NEXT_CHAT_REPLY: {result.next_chat_reply}",
            f"CHAT_REPLY: {result.next_chat_reply}",
            f"### RESULT: {result.overall_result} ###",
            "================================================================",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(prog="next-turn-result")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--work-result", required=True, choices=["PASS", "FAIL", "PENDING", "HARD_FAIL", "PASS_ALREADY_DONE", "NOOP"])
    parser.add_argument("--evidence-result", default="LOCAL_LOG")
    parser.add_argument("--remote-evidence", default="NOT_REQUIRED")
    parser.add_argument("--terminal-log", default="NONE")
    parser.add_argument("--remote-terminal-log", default="NONE")
    parser.add_argument("--command-report", default="NONE")
    parser.add_argument("--reason", default="")
    args = parser.parse_args()

    result = build_result(
        run_id=args.run_id,
        work_result=args.work_result,
        evidence_result=args.evidence_result,
        remote_evidence=args.remote_evidence,
        terminal_log=args.terminal_log,
        remote_terminal_log=args.remote_terminal_log,
        command_report=args.command_report,
        reason=args.reason,
    )
    write_result(result)
    print(render_summary(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
