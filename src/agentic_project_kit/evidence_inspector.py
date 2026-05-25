from __future__ import annotations

import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from agentic_project_kit.run_summary_renderer import SummaryPayload
from agentic_project_kit.run_summary_renderer import validate_summary_data

PASS_MARKER = "### RESULT: PASS ###"
FAIL_MARKER = "### RESULT: FAIL ###"
LATEST_TERMINAL_POINTER = Path("docs/reports/terminal/LATEST_TERMINAL_LOG.txt")
STRUCTURED_SUMMARY_HEADER = "SUMMARY COMM-"
SUMMARY_BOUNDARY = "================================================================"


class EvidenceVerdict(str, Enum):
    PASS_CONTINUE = "PASS_CONTINUE"
    FAIL_DIAGNOSE = "FAIL_DIAGNOSE"
    MISSING_EVIDENCE_UPLOAD_FIRST = "MISSING_EVIDENCE_UPLOAD_FIRST"
    AMBIGUOUS_SUMMARY_REVIEW_REQUIRED = "AMBIGUOUS_SUMMARY_REVIEW_REQUIRED"


@dataclass(frozen=True)
class ParsedSummary:
    found: bool
    valid: bool
    payload: SummaryPayload = SummaryPayload()
    result_marker: str = ""
    findings: tuple[str, ...] = ()

    @property
    def work(self) -> str:
        return self.payload.work

    @property
    def evidence(self) -> str:
        return self.payload.evidence

    @property
    def overall(self) -> str:
        return self.payload.overall

    @property
    def remote_evidence(self) -> str:
        return self.payload.remote_evidence

    @property
    def chat_reply(self) -> str:
        return self.payload.chat_reply or self.payload.next

    @property
    def overall_pass(self) -> bool:
        return self.valid and self.overall == "PASS" and self.result_marker == "PASS"

    @property
    def overall_fail(self) -> bool:
        return self.valid and self.overall in {"FAIL", "HARD-FAIL"}


@dataclass(frozen=True)
class EvidenceInspection:
    path: Path | None
    exists: bool
    verdict: EvidenceVerdict
    final_marker: str | None = None
    pass_markers: int = 0
    fail_markers: int = 0
    hidden_fail_before_final_pass: bool = False
    structured_summary: ParsedSummary = ParsedSummary(found=False, valid=False)
    require_summary: bool = False
    git_branch: str = "UNKNOWN"
    git_status: tuple[str, ...] = ()

    @property
    def success(self) -> bool:
        return self.verdict == EvidenceVerdict.PASS_CONTINUE


def _run_git(args: list[str], root: Path) -> tuple[str, ...]:
    completed = subprocess.run(["git", *args], cwd=root, text=True, capture_output=True, check=False)
    if completed.returncode != 0:
        return ("UNKNOWN",)
    text = completed.stdout.strip()
    return tuple(text.splitlines()) if text else ()


def resolve_latest_evidence(root: Path | str = ".") -> Path | None:
    root_path = Path(root)
    pointer = root_path / LATEST_TERMINAL_POINTER
    if not pointer.exists():
        return None
    target = pointer.read_text(encoding="utf-8").strip()
    if not target:
        return None
    candidate = Path(target)
    return candidate if candidate.is_absolute() else root_path / candidate


def _last_structured_summary_block(text: str) -> str | None:
    header_index = text.rfind(STRUCTURED_SUMMARY_HEADER)
    if header_index < 0:
        return None
    start = text.rfind(SUMMARY_BOUNDARY, 0, header_index)
    if start < 0:
        start = header_index
    end = text.find(SUMMARY_BOUNDARY, header_index)
    if end < 0:
        return text[start:]
    return text[start : end + len(SUMMARY_BOUNDARY)]


def _summary_field(block: str, label: str) -> str:
    prefix = f"  {label}:"
    for line in block.splitlines():
        if line.startswith(prefix):
            return line.split(":", 1)[1].strip()
    return ""


def _summary_paragraph(block: str, section: str) -> str:
    lines = block.splitlines()
    for index, line in enumerate(lines):
        if line == section and index + 1 < len(lines) and lines[index + 1].startswith("  "):
            return lines[index + 1].strip()
    return ""


