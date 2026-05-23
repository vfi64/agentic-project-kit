from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import re
from typing import Any

import yaml

from agentic_project_kit.checks import check_docs
from agentic_project_kit.doc_lifecycle import build_doc_lifecycle_report
from agentic_project_kit.doc_mesh import build_doc_mesh_report


MANDATORY_ORDER = (
    ".agentic/compiled_agent_context.yaml",
    "docs/governance/FINAL_SUMMARY_CONTRACT.md",
    "docs/governance/CHAT_COMMUNICATION_CONTRACT.md",
    "docs/governance/PORTABLE_CHAT_EXECUTION_CONTRACT.md",
    "docs/governance/CHAT_BOOTSTRAP_AND_DRIFT_CONTRACT.md",
    "docs/TEST_GATES.md",
    "docs/STATUS.md",
    "docs/handoff/CURRENT_HANDOFF.md",
)

STATUS_HEADROOM_WORD_LIMIT = 3450

REQUIRED_DOCS = (
    "README.md",
    "AGENTS.md",
    "docs/STATUS.md",
    "docs/TEST_GATES.md",
    "docs/handoff/CURRENT_HANDOFF.md",
    "docs/DOCUMENTATION_COVERAGE.yaml",
    "docs/DOCUMENTATION_REGISTRY.yaml",
    "sentinel.yaml",
    ".agentic/compiled_agent_context.yaml",
    "docs/governance/FINAL_SUMMARY_CONTRACT.md",
    "docs/governance/CHAT_COMMUNICATION_CONTRACT.md",
    "docs/governance/PORTABLE_CHAT_EXECUTION_CONTRACT.md",
    "docs/governance/CHAT_BOOTSTRAP_AND_DRIFT_CONTRACT.md",
    "docs/governance/DOCUMENTATION_REGISTRY_CONTRACT.md",
    "docs/architecture/ARCHITECTURE_CONTRACT.md",
    "docs/architecture/DOCUMENTATION_INFORMATION_ARCHITECTURE.md",
)


@dataclass(frozen=True)
class DocumentationAuditDimension:
    name: str
    ok: bool
    findings: tuple[str, ...]
    review_only: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "ok": self.ok,
            "review_only": self.review_only,
            "findings": list(self.findings),
        }


@dataclass(frozen=True)
class DocumentationSystemAuditReport:
    dimensions: tuple[DocumentationAuditDimension, ...]

    @property
    def ok(self) -> bool:
        return all(dimension.ok for dimension in self.dimensions if not dimension.review_only)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "dimensions": [dimension.to_dict() for dimension in self.dimensions],
        }


def build_documentation_system_audit(project_root: Path) -> DocumentationSystemAuditReport:
    project_root = project_root.resolve()
    check_doc_errors = tuple(check_docs(project_root))
    mesh_report = build_doc_mesh_report(project_root)
    lifecycle_report = build_doc_lifecycle_report(project_root)
    dimensions = (
        _freshness_dimension(project_root, mesh_report),
        _completeness_dimension(project_root, check_doc_errors),
        _correctness_dimension(check_doc_errors, mesh_report, lifecycle_report),
        _redundancy_dimension(project_root),
        _document_order_dimension(project_root),
        _consistency_dimension(mesh_report, lifecycle_report),
    )
    return DocumentationSystemAuditReport(dimensions=dimensions)


def render_documentation_system_audit(report: DocumentationSystemAuditReport) -> str:
    lines = ["Documentation system audit", ""]
    for dimension in report.dimensions:
        status = "PASS" if dimension.ok else "FAIL"
        suffix = " (review-only boundary)" if dimension.review_only else ""
        lines.append(f"[{status}] {dimension.name}{suffix}")
        if dimension.findings:
            for finding in dimension.findings:
                lines.append(f"- {finding}")
        else:
            lines.append("- no deterministic findings")
        lines.append("")
    lines.append(f"Overall: {'PASS' if report.ok else 'FAIL'}")
    return "\n".join(lines)


