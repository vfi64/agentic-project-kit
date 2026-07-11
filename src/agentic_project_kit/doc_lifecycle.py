from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

import json
from typing import Any

import yaml

from agentic_project_kit.documentation_registry import build_doc_registry_reconcile_report
from agentic_project_kit.documentation_registry import build_documentation_registry_summary
from agentic_project_kit.doc_lifecycle_signals import (
    build_review_after_findings,
    load_direction_statuses,
    resolve_current_version,
)

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

HEADER_AUDIT_EXEMPT_PREFIXES = (
    "docs/archive/",
    "docs/reports/",
    "docs/examples/",
)

STALE_BUDGETS_DAYS = {
    "governance": 180,
    "reference": 365,
    "workflow": 270,
}

STALE_BUDGET_CLASS_GROUPS = {
    "architecture": "governance",
    "governance/system": "governance",
    "operational/automation": "workflow",
    "release": "workflow",
    "user-facing description": "reference",
}

PLANNING_CLASS = "planning"


@dataclass(frozen=True)
class DocLifecycleDocument:
    path: str
    status: str | None
    decision_status: str | None
    status_date: str | None = None
    superseded_by: str | None = None
    document_class: str | None = None
    registry_status: str | None = None
    age_days: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "status": self.status,
            "decision_status": self.decision_status,
            "status_date": self.status_date,
            "superseded_by": self.superseded_by,
            "class": self.document_class,
            "registry_status": self.registry_status,
            "age_days": self.age_days,
        }


@dataclass(frozen=True)
class DocLifecycleFinding:
    code: str
    path: str
    message: str
    severity: str = "FAIL"
    document_class: str | None = None
    age_days: int | None = None

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "code": self.code,
            "path": self.path,
            "message": self.message,
            "severity": self.severity,
        }
        if self.document_class is not None:
            data["class"] = self.document_class
        if self.age_days is not None:
            data["age_days"] = self.age_days
        return data


@dataclass(frozen=True)
class DocLifecycleReport:
    documents: tuple[DocLifecycleDocument, ...]
    findings: tuple[DocLifecycleFinding, ...]
    registry_summary: dict[str, Any] | None = None

    @property
    def ok(self) -> bool:
        return not any(finding.severity in {"FAIL", "BLOCK"} for finding in self.findings)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "documents": [document.to_dict() for document in self.documents],
            "findings": [finding.to_dict() for finding in self.findings],
            "findings_by_code": _findings_by_code(self.findings),
            "registry_summary": self.registry_summary,
        }


def build_doc_lifecycle_report(
    project_root: Path,
    *,
    now: date | None = None,
    current_version: str | None = None,
) -> DocLifecycleReport:
    today = now or date.today()
    documents: list[DocLifecycleDocument] = []
    findings: list[DocLifecycleFinding] = []
    registry_entries = _load_documentation_registry_entries_by_path(project_root)
    direction_statuses = load_direction_statuses(project_root)
    resolved_current_version = resolve_current_version(project_root, current_version)
    visited_paths: set[str] = set()
    for relative_path in _iter_lifecycle_markdown_files(project_root):
        text = (project_root / relative_path).read_text(encoding="utf-8")
        status = _first_header_value(text, "Status")
        decision_status = _first_header_value(text, "Decision status")
        status_date = _first_header_value(text, "Status-date")
        superseded_by = _first_header_value(text, "Superseded-by")
        path_text = str(relative_path)
        registry_entry = registry_entries.get(path_text, {})
        age_days = _age_days(status_date, today)
        documents.append(
            DocLifecycleDocument(
                path_text,
                status,
                decision_status,
                status_date=status_date,
                superseded_by=superseded_by,
                document_class=_entry_class(registry_entry),
                registry_status=_entry_status(registry_entry),
                age_days=age_days,
            )
        )
        visited_paths.add(path_text)
        findings.extend(_audit_document(relative_path, text, status, decision_status))
        findings.extend(
            _audit_registry_header_consistency(
                project_root=project_root,
                path_text=path_text,
                text=text,
                registry_entry=registry_entry,
                status=status,
                status_date=status_date,
                superseded_by=superseded_by,
                now=today,
                current_version=resolved_current_version,
                direction_statuses=direction_statuses,
            )
        )
    for path_text, registry_entry in sorted(registry_entries.items()):
        if path_text in visited_paths or not path_text.endswith(".md"):
            continue
        document_path = project_root / path_text
        if not document_path.exists() or not document_path.is_file():
            continue
        text = document_path.read_text(encoding="utf-8")
        status = _first_header_value(text, "Status")
        status_date = _first_header_value(text, "Status-date")
        superseded_by = _first_header_value(text, "Superseded-by")
        age_days = _age_days(status_date, today)
        documents.append(
            DocLifecycleDocument(
                path_text,
                status,
                _first_header_value(text, "Decision status"),
                status_date=status_date,
                superseded_by=superseded_by,
                document_class=_entry_class(registry_entry),
                registry_status=_entry_status(registry_entry),
                age_days=age_days,
            )
        )
        findings.extend(
            _audit_registry_header_consistency(
                project_root=project_root,
                path_text=path_text,
                text=text,
                registry_entry=registry_entry,
                status=status,
                status_date=status_date,
                superseded_by=superseded_by,
                now=today,
                current_version=resolved_current_version,
                direction_statuses=direction_statuses,
            )
        )
    return DocLifecycleReport(
        documents=tuple(sorted(documents, key=lambda document: document.path)),
        findings=tuple(findings),
        registry_summary=_load_registry_summary(project_root),
    )


