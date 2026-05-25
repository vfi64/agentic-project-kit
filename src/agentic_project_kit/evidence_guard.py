from __future__ import annotations

import fnmatch
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
    "Traceback (most recent call last):",
    "ModuleNotFoundError:",
    "ERROR collecting",
)

EXPECTED_NEGATIVE_SMOKE_START = "### EXPECTED NEGATIVE SMOKE START ###"
EXPECTED_NEGATIVE_SMOKE_DONE = "### EXPECTED NEGATIVE SMOKE DONE ###"
EXPECTED_NEGATIVE_SMOKE_MARKERS = (
    "PASS: false-pass log was rejected",
    "PASS: ns evidence-guard rejected false-PASS log",
)

EVIDENCE_LOG_PATTERNS = ("docs/reports/terminal/*.log",)

@dataclass(frozen=True)
class EvidenceGuardResult:
    ok: bool
    path: Path
    final_result: str
    findings: tuple[str, ...]

@dataclass(frozen=True)
class ChangeScopeGuardResult:
    ok: bool
    changed_paths: tuple[str, ...]
    expected_paths: tuple[str, ...]
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

def _is_expected_negative_smoke_log(text: str) -> bool:
    if EXPECTED_NEGATIVE_SMOKE_START not in text or EXPECTED_NEGATIVE_SMOKE_DONE not in text:
        return False
    if text.count(EXPECTED_NEGATIVE_SMOKE_START) != text.count(EXPECTED_NEGATIVE_SMOKE_DONE):
        return False
    return any(marker in text for marker in EXPECTED_NEGATIVE_SMOKE_MARKERS)

def _has_unscoped_expected_negative_smoke_marker(text: str) -> bool:
    has_marker = any(marker in text for marker in EXPECTED_NEGATIVE_SMOKE_MARKERS)
    if not has_marker:
        return False
    return EXPECTED_NEGATIVE_SMOKE_START not in text or EXPECTED_NEGATIVE_SMOKE_DONE not in text

def _normalize_paths(paths: list[str] | tuple[str, ...]) -> tuple[str, ...]:
    return tuple(path.strip() for path in paths if path.strip())

def _is_evidence_log_path(path: str, patterns: tuple[str, ...]) -> bool:
    return any(fnmatch.fnmatch(path, pattern) for pattern in patterns)

def check_change_scope(
    *,
    changed_paths: list[str] | tuple[str, ...],
    expected_paths: list[str] | tuple[str, ...],
    evidence_log_patterns: tuple[str, ...] = EVIDENCE_LOG_PATTERNS,
) -> ChangeScopeGuardResult:
    changed = _normalize_paths(changed_paths)
    expected = _normalize_paths(expected_paths)
    findings: list[str] = []
    if not changed:
        findings.append("changed_paths must list at least one changed path")
    missing = tuple(path for path in expected if path not in changed)
    if missing:
        findings.append("expected changed paths missing: " + ", ".join(missing))
    if expected and changed:
        non_evidence = tuple(path for path in changed if not _is_evidence_log_path(path, evidence_log_patterns))
        if not non_evidence:
            findings.append("expected target changes, but changed paths are evidence logs only")
    return ChangeScopeGuardResult(
        ok=not findings,
        changed_paths=changed,
        expected_paths=expected,
        findings=tuple(findings),
    )

def check_terminal_log(path: Path) -> EvidenceGuardResult:
    text = path.read_text(encoding="utf-8")
    final_result = last_result_marker(text)
    findings: list[str] = []
    fail_hits = [marker for marker in FAIL_MARKERS if marker in text]
    if final_result == "UNKNOWN":
        findings.append("missing final result marker")
    if _has_unscoped_expected_negative_smoke_marker(text):
        findings.append("expected negative smoke markers must be scoped with START/DONE markers")
    if final_result == "PASS" and fail_hits and not _is_expected_negative_smoke_log(text):
        findings.append("final PASS conflicts with earlier failure markers: " + ", ".join(fail_hits))
    return EvidenceGuardResult(ok=not findings, path=path, final_result=final_result, findings=tuple(findings))