def write_documentation_system_audit_json(
    report: DocumentationSystemAuditReport,
    output_path: Path,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _freshness_dimension(project_root: Path, mesh_report: Any) -> DocumentationAuditDimension:
    freshness_codes = {"stale-current-state-marker", "version-mismatch", "release-doi-list-mismatch"}
    findings = [
        f"{finding.path}: {finding.message}"
        for finding in mesh_report.findings
        if finding.code in freshness_codes
    ]
    findings.extend(_status_handoff_sync_findings(project_root))
    findings.extend(_status_headroom_findings(project_root))
    return DocumentationAuditDimension("Aktualität", ok=not findings, findings=tuple(findings))


def _completeness_dimension(project_root: Path, check_doc_errors: tuple[str, ...]) -> DocumentationAuditDimension:
    missing = [path for path in REQUIRED_DOCS if not (project_root / path).exists()]
    findings = [f"missing required documentation file: {path}" for path in missing]
    findings.extend(error for error in check_doc_errors if "missing" in error.lower())
    return DocumentationAuditDimension("Vollständigkeit", ok=not findings, findings=tuple(findings))


def _correctness_dimension(
    check_doc_errors: tuple[str, ...],
    mesh_report: Any,
    lifecycle_report: Any,
) -> DocumentationAuditDimension:
    findings = list(check_doc_errors)
    findings.extend(f"doc-mesh:{finding.code}:{finding.path}: {finding.message}" for finding in mesh_report.findings)
    findings.extend(
        f"doc-lifecycle:{finding.code}:{finding.path}: {finding.message}"
        for finding in lifecycle_report.findings
    )
    return DocumentationAuditDimension("Korrektheit", ok=not findings, findings=tuple(findings))


def _redundancy_dimension(project_root: Path) -> DocumentationAuditDimension:
    findings: list[str] = []
    test_gates = _read_optional(project_root / "docs/TEST_GATES.md")
    if _contains_long_rule_duplication(test_gates):
        findings.append("docs/TEST_GATES.md appears to duplicate long rule-book content")
    status = _read_optional(project_root / "docs/STATUS.md")
    handoff = _read_optional(project_root / "docs/handoff/CURRENT_HANDOFF.md")
    for path, text in (("docs/STATUS.md", status), ("docs/handoff/CURRENT_HANDOFF.md", handoff)):
        if "concise pointers, not duplicate rule books" not in text and len(text.split()) > 3500:
            findings.append(f"{path} is long but does not state the concise-pointer boundary")
    boundary = (
        "semantic redundancy-free prose still requires advisory review; "
        "this hard check only catches known structural duplication patterns"
    )
    if not findings:
        findings.append(boundary)
    return DocumentationAuditDimension(
        "Redundanzfreiheit",
        ok=True if findings == [boundary] else False,
        findings=tuple(findings),
        review_only=findings == [boundary],
    )



def _status_headroom_findings(project_root: Path) -> tuple[str, ...]:
    status = _read_optional(project_root / "docs/STATUS.md")
    words = len(status.split())
    if words > STATUS_HEADROOM_WORD_LIMIT:
        return (f"docs/STATUS.md exceeds headroom limit: {words}/{STATUS_HEADROOM_WORD_LIMIT} words",)
    return ()


def _status_handoff_sync_findings(project_root: Path) -> tuple[str, ...]:
    status = _read_optional(project_root / "docs/STATUS.md")
    handoff = _read_optional(project_root / "docs/handoff/CURRENT_HANDOFF.md")
    findings: list[str] = []
    status_prs = set(re.findall(r"PR #\d+ merged", status))
    handoff_prs = set(re.findall(r"PR #\d+ merged", handoff))
    for item in sorted(status_prs - handoff_prs):
        findings.append(f"docs/handoff/CURRENT_HANDOFF.md missing current closeout marker from STATUS.md: {item}")
    for item in sorted(handoff_prs - status_prs):
        findings.append(f"docs/STATUS.md missing current closeout marker from CURRENT_HANDOFF.md: {item}")
    required_handoff_terms = (
        ".agentic/compiled_agent_context.yaml",
        "FINAL_SUMMARY_CONTRACT.md",
        "CHAT_COMMUNICATION_CONTRACT.md",
        "CHAT_BOOTSTRAP_AND_DRIFT_CONTRACT.md",
    )
    for term in required_handoff_terms:
        if term not in handoff:
            findings.append(f"docs/handoff/CURRENT_HANDOFF.md missing mandatory successor-chat source pointer: {term}")
    return tuple(findings)


def _document_order_dimension(project_root: Path) -> DocumentationAuditDimension:
    findings: list[str] = []
    context = _load_yaml(project_root / ".agentic/compiled_agent_context.yaml")
    configured = tuple(context.get("mandatory_successor_chat_sources", []) or [])
    if configured[: len(MANDATORY_ORDER)] != MANDATORY_ORDER:
        findings.append("compiled agent context does not preserve the mandatory successor-chat source order")
    for source in MANDATORY_ORDER:
        if source not in configured:
            findings.append(f"mandatory successor-chat source missing from compiled context: {source}")
        if not (project_root / source).exists():
            findings.append(f"mandatory successor-chat source file missing: {source}")
    return DocumentationAuditDimension("Stringenz der Dokumentenordnung", ok=not findings, findings=tuple(findings))


def _consistency_dimension(mesh_report: Any, lifecycle_report: Any) -> DocumentationAuditDimension:
    findings = [
        f"doc-mesh:{finding.code}:{finding.path}: {finding.message}" for finding in mesh_report.findings
    ]
    findings.extend(
        f"doc-lifecycle:{finding.code}:{finding.path}: {finding.message}"
        for finding in lifecycle_report.findings
    )
    return DocumentationAuditDimension("Konsistenz", ok=not findings, findings=tuple(findings))


def _contains_long_rule_duplication(text: str) -> bool:
    if "## LLM Communication and Bootstrap Gate" not in text:
        return False
    section = text.split("## LLM Communication and Bootstrap Gate", 1)[1]
    next_section = section.split("\n## ", 1)[0]
    return len(next_section.split()) > 450


def _read_optional(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    content = yaml.safe_load(path.read_text(encoding="utf-8"))
    return content if isinstance(content, dict) else {}
