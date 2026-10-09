"""Shared result types for Kit and external-workspace documentation audits."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class DocumentationAuditDimension:
    name: str
    ok: bool
    findings: tuple[str, ...]
    warnings: tuple[str, ...] = ()
    review_only: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "ok": self.ok, "review_only": self.review_only,
                "findings": list(self.findings), "warnings": list(self.warnings)}


@dataclass(frozen=True)
class DocumentationSystemAuditReport:
    dimensions: tuple[DocumentationAuditDimension, ...]
    scope: str = "kit"

    @property
    def ok(self) -> bool:
        return all(d.ok for d in self.dimensions if not d.review_only)

    def to_dict(self) -> dict[str, Any]:
        return {"ok": self.ok, "result_status": "PASS" if self.ok else "BLOCKED",
                "scope": self.scope, "dimensions": [d.to_dict() for d in self.dimensions]}
