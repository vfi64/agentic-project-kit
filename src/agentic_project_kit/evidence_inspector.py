from __future__ import annotations

import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

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
    work: str = ""
    evidence: str = ""
    overall: str = ""
    remote_evidence: str = ""
    terminal_log: str = ""
    terminal_log_remote: str = ""
    command_report: str = ""
    chat_reply: str = ""
    result_marker: str = ""
    findings: tuple[str, ...] = ()

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


def parse_structured_summary(text: str) -> ParsedSummary:
    block = _last_structured_summary_block(text)
    if block is None:
        return ParsedSummary(found=False, valid=False)
    marker_values = [
        line.replace("### RESULT:", "").replace("###", "").strip()
        for line in block.splitlines()
        if line.startswith("### RESULT:")
    ]
    work = _summary_field(block, "WORK")
    evidence = _summary_field(block, "EVIDENCE")
    overall = _summary_field(block, "OVERALL")
    remote_evidence = _summary_field(block, "REMOTE_EVIDENCE")
    terminal_log = _summary_field(block, "terminal_log")
    terminal_log_remote = _summary_field(block, "terminal_log_remote")
    command_report = _summary_field(block, "command_report")
    chat_reply = _summary_field(block, "CHAT_REPLY")
    findings: list[str] = []
    if len(marker_values) != 1:
        findings.append(f"invalid result marker count: {len(marker_values)}")
    result_marker = marker_values[0] if len(marker_values) == 1 else ""
    for name, value in (
        ("WORK", work),
        ("EVIDENCE", evidence),
        ("OVERALL", overall),
        ("REMOTE_EVIDENCE", remote_evidence),
        ("terminal_log", terminal_log),
        ("CHAT_REPLY", chat_reply),
    ):
        if not value:
            findings.append(f"missing summary field: {name}")
    if overall and result_marker and overall != result_marker:
        findings.append("contradictory summary marker")
    if overall == "PASS" and work != "PASS":
        findings.append("invalid pass: work is not PASS")
    if overall == "PASS" and evidence in {"FAIL", "PARTIAL", "CHAT_ONLY"}:
        findings.append("invalid pass: evidence is not complete")
    if overall == "PASS" and remote_evidence not in {"PASS", "NOT_REQUIRED"}:
        findings.append("invalid pass: remote evidence is not complete")
    if overall == "PASS" and chat_reply != "d":
        findings.append("invalid pass: chat_reply must be d")
    if overall in {"FAIL", "HARD-FAIL"} and chat_reply == "d":
        findings.append("invalid failure: chat_reply must not be d")
    return ParsedSummary(
        found=True,
        valid=not findings,
        work=work,
        evidence=evidence,
        overall=overall,
        remote_evidence=remote_evidence,
        terminal_log=terminal_log,
        terminal_log_remote=terminal_log_remote,
        command_report=command_report,
        chat_reply=chat_reply,
        result_marker=result_marker,
        findings=tuple(findings),
    )


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


def inspect_evidence(path: Path | str | None = None, *, root: Path | str = ".") -> EvidenceInspection:
    root_path = Path(root)
    evidence_path = Path(path) if path is not None else resolve_latest_evidence(root_path)
    branch_lines = _run_git(["branch", "--show-current"], root_path)
    status_lines = _run_git(["status", "--short"], root_path)
    branch = branch_lines[0] if branch_lines else "UNKNOWN"
    if evidence_path is None:
        return EvidenceInspection(
            path=None,
            exists=False,
            verdict=EvidenceVerdict.MISSING_EVIDENCE_UPLOAD_FIRST,
            git_branch=branch,
            git_status=status_lines,
        )
    if not evidence_path.exists():
        return EvidenceInspection(
            path=evidence_path,
            exists=False,
            verdict=EvidenceVerdict.MISSING_EVIDENCE_UPLOAD_FIRST,
            git_branch=branch,
            git_status=status_lines,
        )
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
    else:
        verdict = marker_verdict
    return EvidenceInspection(
        path=evidence_path,
        exists=True,
        verdict=verdict,
        final_marker=final_marker,
        pass_markers=pass_count,
        fail_markers=fail_count,
        hidden_fail_before_final_pass=hidden_fail,
        structured_summary=summary,
        git_branch=branch,
        git_status=status_lines,
    )


def render_evidence_inspection(result: EvidenceInspection) -> str:
    summary = result.structured_summary
    lines = [
        "EVIDENCE_INSPECTION",
        f"verdict: {result.verdict.value}",
        f"evidence_exists: {'yes' if result.exists else 'no'}",
        f"git_branch: {result.git_branch}",
        f"git_status_clean: {'yes' if not result.git_status else 'no'}",
        f"pass_markers: {result.pass_markers}",
        f"fail_markers: {result.fail_markers}",
        f"hidden_fail_before_final_pass: {'yes' if result.hidden_fail_before_final_pass else 'no'}",
        f"structured_summary_found: {'yes' if summary.found else 'no'}",
        f"structured_summary_valid: {'yes' if summary.valid else 'no'}",
    ]
    if summary.found:
        lines.extend(
            [
                f"summary_work: {summary.work}",
                f"summary_evidence: {summary.evidence}",
                f"summary_overall: {summary.overall}",
                f"summary_remote_evidence: {summary.remote_evidence}",
                f"summary_chat_reply: {summary.chat_reply}",
                f"summary_result_marker: {summary.result_marker}",
            ]
        )
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
