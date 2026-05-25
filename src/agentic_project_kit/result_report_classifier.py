from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from agentic_project_kit.pass_already_done import CompletionClassification
from agentic_project_kit.pass_already_done import classify_completion
from agentic_project_kit.pass_already_done import render_classification


@dataclass(frozen=True)
class ReportClassification:
    report_path: Path
    raw_exit_code: int
    target_verified: bool
    classification: CompletionClassification

    @property
    def success(self) -> bool:
        return self.classification.success


def classify_report(path: Path, *, raw_exit_code: int, target_verified: bool = False) -> ReportClassification:
    text = path.read_text(encoding="utf-8")
    classification = classify_completion(
        exit_code=raw_exit_code,
        output=text,
        target_verified=target_verified,
    )
    return ReportClassification(
        report_path=path,
        raw_exit_code=raw_exit_code,
        target_verified=target_verified,
        classification=classification,
    )


def render_report_classification(result: ReportClassification) -> str:
    lines = [
        "WORKFLOW_REPORT_CLASSIFICATION",
        f"report_path: {result.report_path}",
        f"raw_exit_code: {result.raw_exit_code}",
        f"target_verified: {'yes' if result.target_verified else 'no'}",
        f"effective_success: {'yes' if result.success else 'no'}",
        render_classification(result.classification),
    ]
    return "\n".join(lines)
