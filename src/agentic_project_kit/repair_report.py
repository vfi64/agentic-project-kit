from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

RepairOperationStatus = Literal["applied", "planned", "failed"]


@dataclass(frozen=True)
class RepairOperation:
    kind: str
    status: RepairOperationStatus
    target: str
    message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"kind": self.kind, "status": self.status, "target": self.target}
        if self.message is not None:
            payload["message"] = self.message
        return payload


@dataclass(frozen=True)
class SkippedRepairOperation:
    kind: str
    target: str
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {"kind": self.kind, "target": self.target, "reason": self.reason}


@dataclass(frozen=True)
class FinalValidation:
    ok: bool
    findings: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"ok": self.ok, "findings": self.findings}


@dataclass(frozen=True)
class RepairReport:
    ok: bool
    repair_attempted: bool
    original_findings: list[dict[str, Any]] = field(default_factory=list)
    operations: list[RepairOperation] = field(default_factory=list)
    skipped_operations: list[SkippedRepairOperation] = field(default_factory=list)
    final_validation: FinalValidation = field(default_factory=lambda: FinalValidation(ok=True))

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "repair_attempted": self.repair_attempted,
            "original_findings": self.original_findings,
            "operations": [operation.to_dict() for operation in self.operations],
            "skipped_operations": [operation.to_dict() for operation in self.skipped_operations],
            "final_validation": self.final_validation.to_dict(),
        }


def repair_report_from_validation(
    *,
    original_findings: list[dict[str, Any]],
    final_ok: bool,
    final_findings: list[dict[str, Any]] | None = None,
    operations: list[RepairOperation] | None = None,
    skipped_operations: list[SkippedRepairOperation] | None = None,
) -> RepairReport:
    effective_operations = operations or []
    effective_skipped_operations = skipped_operations or []
    return RepairReport(
        ok=final_ok,
        repair_attempted=bool(effective_operations or effective_skipped_operations),
        original_findings=original_findings,
        operations=effective_operations,
        skipped_operations=effective_skipped_operations,
        final_validation=FinalValidation(ok=final_ok, findings=final_findings or []),
    )
