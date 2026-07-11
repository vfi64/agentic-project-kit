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
from agentic_project_kit.documentation_registry import build_documentation_registry_summary
from agentic_project_kit.workspace import KitConfig, Workspace, load_workspace


_LEGACY_WORKSPACE = Workspace(root=Path("."), config=KitConfig())

STATUS_HEADROOM_WORD_LIMIT = 4968


def _workspace_path_text(ws: Workspace, path: Path) -> str:
    try:
        return path.relative_to(ws.root).as_posix()
    except ValueError:
        return path.as_posix()


def _mandatory_order(ws: Workspace) -> tuple[str, ...]:
    return (
        _workspace_path_text(ws, ws.compiled_agent_context_path()),
        _workspace_path_text(ws, ws.governance_file("FINAL_SUMMARY_CONTRACT.md")),
        _workspace_path_text(ws, ws.governance_file("CHAT_COMMUNICATION_CONTRACT.md")),
        _workspace_path_text(ws, ws.governance_file("PORTABLE_CHAT_EXECUTION_CONTRACT.md")),
        _workspace_path_text(ws, ws.governance_file("CHAT_BOOTSTRAP_AND_DRIFT_CONTRACT.md")),
        _workspace_path_text(ws, ws.test_gates_path()),
        _workspace_path_text(ws, ws.status_path()),
        _workspace_path_text(ws, ws.handoff_file("CURRENT_HANDOFF.md")),
    )


def _required_docs(ws: Workspace) -> tuple[str, ...]:
    return (
        _workspace_path_text(ws, ws.root_file("README.md")),
        _workspace_path_text(ws, ws.root_file("AGENTS.md")),
        _workspace_path_text(ws, ws.status_path()),
        _workspace_path_text(ws, ws.test_gates_path()),
        _workspace_path_text(ws, ws.handoff_file("CURRENT_HANDOFF.md")),
        _workspace_path_text(ws, ws.documentation_coverage_path()),
        _workspace_path_text(ws, ws.doc_registry_path()),
        _workspace_path_text(ws, ws.root_file("sentinel.yaml")),
        _workspace_path_text(ws, ws.compiled_agent_context_path()),
        _workspace_path_text(ws, ws.governance_file("FINAL_SUMMARY_CONTRACT.md")),
        _workspace_path_text(ws, ws.governance_file("CHAT_COMMUNICATION_CONTRACT.md")),
        _workspace_path_text(ws, ws.governance_file("PORTABLE_CHAT_EXECUTION_CONTRACT.md")),
        _workspace_path_text(ws, ws.governance_file("CHAT_BOOTSTRAP_AND_DRIFT_CONTRACT.md")),
        _workspace_path_text(ws, ws.governance_file("DOCUMENTATION_REGISTRY_CONTRACT.md")),
        _workspace_path_text(ws, ws.architecture_file("ARCHITECTURE_CONTRACT.md")),
        _workspace_path_text(ws, ws.architecture_file("DOCUMENTATION_INFORMATION_ARCHITECTURE.md")),
    )