def write_doc_lifecycle_json_report(report: DocLifecycleReport, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _findings_by_code(findings: tuple[DocLifecycleFinding, ...]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for finding in findings:
        grouped.setdefault(finding.code, []).append(finding.to_dict())
    return dict(sorted(grouped.items()))


def render_doc_lifecycle_report(report: DocLifecycleReport) -> str:
    lines = ["Documentation lifecycle audit", "", "Documents:"]
    if not report.documents:
        lines.append("- none")
    for document in report.documents:
        status = document.status if document.status is not None else "MISSING"
        class_suffix = f" | class={document.document_class}" if document.document_class else ""
        age_suffix = f" | age_days={document.age_days}" if document.age_days is not None else ""
        lines.append(f"- {document.path}: {status}{class_suffix}{age_suffix}")
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
            class_suffix = f" | class={finding.document_class}" if finding.document_class else ""
            age_suffix = f" | age_days={finding.age_days}" if finding.age_days is not None else ""
            lines.append(
                f"- [{finding.severity}|{finding.code}] {finding.path}: "
                f"{finding.message}{class_suffix}{age_suffix}"
            )
    lines.extend(["", f"Overall: {'PASS' if report.ok else 'FAIL'}"])
    return "\n".join(lines)


def _load_registry_summary(project_root: Path) -> dict[str, Any] | None:
    try:
        summary = build_documentation_registry_summary(project_root)
    except (OSError, ValueError):
        return None
    summary["entries_by_path"] = _load_documentation_registry_entries_by_path(project_root)
    return summary


def _load_documentation_registry_entries_by_path(project_root: Path) -> dict[str, dict[str, Any]]:
    registry_path = project_root / "docs" / "DOCUMENTATION_REGISTRY.yaml"
    if not registry_path.exists():
        return {}
    data = yaml.safe_load(registry_path.read_text(encoding="utf-8")) or {}
    documents = data.get("documents", []) if isinstance(data, dict) else []
    entries: dict[str, dict[str, Any]] = {}
    for item in documents:
        if not isinstance(item, dict):
            continue
        path = item.get("path")
        if isinstance(path, str) and path:
            entries[path] = item
    return entries


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


def _audit_registry_header_consistency(
    *,
    project_root: Path,
    path_text: str,
    text: str,
    registry_entry: dict[str, Any],
    status: str | None,
    status_date: str | None,
    superseded_by: str | None,
    now: date,
    current_version: str | None,
    direction_statuses: dict[str, str],
) -> list[DocLifecycleFinding]:
    if not registry_entry or _is_lifecycle_header_exempt(path_text):
        return []

    findings: list[DocLifecycleFinding] = []
    document_class = _entry_class(registry_entry)
    for signal in build_review_after_findings(
        path=path_text,
        review_after=registry_entry.get("review_after"),
        now=now,
        current_version=current_version,
        direction_statuses=direction_statuses,
        document_class=document_class,
    ):
        findings.append(DocLifecycleFinding(**signal.to_finding_kwargs()))

    if status is None or status_date is None:
        missing = []
        if status is None:
            missing.append("Status")
        if status_date is None:
            missing.append("Status-date")
        findings.append(
            DocLifecycleFinding(
                "HEADER_MISSING",
                path_text,
                "missing lifecycle header field(s): " + ", ".join(missing),
                severity="WARN",
                document_class=document_class,
            )
        )

    registry_status = _entry_status(registry_entry)
    if status is not None and registry_status is not None and status != registry_status:
        findings.append(
            DocLifecycleFinding(
                "HEADER_REGISTRY_MISMATCH",
                path_text,
                f"header status {status!r} differs from registry status {registry_status!r}",
                severity="WARN",
                document_class=document_class,
            )
        )

    if superseded_by and superseded_by != "n/a":
        target = project_root / superseded_by
        if not target.exists():
            findings.append(
                DocLifecycleFinding(
                    "SUPERSEDED_TARGET_MISSING",
                    path_text,
                    f"Superseded-by target does not exist: {superseded_by}",
                    severity="WARN",
                    document_class=document_class,
                )
            )

    age_days = _age_days(status_date, now)
    budget_group = _stale_budget_group(document_class)
    if age_days is not None and budget_group is not None:
        budget_days = STALE_BUDGETS_DAYS[budget_group]
        if age_days > budget_days:
            findings.append(
                DocLifecycleFinding(
                    "STALE_BY_BUDGET",
                    path_text,
                    f"Status-date is {age_days} days old; {budget_group} budget is {budget_days} days",
                    severity="WARN",
                    document_class=document_class,
                    age_days=age_days,
                )
            )

    return findings


def _first_header_value(text: str, key: str) -> str | None:
    prefix = f"{key}:"
    for line in text.splitlines():
        if line.startswith(prefix):
            value = line[len(prefix):].strip()
            return value or None
    return None


def _entry_class(entry: dict[str, Any]) -> str | None:
    value = entry.get("class")
    return value if isinstance(value, str) and value else None


def _entry_status(entry: dict[str, Any]) -> str | None:
    value = entry.get("status")
    return value if isinstance(value, str) and value else None


def _is_lifecycle_header_exempt(path_text: str) -> bool:
    return any(path_text.startswith(prefix) for prefix in HEADER_AUDIT_EXEMPT_PREFIXES)


def _stale_budget_group(document_class: str | None) -> str | None:
    if document_class == PLANNING_CLASS:
        return None
    return STALE_BUDGET_CLASS_GROUPS.get(document_class or "")


def _age_days(status_date: str | None, now: date) -> int | None:
    if status_date is None:
        return None
    try:
        parsed = date.fromisoformat(status_date)
    except ValueError:
        return None
    return (now - parsed).days


def build_doc_lifecycle_triage_payload(project_root: Path) -> dict[str, Any]:
    """Build a safe dry-run lifecycle triage report.

    The triage layer is intentionally advisory. Missing lifecycle metadata is
    WARN-only. Objective event conflicts, such as an invalid Status header, are
    blocking because they make downstream lifecycle decisions unsafe.
    """
    report = build_doc_lifecycle_report(project_root)
    reconcile = _load_reconcile_summary(project_root)
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
                "source": "doc-lifecycle-triage",
            }
        )

    reconcile_actions = _reconcile_actions(reconcile)
    finding_paths = {finding["path"] for finding in findings if finding["severity"] == "FAIL"}
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
                "source": "doc-lifecycle-triage",
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
            "proposed_actions": len(proposed_actions) + len(reconcile_actions),
            "reconcile_findings": len(reconcile.get("findings", [])),
        },
        "documents": [_document_with_registry_metadata(document, report.registry_summary) for document in report.documents],
        "findings": findings,
        "proposed_actions": proposed_actions + reconcile_actions,
        "registry_summary": _public_registry_summary(report.registry_summary),
        "reconcile": reconcile,
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


