from __future__ import annotations

import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

PASS_MARKER = "### RESULT: PASS ###"
FAIL_MARKER = "### RESULT: FAIL ###"
LATEST_TERMINAL_POINTER = Path("docs/reports/terminal/LATEST_TERMINAL_LOG.txt")


class EvidenceVerdict(str, Enum):
    PASS_CONTINUE = "PASS_CONTINUE"
    FAIL_DIAGNOSE = "FAIL_DIAGNOSE"
    MISSING_EVIDENCE_UPLOAD_FIRST = "MISSING_EVIDENCE_UPLOAD_FIRST"
    AMBIGUOUS_SUMMARY_REVIEW_REQUIRED = "AMBIGUOUS_SUMMARY_REVIEW_REQUIRED"


@dataclass(frozen=True)
class EvidenceInspection:
    path: Path | None
    exists: bool
    verdict: EvidenceVerdict
    final_marker: str | None = None
    pass_markers: int = 0
    fail_markers: int = 0
    hidden_fail_before_final_pass: bool = False
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
    pass_count = text.count(PASS_MARKER)
    fail_count = text.count(FAIL_MARKER)
    marker_positions = [(text.rfind(PASS_MARKER), PASS_MARKER), (text.rfind(FAIL_MARKER), FAIL_MARKER)]
    marker_positions = [(index, marker) for index, marker in marker_positions if index >= 0]
    if not marker_positions:
        verdict = EvidenceVerdict.AMBIGUOUS_SUMMARY_REVIEW_REQUIRED
        final_marker = None
    else:
        final_index, final_marker = max(marker_positions, key=lambda item: item[0])
        hidden_fail = fail_count > 0 and final_marker == PASS_MARKER and text.find(FAIL_MARKER) < final_index
        if final_marker == FAIL_MARKER:
            verdict = EvidenceVerdict.FAIL_DIAGNOSE
        elif hidden_fail:
            verdict = EvidenceVerdict.AMBIGUOUS_SUMMARY_REVIEW_REQUIRED
        else:
            verdict = EvidenceVerdict.PASS_CONTINUE
    return EvidenceInspection(
        path=evidence_path,
        exists=True,
        verdict=verdict,
        final_marker=final_marker,
        pass_markers=pass_count,
        fail_markers=fail_count,
        hidden_fail_before_final_pass=fail_count > 0 and final_marker == PASS_MARKER if marker_positions else False,
        git_branch=branch,
        git_status=status_lines,
    )


def render_evidence_inspection(result: EvidenceInspection) -> str:
    lines = [
        "EVIDENCE_INSPECTION",
        f"verdict: {result.verdict.value}",
        f"evidence_exists: {'yes' if result.exists else 'no'}",
        f"git_branch: {result.git_branch}",
        f"git_status_clean: {'yes' if not result.git_status else 'no'}",
        f"pass_markers: {result.pass_markers}",
        f"fail_markers: {result.fail_markers}",
        f"hidden_fail_before_final_pass: {'yes' if result.hidden_fail_before_final_pass else 'no'}",
    ]
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
