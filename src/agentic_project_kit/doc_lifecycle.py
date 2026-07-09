from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
from typing import Any

from agentic_project_kit.documentation_registry import build_documentation_registry_summary

ALLOWED_STATUS_VALUES = {
    "idea-note",
    "proposed",
    "active",
    "accepted",
    "implemented",
    "rejected",
    "superseded",
    "archived",
}

LIFECYCLE_DIRS = (
    "docs/ideas",
    "docs/planning",
    "docs/roadmap",
    "docs/strategy",
)


@dataclass(frozen=True)
class DocLifecycleDocument:
    path: str
    status: str | None
    decision_status: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "status": self.status,
            "decision_status": self.decision_status,
        }


@dataclass(frozen=True)
class DocLifecycleFinding:
    code: str
    path: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return {
            "code": self.code,
            "path": self.path,
            "message": self.message,
        }


@dataclass(frozen=True)
class DocLifecycleReport:
    documents: tuple[DocLifecycleDocument, ...]
    findings: tuple[DocLifecycleFinding, ...]
    registry_summary: dict[str, Any] | None = None

    @property
    def ok(self) -> bool:
        return not self.findings

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "documents": [document.to_dict() for document in self.documents],
            "findings": [finding.to_dict() for finding in self.findings],
            "registry_summary": self.registry_summary,
        }


def build_doc_lifecycle_report(project_root: Path) -> DocLifecycleReport:
    documents: list[DocLifecycleDocument] = []
    findings: list[DocLifecycleFinding] = []
    for relative_path in _iter_lifecycle_markdown_files(project_root):
        text = (project_root / relative_path).read_text(encoding="utf-8")
        status = _first_header_value(text, "Status")
        decision_status = _first_header_value(text, "Decision status")
        documents.append(DocLifecycleDocument(str(relative_path), status, decision_status))
        findings.extend(_audit_document(relative_path, text, status, decision_status))
    return DocLifecycleReport(
        documents=tuple(documents),
        findings=tuple(findings),
        registry_summary=_load_registry_summary(project_root),
    )