def parse_structured_summary(text: str) -> ParsedSummary:
    block = _last_structured_summary_block(text)
    if block is None:
        return ParsedSummary(found=False, valid=False)
    lines = block.splitlines()
    comm_header = next((line for line in lines if line.startswith(STRUCTURED_SUMMARY_HEADER)), "")
    marker_values = [line.replace("### RESULT:", "").replace("###", "").strip() for line in lines if line.startswith("### RESULT:")]
    result_marker = marker_values[0] if len(marker_values) == 1 else ""
    payload = SummaryPayload(
        comm_header=comm_header,
        slice=_summary_field(block, "NAME"),
        scope=_summary_field(block, "SCOPE"),
        branch=_summary_field(block, "BRANCH"),
        origin=_summary_field(block, "ORIGIN"),
        state_mode=_summary_field(block, "STATE_MODE"),
        mode_check=_summary_field(block, "MODE_CHECK"),
        work=_summary_field(block, "WORK"),
        evidence=_summary_field(block, "EVIDENCE"),
        overall=_summary_field(block, "OVERALL"),
        remote_evidence=_summary_field(block, "REMOTE_EVIDENCE"),
        pr=_summary_field(block, "PR"),
        head_sha=_summary_field(block, "HEAD_SHA"),
        ci=_summary_field(block, "CI"),
        merge=_summary_field(block, "MERGE"),
        terminal_log=_summary_field(block, "terminal_log"),
        terminal_log_remote=_summary_field(block, "terminal_log_remote"),
        terminal_log_local=_summary_field(block, "terminal_log_local"),
        command_report=_summary_field(block, "command_report"),
        interpretation=_summary_paragraph(block, "INTERPRETATION"),
        safe_step=_summary_field(block, "SAFE_STEP"),
        chat_reply=_summary_field(block, "CHAT_REPLY"),
    )
    findings = list(validate_summary_data(payload))
    if len(marker_values) != 1:
        findings.append(f"invalid result marker count: {len(marker_values)}")
    if payload.overall and result_marker and payload.overall != result_marker:
        findings.append("contradictory summary marker")
    for label, value in (
        ("BRANCH", payload.branch),
        ("ORIGIN", payload.origin),
        ("STATE_MODE", payload.state_mode),
        ("MODE_CHECK", payload.mode_check),
        ("terminal_log_remote", payload.terminal_log_remote),
        ("terminal_log_local", payload.terminal_log_local),
        ("SAFE_STEP", payload.safe_step),
    ):
        if not value:
            findings.append(f"missing summary field: {label}")
    if not payload.interpretation:
        findings.append("missing summary section: INTERPRETATION")
    return ParsedSummary(found=True, valid=not findings, payload=payload, result_marker=result_marker, findings=tuple(findings))


def _marker_verdict(text: str) -> tuple[EvidenceVerdict, str | None, int, int, bool]:
    pass_count = text.count(PASS_MARKER)
    fail_count = text.count(FAIL_MARKER)
    marker_positions = [(text.rfind(PASS_MARKER), PASS_MARKER), (text.rfind(FAIL_MARKER), FAIL_MARKER)]
    marker_positions = [(index, marker) for index, marker in marker_positions if index >= 0]
    if not marker_positions:
        return EvidenceVerdict.AMBIGUOUS_SUMMARY_REVIEW_REQUIRED, None, pass_count, fail_count, False
    final_index, final_marker = max(marker_positions, key=lambda item: item[0])
    hidden_fail = fail_count > 0 and final_marker == PASS_MARKER and text.find(FAIL_MARKER) < final_index
    if final_marker == FAIL_MARKER:
        verdict = EvidenceVerdict.FAIL_DIAGNOSE
    elif hidden_fail:
        verdict = EvidenceVerdict.AMBIGUOUS_SUMMARY_REVIEW_REQUIRED
    else:
        verdict = EvidenceVerdict.PASS_CONTINUE
    return verdict, final_marker, pass_count, fail_count, hidden_fail