def build_doc_lifecycle_plan_payload(project_root: Path, scope: str) -> dict[str, Any]:
    """Build a deterministic dry-run lifecycle plan for a repository scope."""
    normalized_scope = scope.strip().strip("/")
    triage = build_doc_lifecycle_triage_payload(project_root)
    steps: list[dict[str, Any]] = []

    for action in triage.get("proposed_actions", []):
        path = action["path"]
        if normalized_scope and not (
            path == normalized_scope or path.startswith(normalized_scope + "/")
        ):
            continue
        operation = action["operation"]
        registry_by_path = _registry_metadata_by_path(triage)
        steps.append(
            {
                "id": action["id"],
                "path": path,
                "operation": operation,
                "reason": action["reason"],
                "execute": False,
                "safety_class": _plan_safety_class(operation),
                "source": action.get("source", "doc-lifecycle-triage"),
                "registry": registry_by_path.get(
                    path,
                    _registry_metadata_for_path(triage.get("registry_summary") or {}, path),
                ),
            }
        )

    failures = sum(1 for step in steps if step["safety_class"] == "human-decision-required")
    result_status = "BLOCK" if triage["result_status"] == "BLOCK" and failures else "PASS"

    return {
        "schema_version": 1,
        "kind": "doc_lifecycle_plan",
        "mode": "dry-run",
        "scope": normalized_scope,
        "execution_enabled": False,
        "result_status": result_status,
        "summary": {
            "steps": len(steps),
            "failures": failures,
            "warnings": sum(1 for step in steps if step["safety_class"] == "advisory"),
            "safe_noops": sum(1 for step in steps if step["safety_class"] == "no-op-confirmation"),
        },
        "steps": steps,
        "triage_summary": triage["summary"],
    }


