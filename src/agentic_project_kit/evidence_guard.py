from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

FAIL_MARKERS = (
    "### RESULT: FAIL ###",
    "WORK RESULT: FAIL",
    "OVERALL RESULT: FAIL",
    "FAIL: targeted tests failed",
    "FAIL: ./ns dev failed",
    "FAIL: gates failed",
    "FAIL: repair did not pass gates",
    "FAILED tests/",
    "short test summary info",
)

@dataclass(frozen=True)
class EvidenceGuardResult:
    ok: bool
    path: Path
    final_result: str
    findings: tuple[str, ...]

def last_result_marker(text: str) -> str:
    result = "UNKNOWN"
    for line in text.splitlines():
        stripped = line.strip()
        if stripped == "### RESULT: PASS ###":
            result = "PASS"
        elif stripped == "### RESULT: FAIL ###":
            result = "FAIL"
        elif stripped == "### RESULT: PENDING ###":
            result = "PENDING"
        elif stripped == "### RESULT: HARD-FAIL ###":
            result = "HARD-FAIL"
    return result

def check_terminal_log(path: Path) -> EvidenceGuardResult:
    text = path.read_text(encoding="utf-8")
    final_result = last_result_marker(text)
    findings: list[str] = []
    fail_hits = [marker for marker in FAIL_MARKERS if marker in text]
    if final_result == "UNKNOWN":
        findings.append("missing final result marker")
    if final_result == "PASS" and fail_hits:
        findings.append("final PASS conflicts with earlier failure markers: " + ", ".join(fail_hits))
    return EvidenceGuardResult(
        ok=not findings,
        path=path,
        final_result=final_result,
        findings=tuple(findings),
    )
