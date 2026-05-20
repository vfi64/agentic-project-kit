from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from agentic_project_kit.evidence_guard import check_terminal_log

SUPPORTED_EVIDENCE_TYPES = {"terminal_log"}
SUPPORTED_FINAL_RESULTS = {"PASS", "FAIL", "PENDING", "HARD-FAIL"}

@dataclass(frozen=True)
class TypedWorkOrderEvidenceResult:
    ok: bool
    status: str
    evidence_type: str | None
    path: Path | None
    findings: tuple[str, ...]

def validate_typed_work_order_evidence(work_order: dict[str, Any], *, repo_root: Path = Path(".")) -> TypedWorkOrderEvidenceResult:
    evidence = work_order.get("evidence")
    if evidence is None:
        return TypedWorkOrderEvidenceResult(True, "NO_EVIDENCE_DECLARED", None, None, ())
    if not isinstance(evidence, dict):
        return TypedWorkOrderEvidenceResult(False, "INVALID_EVIDENCE", None, None, ("evidence must be a mapping",))

    evidence_type = evidence.get("type")
    raw_path = evidence.get("path")
    guard_required = bool(evidence.get("guard_required", False))
    expected_final_result = evidence.get("expected_final_result")
    on_guard_fail = evidence.get("on_guard_fail", "FAIL")

    findings: list[str] = []
    if evidence_type not in SUPPORTED_EVIDENCE_TYPES:
        findings.append(f"unsupported evidence type: {evidence_type!r}")
    if not isinstance(raw_path, str) or not raw_path:
        findings.append("evidence.path must be a non-empty repo-relative string")
    if expected_final_result not in SUPPORTED_FINAL_RESULTS:
        findings.append(f"unsupported expected_final_result: {expected_final_result!r}")
    if on_guard_fail != "FAIL":
        findings.append(f"unsupported on_guard_fail: {on_guard_fail!r}")

    if findings:
        return TypedWorkOrderEvidenceResult(False, "INVALID_EVIDENCE", evidence_type if isinstance(evidence_type, str) else None, None, tuple(findings))

    evidence_path = repo_root / raw_path
    if not evidence_path.exists():
        return TypedWorkOrderEvidenceResult(False, "MISSING_EVIDENCE", evidence_type, evidence_path, (f"evidence path does not exist: {raw_path}",))

    if guard_required:
        guard_result = check_terminal_log(evidence_path)
        if not guard_result.ok:
            return TypedWorkOrderEvidenceResult(False, "GUARD_FAILED", evidence_type, evidence_path, guard_result.findings)
        if guard_result.final_result != expected_final_result:
            return TypedWorkOrderEvidenceResult(False, "UNEXPECTED_FINAL_RESULT", evidence_type, evidence_path, (f"expected {expected_final_result}, got {guard_result.final_result}",))
        return TypedWorkOrderEvidenceResult(True, "EVIDENCE_ACCEPTED", evidence_type, evidence_path, ())

    return TypedWorkOrderEvidenceResult(True, "EVIDENCE_DECLARED_NOT_GUARDED", evidence_type, evidence_path, ())