def render_doc_lifecycle_plan_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "DOC_LIFECYCLE_PLAN",
        f"STATUS: {payload['result_status']}",
        f"MODE: {payload['mode']}",
        f"SCOPE: {payload['scope']}",
        "EXECUTION: disabled",
        f"STEPS: {summary['steps']}",
        f"FAILURES: {summary['failures']}",
        f"WARNINGS: {summary['warnings']}",
        "",
        "STEPS:",
    ]
    if not payload["steps"]:
        lines.append("- none")
    for step in payload["steps"]:
        registry = step.get("registry", {})
        registry_note = (
            f" | class={registry.get('doc_class')} | owner={registry.get('owner')}"
            if registry
            else ""
        )
        lines.append(
            "- "
            f"{step['operation']} | {step['path']} | "
            f"{step['safety_class']} | execute={str(step['execute']).lower()}"
            f" | source={step.get('source', 'doc-lifecycle-triage')}"
            f"{registry_note}"
        )
    return "\n".join(lines) + "\n"


def _plan_safety_class(operation: str) -> str:
    if operation == "confirm-current":
        return "no-op-confirmation"
    if operation in {"defer", "historical"}:
        return "advisory"
    return "human-decision-required"



def _registry_metadata_for_path(registry_summary: dict[str, Any] | None, path: str) -> dict[str, Any]:
    """Return stable lifecycle registry context for one repository-relative path."""
    registry_summary = registry_summary or {}
    entry = (registry_summary.get("entries_by_path") or {}).get(path)
    if isinstance(entry, dict):
        return {
            "registered": True,
            "doc_class": entry.get("class"),
            "owner": entry.get("owner"),
            "scope": "in-scope",
            "status": entry.get("status"),
            "review_policy": entry.get("review_policy"),
            "summary": entry.get("summary"),
        }
    unregistered = set(registry_summary.get("unregistered_candidates", []))
    if path in unregistered:
        return {
            "registered": False,
            "doc_class": None,
            "owner": None,
            "scope": "unregistered-candidate",
            "status": None,
            "review_policy": None,
            "summary": None,
        }
    return {
        "registered": None,
        "doc_class": None,
        "owner": None,
        "scope": "unknown",
        "status": None,
        "review_policy": None,
        "summary": None,
    }