def write_doc_lifecycle_json_report(report: DocLifecycleReport, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def render_doc_lifecycle_report(report: DocLifecycleReport) -> str:
    lines = ["Documentation lifecycle audit", "", "Documents:"]
    if not report.documents:
        lines.append("- none")
    for document in report.documents:
        status = document.status if document.status is not None else "MISSING"
        lines.append(f"- {document.path}: {status}")
    if report.registry_summary is not None:
        lines.extend([
            "",
            "Documentation registry:",
            f"- registry: {report.registry_summary['registry_path']}",
            f"- version: {report.registry_summary['version']}",
            f"- documents: {report.registry_summary['document_count']}",
            "- broad_migration_allowed: "
            f"{report.registry_summary['broad_migration_allowed']}",
        ])
        class_counts = report.registry_summary.get("class_counts", {})
        if isinstance(class_counts, dict):
            for class_name, count in class_counts.items():
                lines.append(f"- class:{class_name}: {count}")
    if report.findings:
        lines.extend(["", "Findings:"])
        for finding in report.findings:
            lines.append(f"- [{finding.code}] {finding.path}: {finding.message}")
    lines.extend(["", f"Overall: {'PASS' if report.ok else 'FAIL'}"])
    return "\n".join(lines)


def _load_registry_summary(project_root: Path) -> dict[str, Any] | None:
    try:
        return build_documentation_registry_summary(project_root)
    except (OSError, ValueError):
        return None


def _iter_lifecycle_markdown_files(project_root: Path) -> tuple[Path, ...]:
    paths: list[Path] = []
    for directory in LIFECYCLE_DIRS:
        root = project_root / directory
        if not root.exists():
            continue
        paths.extend(path.relative_to(project_root) for path in root.rglob("*.md") if path.is_file())
    return tuple(sorted(paths))


def _audit_document(
    path: Path,
    text: str,
    status: str | None,
    decision_status: str | None,
) -> list[DocLifecycleFinding]:
    findings: list[DocLifecycleFinding] = []
    path_text = str(path)
    if status is None:
        findings.append(DocLifecycleFinding("missing-status", path_text, "document is missing a Status header"))
    elif status not in ALLOWED_STATUS_VALUES:
        findings.append(
            DocLifecycleFinding(
                "invalid-status",
                path_text,
                "status must be one of: " + ", ".join(sorted(ALLOWED_STATUS_VALUES)) + f"; found {status!r}",
            )
        )
    if decision_status is None:
        findings.append(DocLifecycleFinding("missing-decision-status", path_text, "document is missing a Decision status header"))
    if status in {"idea-note", "active"} and "Review policy:" not in text:
        findings.append(DocLifecycleFinding("missing-review-policy", path_text, "active and idea documents need a Review policy"))
    if status in {"implemented", "superseded", "archived", "rejected"} and "Lifecycle note:" not in text:
        findings.append(DocLifecycleFinding("missing-lifecycle-note", path_text, "closed lifecycle documents need a Lifecycle note"))
    return findings


def _first_header_value(text: str, key: str) -> str | None:
    prefix = f"{key}:"
    for line in text.splitlines():
        if line.startswith(prefix):
            value = line[len(prefix):].strip()
            return value or None
    return None


def build_doc_lifecycle_triage_payload(project_root: Path) -> dict[str, Any]:
    """Build a safe dry-run lifecycle triage report.

    The triage layer is intentionally advisory. Missing lifecycle metadata is
    WARN-only. Objective event conflicts, such as an invalid Status header, are
    blocking because they make downstream lifecycle decisions unsafe.
    """
    report = build_doc_lifecycle_report(project_root)
    findings: list[dict[str, str]] = []
    proposed_actions: list[dict[str, str]] = []
    failures = 0
    warnings = 0

    for finding in report.findings:
        severity = "FAIL" if finding.code == "invalid-status" else "WARN"
        if severity == "FAIL":
            failures += 1
        else:
            warnings += 1
        findings.append(
            {
                "severity": severity,
                "code": finding.code,
                "path": finding.path,
                "message": finding.message,
            }
        )
        proposed_actions.append(
            {
                "id": finding.path + ":" + finding.code,
                "path": finding.path,
                "operation": "manual-review" if severity == "FAIL" else "defer",
                "reason": finding.message,
                "execute": "false",
            }
        )

    finding_paths = {finding["path"] for finding in findings}
    for document in report.documents:
        if document.path in finding_paths:
            continue
        operation = _triage_operation_for_status(document.status)
        proposed_actions.append(
            {
                "id": document.path + ":" + operation,
                "path": document.path,
                "operation": operation,
                "reason": _triage_reason_for_status(document.status),
                "execute": "false",
            }
        )

    return {
        "schema_version": 1,
        "kind": "doc_lifecycle_triage_report",
        "mode": "dry-run",
        "auto_apply": False,
        "result_status": "BLOCK" if failures else "PASS",
        "summary": {
            "documents": len(report.documents),
            "findings": len(findings),
            "warnings": warnings,
            "failures": failures,
            "proposed_actions": len(proposed_actions),
        },
        "documents": [document.to_dict() for document in report.documents],
        "findings": findings,
        "proposed_actions": proposed_actions,
        "registry_summary": report.registry_summary,
    }


def render_doc_lifecycle_triage_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "DOC_LIFECYCLE_TRIAGE",
        f"STATUS: {payload['result_status']}",
        f"MODE: {payload['mode']}",
        "AUTO_APPLY: disabled",
        f"DOCUMENTS: {summary['documents']}",
        f"FINDINGS: {summary['findings']}",
        f"WARNINGS: {summary['warnings']}",
        f"FAILURES: {summary['failures']}",
        "",
        "PROPOSED_ACTIONS:",
    ]
    actions = payload.get("proposed_actions", [])
    if not actions:
        lines.append("- none")
    for action in actions:
        lines.append(
            "- "
            f"{action['operation']} | {action['path']} | "
            f"{action['reason']} | execute={action['execute']}"
        )
    return "\n".join(lines) + "\n"


def _triage_operation_for_status(status: str | None) -> str:
    if status in {"active", "accepted", "implemented"}:
        return "confirm-current"
    if status in {"superseded", "archived", "rejected"}:
        return "historical"
    if status == "idea-note":
        return "defer"
    return "manual-review"


def _triage_reason_for_status(status: str | None) -> str:
    if status in {"active", "accepted", "implemented"}:
        return "registered lifecycle metadata indicates current document"
    if status in {"superseded", "archived", "rejected"}:
        return "registered lifecycle metadata indicates historical document"
    if status == "idea-note":
        return "idea document remains advisory"
    return "status requires manual review"
