from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
from typing import Any

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

    @property
    def ok(self) -> bool:
        return not self.findings

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "documents": [document.to_dict() for document in self.documents],
            "findings": [finding.to_dict() for finding in self.findings],
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
    return DocLifecycleReport(tuple(documents), tuple(findings))


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
    if report.findings:
        lines.extend(["", "Findings:"])
        for finding in report.findings:
            lines.append(f"- [{finding.code}] {finding.path}: {finding.message}")
    lines.extend(["", f"Overall: {'PASS' if report.ok else 'FAIL'}"])
    return "\n".join(lines)


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