def _registry_metadata_by_path(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    registry_summary = payload.get("registry_summary") or {}
    return {
        document["path"]: document.get(
            "registry",
            _registry_metadata_for_path(registry_summary, document["path"]),
        )
        for document in payload.get("documents", [])
    }



def _document_with_registry_metadata(document: Any, registry_summary: dict[str, Any]) -> dict[str, Any]:
    data = document.to_dict()
    data["registry"] = _registry_metadata_for_path(registry_summary or {}, document.path)
    return data



def _public_registry_summary(registry_summary: dict[str, Any] | None) -> dict[str, Any] | None:
    if registry_summary is None:
        return None
    public = dict(registry_summary)
    public.pop("entries_by_path", None)
    return public



def _load_reconcile_summary(project_root: Path) -> dict[str, Any]:
    try:
        report = build_doc_registry_reconcile_report(project_root)
    except (OSError, ValueError):
        return {
            "schema_version": 1,
            "kind": "doc_registry_reconcile_report",
            "mode": "dry-run",
            "result_status": "PASS",
            "findings": [],
        }
    public = dict(report)
    public.pop("rendered_scope_decision_table", None)
    public.pop("scope_decision_rows", None)
    return public


def _reconcile_actions(reconcile: dict[str, Any]) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    for index, finding in enumerate(reconcile.get("findings", []), start=1):
        severity = finding.get("severity", "WARN")
        operation = "manual-review" if severity == "BLOCK" else "defer"
        actions.append(
            {
                "id": f"doc-registry-reconcile:{index}:{finding.get('kind', 'finding')}",
                "path": finding.get("path") or "docs",
                "operation": operation,
                "reason": finding.get("message", "doc-registry reconcile finding"),
                "execute": "false",
                "source": "doc-registry-reconcile",
                "finding_kind": finding.get("kind"),
                "severity": severity,
                "next_action": finding.get("next_action"),
            }
        )
    return actions



def build_doc_lifecycle_apply_payload(
    project_root: Path,
    scope: str,
    only: str,
    *,
    execute: bool,
) -> dict[str, Any]:
    """Apply one safe lifecycle plan step.

    This first apply slice intentionally supports only no-op confirmations and
    deferrals. It never edits, moves, archives, or deletes files.
    """
    if not execute:
        return {
            "schema_version": 1,
            "kind": "doc_lifecycle_apply_result",
            "mode": "blocked",
            "result_status": "BLOCK",
            "reason": "missing_execute_flag",
            "requested_id": only,
            "mutation": "none",
        }

    plan = build_doc_lifecycle_plan_payload(project_root, scope)
    match = next((step for step in plan.get("steps", []) if step.get("id") == only), None)
    if match is None:
        return {
            "schema_version": 1,
            "kind": "doc_lifecycle_apply_result",
            "mode": "blocked",
            "result_status": "BLOCK",
            "reason": "unknown_step_id",
            "requested_id": only,
            "mutation": "none",
        }

    operation = match.get("operation")
    if operation not in {"confirm-current", "defer"}:
        return {
            "schema_version": 1,
            "kind": "doc_lifecycle_apply_result",
            "mode": "blocked",
            "result_status": "BLOCK",
            "reason": "unsafe_operation",
            "requested_id": only,
            "mutation": "none",
            "step": match,
        }

    return {
        "schema_version": 1,
        "kind": "doc_lifecycle_apply_result",
        "mode": "execute",
        "result_status": "PASS",
        "requested_id": only,
        "mutation": "none",
        "applied": {
            "id": match["id"],
            "path": match["path"],
            "operation": operation,
            "effect": "no-op",
            "reason": match["reason"],
            "source": match.get("source", "doc-lifecycle-triage"),
        },
    }


def render_doc_lifecycle_apply_report(payload: dict[str, Any]) -> str:
    lines = [
        "DOC_LIFECYCLE_APPLY",
        f"STATUS: {payload['result_status']}",
        f"MODE: {payload['mode']}",
        "MUTATION: none",
    ]
    if payload["result_status"] == "BLOCK":
        lines.append(f"REASON: {payload['reason']}")
        lines.append(f"REQUESTED_ID: {payload['requested_id']}")
    else:
        applied = payload["applied"]
        lines.append(f"APPLIED: {applied['id']}")
        lines.append(f"OPERATION: {applied['operation']}")
        lines.append(f"EFFECT: {applied['effect']}")
        lines.append(f"SOURCE: {applied['source']}")
    return "\n".join(lines) + "\n"



def build_doc_lifecycle_evidence_report_payload(
    project_root: Path,
    scope: str,
    output_path: Path,
    *,
    execute: bool,
) -> dict[str, Any]:
    """Build or write one explicit documentation lifecycle evidence report."""
    output = output_path if output_path.is_absolute() else project_root / output_path
    allowed, relative_output = _is_allowed_lifecycle_evidence_output(project_root, output)
    if not allowed:
        return {
            "schema_version": 1,
            "kind": "doc_lifecycle_evidence_report_result",
            "mode": "blocked",
            "result_status": "BLOCK",
            "reason": "output_path_not_allowed",
            "output_path": str(output),
            "mutation": "none",
        }

    triage = build_doc_lifecycle_triage_payload(project_root)
    plan = build_doc_lifecycle_plan_payload(project_root, scope)
    handoff_context = _load_handoff_context(project_root)
    report = {
        "schema_version": 1,
        "kind": "doc_lifecycle_evidence_report",
        "scope": scope.strip().strip("/"),
        "triage": triage,
        "plan": plan,
        "handoff_context": handoff_context,
    }

    if not execute:
        return {
            "schema_version": 1,
            "kind": "doc_lifecycle_evidence_report_result",
            "mode": "dry-run",
            "result_status": "PASS",
            "scope": scope.strip().strip("/"),
            "output_path": relative_output,
            "would_write": True,
            "mutation": "none",
            "archive": "disabled",
            "delete": "disabled",
            "handoff_context": handoff_context,
            "report_summary": {
                "triage": triage["summary"],
                "plan": plan["summary"],
            },
        }

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "schema_version": 1,
        "kind": "doc_lifecycle_evidence_report_result",
        "mode": "execute",
        "result_status": "PASS",
        "scope": scope.strip().strip("/"),
        "output_path": relative_output,
        "would_write": True,
        "mutation": "write-report",
        "archive": "disabled",
        "delete": "disabled",
        "handoff_context": handoff_context,
        "report_summary": {
            "triage": triage["summary"],
            "plan": plan["summary"],
        },
    }