def inspect_evidence(path: Path | str | None = None, *, root: Path | str = ".", require_summary: bool = False) -> EvidenceInspection:
    root_path = Path(root)
    evidence_path = Path(path) if path is not None else resolve_latest_evidence(root_path)
    branch_lines = _run_git(["branch", "--show-current"], root_path)
    status_lines = _run_git(["status", "--short"], root_path)
    branch = branch_lines[0] if branch_lines else "UNKNOWN"
    if evidence_path is None:
        return EvidenceInspection(path=None, exists=False, verdict=EvidenceVerdict.MISSING_EVIDENCE_UPLOAD_FIRST, require_summary=require_summary, git_branch=branch, git_status=status_lines)
    if not evidence_path.exists():
        return EvidenceInspection(path=evidence_path, exists=False, verdict=EvidenceVerdict.MISSING_EVIDENCE_UPLOAD_FIRST, require_summary=require_summary, git_branch=branch, git_status=status_lines)
    text = evidence_path.read_text(encoding="utf-8")
    summary = parse_structured_summary(text)
    marker_verdict, final_marker, pass_count, fail_count, hidden_fail = _marker_verdict(text)
    if summary.found:
        if not summary.valid:
            verdict = EvidenceVerdict.AMBIGUOUS_SUMMARY_REVIEW_REQUIRED
        elif summary.overall_pass:
            verdict = EvidenceVerdict.PASS_CONTINUE
        elif summary.overall_fail:
            verdict = EvidenceVerdict.FAIL_DIAGNOSE
        else:
            verdict = EvidenceVerdict.AMBIGUOUS_SUMMARY_REVIEW_REQUIRED
    elif require_summary:
        verdict = EvidenceVerdict.AMBIGUOUS_SUMMARY_REVIEW_REQUIRED
    else:
        verdict = marker_verdict
    return EvidenceInspection(path=evidence_path, exists=True, verdict=verdict, final_marker=final_marker, pass_markers=pass_count, fail_markers=fail_count, hidden_fail_before_final_pass=hidden_fail, structured_summary=summary, require_summary=require_summary, git_branch=branch, git_status=status_lines)


def render_evidence_inspection(result: EvidenceInspection) -> str:
    summary = result.structured_summary
    payload = summary.payload
    lines = [
        "EVIDENCE_INSPECTION",
        f"verdict: {result.verdict.value}",
        f"evidence_exists: {'yes' if result.exists else 'no'}",
        f"require_summary: {'yes' if result.require_summary else 'no'}",
        f"git_branch: {result.git_branch}",
        f"git_status_clean: {'yes' if not result.git_status else 'no'}",
        f"pass_markers: {result.pass_markers}",
        f"fail_markers: {result.fail_markers}",
        f"hidden_fail_before_final_pass: {'yes' if result.hidden_fail_before_final_pass else 'no'}",
        f"structured_summary_found: {'yes' if summary.found else 'no'}",
        f"structured_summary_valid: {'yes' if summary.valid else 'no'}",
    ]
    if result.require_summary and not summary.found:
        lines.append("summary_findings:")
        lines.append("- missing structured summary block")
    if summary.found:
        lines.extend([
            f"summary_name: {payload.slice or payload.slice_name}",
            f"summary_scope: {payload.scope}",
            f"summary_branch: {payload.branch}",
            f"summary_origin: {payload.origin}",
            f"summary_state_mode: {payload.state_mode}",
            f"summary_mode_check: {payload.mode_check}",
            f"summary_work: {payload.work}",
            f"summary_evidence: {payload.evidence}",
            f"summary_overall: {payload.overall}",
            f"summary_remote_evidence: {payload.remote_evidence}",
            f"summary_pr: {payload.pr}",
            f"summary_head_sha: {payload.head_sha}",
            f"summary_ci: {payload.ci}",
            f"summary_merge: {payload.merge}",
            f"summary_terminal_log: {payload.terminal_log}",
            f"summary_terminal_log_remote: {payload.terminal_log_remote}",
            f"summary_terminal_log_local: {payload.terminal_log_local}",
            f"summary_command_report: {payload.command_report}",
            f"summary_safe_step: {payload.safe_step}",
            f"summary_chat_reply: {summary.chat_reply}",
            f"summary_result_marker: {summary.result_marker}",
        ])
        if summary.findings:
            lines.append("summary_findings:")
            lines.extend(f"- {finding}" for finding in summary.findings)
    if result.path is not None:
        lines.append(f"evidence_path: {result.path}")
    if result.final_marker is not None:
        lines.append(f"final_marker: {result.final_marker}")
    if result.git_status:
        lines.append("git_status:")
        lines.extend(result.git_status)
    if result.verdict == EvidenceVerdict.PASS_CONTINUE:
        lines.append("next_action: continue with the next safe slice after reviewing evidence")
    elif result.verdict == EvidenceVerdict.FAIL_DIAGNOSE:
        lines.append("next_action: diagnose the failing evidence before continuing")
    elif result.verdict == EvidenceVerdict.MISSING_EVIDENCE_UPLOAD_FIRST:
        lines.append("next_action: locate remote or repo evidence, or run an evidence upload slice before requesting pasted output")
    else:
        lines.append("next_action: review ambiguous evidence manually before continuing")
    lines.append(f"### RESULT: {'PASS' if result.success else 'FAIL'} ###")
    return "\n".join(lines)
