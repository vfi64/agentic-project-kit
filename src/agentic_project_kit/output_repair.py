"""Minimal deterministic output repair primitives.

This module only performs bounded structural repair for literal required section
markers. It does not invent semantic content and does not call a model.
"""

from __future__ import annotations

from dataclasses import dataclass

from agentic_project_kit.output_contract import OutputContract, validate_output_against_contract
from agentic_project_kit.repair_report import RepairOperation, RepairReport, repair_report_from_validation


@dataclass(frozen=True)
class OutputRepairResult:
    text: str
    report: RepairReport


def missing_required_sections(text: str, contract: OutputContract) -> tuple[str, ...]:
    """Return required literal section markers that are absent from text."""
    return tuple(section for section in contract.required_sections if section not in text)


def append_missing_required_sections(text: str, contract: OutputContract) -> OutputRepairResult:
    """Append missing required section markers with explicit empty placeholders.

    This is intentionally structural only. The placeholder makes the repair visible
    and avoids pretending that semantic content was generated.
    """
    original_validation = validate_output_against_contract(text, contract)
    original_findings = original_validation.to_dict()["findings"]
    missing_sections = missing_required_sections(text, contract)
    if not missing_sections:
        report = repair_report_from_validation(
            original_findings=original_findings,
            final_ok=original_validation.ok,
            final_findings=original_findings,
        )
        return OutputRepairResult(text=text, report=report)
    repaired = text.rstrip()
    operations: list[RepairOperation] = []
    for section in missing_sections:
        repaired = f"{repaired}\n\n{section}\nTODO: fill this section."
        operations.append(
            RepairOperation(
                kind="append_missing_required_section",
                status="applied",
                target=section,
                message="Appended missing required section marker with explicit placeholder.",
            )
        )
    final_validation = validate_output_against_contract(repaired, contract)
    report = repair_report_from_validation(
        original_findings=original_findings,
        final_ok=final_validation.ok,
        final_findings=final_validation.to_dict()["findings"],
        operations=operations,
    )
    return OutputRepairResult(text=repaired, report=report)