MANDATORY_ORDER = _mandatory_order(_LEGACY_WORKSPACE)
REQUIRED_DOCS = _required_docs(_LEGACY_WORKSPACE)


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
    ws = load_workspace(project_root)
    check_doc_errors = tuple(check_docs(project_root))
    mesh_report = build_doc_mesh_report(project_root)
    lifecycle_report = build_doc_lifecycle_report(project_root)
    dimensions = (
        _freshness_dimension(ws, mesh_report),
        _completeness_dimension(ws, check_doc_errors),
        _correctness_dimension(check_doc_errors, mesh_report, lifecycle_report),
        _redundancy_dimension(ws),
        _document_order_dimension(ws),
        _registry_dimension(project_root),
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


def _freshness_dimension(ws: Workspace, mesh_report: Any) -> DocumentationAuditDimension:
    freshness_codes = {"stale-current-state-marker", "version-mismatch", "release-doi-list-mismatch"}
    findings = [
        f"{finding.path}: {finding.message}"
        for finding in mesh_report.findings
        if finding.code in freshness_codes
    ]
    findings.extend(_status_handoff_sync_findings(ws))
    findings.extend(_status_headroom_findings(ws))
    return DocumentationAuditDimension("Aktualität", ok=not findings, findings=tuple(findings))


def _completeness_dimension(ws: Workspace, check_doc_errors: tuple[str, ...]) -> DocumentationAuditDimension:
    missing = [path for path in _required_docs(ws) if not (ws.root / path).exists()]
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
    findings.extend(_blocking_lifecycle_findings(lifecycle_report))
    return DocumentationAuditDimension("Korrektheit", ok=not findings, findings=tuple(findings))


def _redundancy_dimension(ws: Workspace) -> DocumentationAuditDimension:
    findings: list[str] = []
    test_gates = _read_optional(ws.test_gates_path())
    if _contains_long_rule_duplication(test_gates):
        findings.append(f"{_workspace_path_text(ws, ws.test_gates_path())} appears to duplicate long rule-book content")
    status = _read_optional(ws.status_path())
    handoff = _read_optional(ws.handoff_file("CURRENT_HANDOFF.md"))
    for path, text in (
        (_workspace_path_text(ws, ws.status_path()), status),
        (_workspace_path_text(ws, ws.handoff_file("CURRENT_HANDOFF.md")), handoff),
    ):
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



def _status_headroom_findings(ws: Workspace) -> tuple[str, ...]:
    status_path = ws.status_path()
    status = _read_optional(status_path)
    words = len(status.split())
    if words > STATUS_HEADROOM_WORD_LIMIT:
        return (f"{_workspace_path_text(ws, status_path)} exceeds headroom limit: {words}/{STATUS_HEADROOM_WORD_LIMIT} words",)
    return ()


def _status_handoff_sync_findings(ws: Workspace) -> tuple[str, ...]:
    status_path = ws.status_path()
    handoff_path = ws.handoff_file("CURRENT_HANDOFF.md")
    status_name = _workspace_path_text(ws, status_path)
    handoff_name = _workspace_path_text(ws, handoff_path)
    status = _read_optional(status_path)
    handoff = _read_optional(handoff_path)
    findings: list[str] = []
    status_prs = set(re.findall(r"PR #\d+ merged", status))
    handoff_prs = set(re.findall(r"PR #\d+ merged", handoff))
    for item in sorted(status_prs - handoff_prs):
        findings.append(f"{handoff_name} missing current closeout marker from STATUS.md: {item}")
    for item in sorted(handoff_prs - status_prs):
        findings.append(f"{status_name} missing current closeout marker from CURRENT_HANDOFF.md: {item}")
    required_handoff_terms = (
        _workspace_path_text(ws, ws.compiled_agent_context_path()),
        "FINAL_SUMMARY_CONTRACT.md",
        "CHAT_COMMUNICATION_CONTRACT.md",
        "CHAT_BOOTSTRAP_AND_DRIFT_CONTRACT.md",
    )
    for term in required_handoff_terms:
        if term not in handoff:
            findings.append(f"{handoff_name} missing mandatory successor-chat source pointer: {term}")
    return tuple(findings)


def _document_order_dimension(ws: Workspace) -> DocumentationAuditDimension:
    findings: list[str] = []
    context = _load_yaml(ws.compiled_agent_context_path())
    configured = tuple(context.get("mandatory_successor_chat_sources", []) or [])
    mandatory_order = _mandatory_order(ws)
    if configured[: len(mandatory_order)] != mandatory_order:
        findings.append("compiled agent context does not preserve the mandatory successor-chat source order")
    for source in mandatory_order:
        if source not in configured:
            findings.append(f"mandatory successor-chat source missing from compiled context: {source}")
        if not (ws.root / source).exists():
            findings.append(f"mandatory successor-chat source file missing: {source}")
    return DocumentationAuditDimension("Stringenz der Dokumentenordnung", ok=not findings, findings=tuple(findings))


def _registry_dimension(project_root: Path) -> DocumentationAuditDimension:
    try:
        summary = build_documentation_registry_summary(project_root)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        return DocumentationAuditDimension(
            "Dokumentationsregistry",
            ok=False,
            findings=(f"registry summary unavailable: {exc}",),
        )

    findings = [
        f"registry={summary['registry_path']}",
        f"version={summary['version']}",
        f"documents={summary['document_count']}",
        f"broad_migration_allowed={summary['broad_migration_allowed']}",
    ]
    class_counts = summary.get("class_counts", {})
    if isinstance(class_counts, dict):
        for class_name, count in class_counts.items():
            findings.append(f"class:{class_name}={count}")
    return DocumentationAuditDimension(
        "Dokumentationsregistry",
        ok=summary.get("version") == 1 and bool(summary.get("document_count")),
        findings=tuple(findings),
    )


def _consistency_dimension(mesh_report: Any, lifecycle_report: Any) -> DocumentationAuditDimension:
    findings = [
        f"doc-mesh:{finding.code}:{finding.path}: {finding.message}" for finding in mesh_report.findings
    ]
    findings.extend(_blocking_lifecycle_findings(lifecycle_report))
    return DocumentationAuditDimension("Konsistenz", ok=not findings, findings=tuple(findings))


def _blocking_lifecycle_findings(lifecycle_report: Any) -> list[str]:
    return [
        f"doc-lifecycle:{finding.code}:{finding.path}: {finding.message}"
        for finding in lifecycle_report.findings
        if getattr(finding, "severity", "FAIL") in {"FAIL", "BLOCK"}
    ]


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