def render_doc_lifecycle_evidence_report_result(payload: dict[str, Any]) -> str:
    lines = [
        "DOC_LIFECYCLE_EVIDENCE_REPORT",
        f"STATUS: {payload['result_status']}",
        f"MODE: {payload['mode']}",
        f"MUTATION: {payload['mutation']}",
        "ARCHIVE: disabled",
        "DELETE: disabled",
        f"HANDOFF_CONTEXT: {payload.get('handoff_context', {}).get('severity', 'advisory')}",
    ]
    if payload["result_status"] == "BLOCK":
        lines.append(f"REASON: {payload['reason']}")
    else:
        lines.append(f"OUTPUT: {payload['output_path']}")
        lines.append(f"SCOPE: {payload['scope']}")
    return "\n".join(lines) + "\n"


def _is_allowed_lifecycle_evidence_output(project_root: Path, output_path: Path) -> tuple[bool, str]:
    resolved_root = project_root.resolve()
    resolved_output = output_path.resolve()
    try:
        relative = resolved_output.relative_to(resolved_root)
    except ValueError:
        return False, str(resolved_output)
    relative_text = relative.as_posix()
    allowed_prefixes = (
        "docs/architecture/evidence/",
        "docs/reports/doc-lifecycle/",
        "tmp/",
    )
    return relative_text.startswith(allowed_prefixes), relative_text



def _load_handoff_context(project_root: Path) -> dict[str, Any]:
    """Load lightweight successor handoff context for lifecycle evidence.

    This is advisory evidence only. It does not decide repository state and it
    does not replace post-merge-check.
    """
    validation_path = (
        project_root
        / "docs"
        / "reports"
        / "handoff-packages"
        / "latest"
        / "validation_report.json"
    )
    if not validation_path.exists():
        return {
            "available": False,
            "severity": "advisory",
            "safe_to_continue": None,
            "path": validation_path.as_posix(),
        }
    try:
        data = json.loads(validation_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {
            "available": True,
            "severity": "advisory",
            "safe_to_continue": None,
            "path": validation_path.as_posix(),
            "parse_status": "unreadable",
        }

    result_status = data.get("result_status") or data.get("status")
    head_status = (
        data.get("head_status")
        or data.get("successor_package_head_status")
        or data.get("generated_head_status")
    )
    safe_to_continue = result_status in {"PASS", "WARN"} and head_status in {
        None,
        "current",
        "matches_head",
        "refresh_only_descendant",
    }
    return {
        "available": True,
        "severity": "advisory",
        "safe_to_continue": safe_to_continue,
        "path": validation_path.as_posix(),
        "result_status": result_status,
        "head_status": head_status,
        "generated_head": data.get("generated_head"),
        "current_head": data.get("current_head"),
    }
