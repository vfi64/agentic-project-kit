from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class WorkResult(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    PENDING = "PENDING"
    HARD_FAIL = "HARD-FAIL"


class EvidenceResult(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    PARTIAL = "PARTIAL"
    CHAT_ONLY = "CHAT_ONLY"
    NOT_REQUIRED = "NOT_REQUIRED"


class RemoteEvidence(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    PARTIAL = "PARTIAL"
    NOT_REQUIRED = "NOT_REQUIRED"


class NextChatReply(StrEnum):
    D = "d"
    F = "f"
    PASTE_OUTPUT = "paste-output"
    CONTINUE = "continue"
    STOP = "stop"


@dataclass(frozen=True)
class RunSummary:
    work_result: WorkResult
    evidence_result: EvidenceResult
    overall_result: WorkResult
    remote_evidence: RemoteEvidence
    terminal_log: str = "NONE"
    command_report: str = "NONE"
    next_chat_reply: NextChatReply = NextChatReply.D


def render_run_summary(summary: RunSummary) -> str:
    lines = [
        "================================================================",
        "SUMMARY",
        f"WORK RESULT: {summary.work_result.value}",
        f"EVIDENCE RESULT: {summary.evidence_result.value}",
        f"OVERALL RESULT: {summary.overall_result.value}",
        f"REMOTE_EVIDENCE: {summary.remote_evidence.value}",
        f"terminal_log={summary.terminal_log}",
        f"command_report={summary.command_report}",
        f"NEXT_CHAT_REPLY: {summary.next_chat_reply.value}",
        f"### RESULT: {summary.overall_result.value} ###",
        "================================================================",
    ]
    return "\n".join(lines)


def summary_for_status(status: int, terminal_log: str = "NONE", command_report: str = "NONE", remote_evidence: RemoteEvidence = RemoteEvidence.PARTIAL) -> RunSummary:
    if status == 0:
        return RunSummary(WorkResult.PASS, EvidenceResult.PASS, WorkResult.PASS, remote_evidence, terminal_log, command_report, NextChatReply.D)
    return RunSummary(WorkResult.FAIL, EvidenceResult.PARTIAL, WorkResult.FAIL, remote_evidence, terminal_log, command_report, NextChatReply.F)
