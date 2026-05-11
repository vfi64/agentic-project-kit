"""Runtime validation primitives for generated governance artifacts.

This module intentionally starts small: it provides deterministic, auditable
validation results without performing repair or invoking any model.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class ValidationSeverity(str, Enum):
    """Severity for runtime validation findings."""

    ERROR = "error"
    WARNING = "warning"


@dataclass(frozen=True)
class ValidationFinding:
    """Single validation finding with stable machine-readable fields."""

    code: str
    message: str
    severity: ValidationSeverity = ValidationSeverity.ERROR


@dataclass(frozen=True)
class ValidationReport:
    findings: tuple[ValidationFinding, ...] = ()

    @property
    def ok(self) -> bool:
        return not any(finding.severity is ValidationSeverity.ERROR for finding in self.findings)

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic JSON-safe representation."""
        return {
            "ok": self.ok,
            "findings": [
                {
                    "severity": finding.severity.value,
                    "code": finding.code,
                    "message": finding.message,
                }
                for finding in self.findings
            ],
        }

def validate_required_sections(text: str, required_sections: tuple[str, ...]) -> ValidationReport:
    """Validate that required section markers are present in text.

    The check is intentionally literal and deterministic. This makes it suitable
    as a first runtime skeleton for generated output contracts and governance
    wrapper artifacts.
    """
    findings: list[ValidationFinding] = []
    for section in required_sections:
        if section not in text:
            findings.append(
                ValidationFinding(
                    code="missing_required_section",
                    message=f"Missing required section: {section}",
                )
            )
    return ValidationReport(findings=tuple(findings))
