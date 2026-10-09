"""Read-only audits of contracts actually declared by an external workspace.

The Kit's fixed document set and class-rule inventory belong to self-hosting.
External targets use sentinel documents, registry scope, version anchors and
optional transfer state. Invalid declarations remain blockers in warn mode.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from agentic_project_kit.checks import check_document_quality, check_documentation_coverage
from agentic_project_kit.doc_lifecycle import build_doc_lifecycle_report
from agentic_project_kit.doc_lifecycle_signals import resolve_current_version
from agentic_project_kit.document_budgets import evaluate_document_word_budget
from agentic_project_kit.documentation_audit_models import (
    DocumentationAuditDimension, DocumentationSystemAuditReport,
)
from agentic_project_kit.documentation_facts import canonical_fact_findings
from agentic_project_kit.documentation_registry import (
    DOCUMENT_CLASSES, REQUIRED_DOCUMENT_FIELDS, load_documentation_registry_scope,
    required_scope_document_paths,
)
from agentic_project_kit.dpa_registry_contracts import validate_dpa_registry_contracts
from agentic_project_kit.handoff_state import validate_handoff_state
from agentic_project_kit.release_version_sources import release_version_anchors
from agentic_project_kit.workspace import Workspace, load_workspace


def _mapping(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path.name}: expected a mapping")
    return data


def _local_file(ws: Workspace, value: object) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("documentation path must be a non-empty string")
    path = ws.root / value
    if Path(value).is_absolute() or not path.resolve().is_relative_to(ws.root.resolve()):
        raise ValueError(f"documentation path must stay inside the workspace: {value}")
    return path


def _registry(ws: Workspace) -> tuple[dict[str, Any], list[str]]:
    path = ws.doc_registry_path()
    if not path.exists() and (ws.root / "docs/DOCUMENTATION_REGISTRY.yaml").exists():
        path = ws.root / "docs/DOCUMENTATION_REGISTRY.yaml"
    if not path.exists():
        return {}, []
    data = _mapping(path)
    if data.get("version", data.get("schema_version")) != 1:
        raise ValueError(f"{ws.path_text(path)}: registry version must be 1")
    documents = data.get("documents")
    if not isinstance(documents, list):
        raise ValueError(f"{ws.path_text(path)}: documents must be a list")
    rules = data.get("class_rules", {})
    if not isinstance(rules, dict) or any(not isinstance(r, dict) for r in rules.values()):
        raise ValueError(f"{ws.path_text(path)}: class_rules must map class names to mappings")
    allowed = set(DOCUMENT_CLASSES) | set(rules)
    errors: list[str] = []
    seen: set[str] = set()
    for index, entry in enumerate(documents):
        if not isinstance(entry, dict):
            raise ValueError(f"registry document {index}: expected mapping")
        for field in REQUIRED_DOCUMENT_FIELDS:
            if not isinstance(entry.get(field), str) or not entry[field].strip():
                errors.append(f"registry document {index}: missing {field}")
        if entry.get("class") not in allowed:
            errors.append(f"registry document {index}: undeclared class {entry.get('class')!r}")
        if entry.get("path"):
            file = _local_file(ws, entry["path"])
            if entry["path"] in seen:
                errors.append(f"duplicate registered path: {entry['path']}")
            seen.add(entry["path"])
            if not file.is_file():
                errors.append(f"registered document does not exist: {entry['path']}")
    errors.extend(validate_dpa_registry_contracts(ws.root, documents, registry_path=path))
    return data, errors


def _declared_documents(ws: Workspace, registry: dict[str, Any]) -> tuple[list[str], list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    required: list[str] = []
    sentinel = _mapping(ws.root / "sentinel.yaml")
    documents = sentinel.get("documents", [])
    if not isinstance(documents, list):
        raise ValueError("sentinel.yaml: documents must be a list")
    for doc in documents:
        if not isinstance(doc, dict):
            raise ValueError("sentinel.yaml: each document must be a mapping")
        path = _local_file(ws, doc.get("path"))
        required.append(ws.path_text(path))
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        sections = doc.get("required_sections", [])
        if not isinstance(sections, list) or any(not isinstance(s, str) for s in sections):
            raise ValueError(f"{doc['path']}: required_sections must be a list of strings")
        errors.extend(f"{doc['path']}: missing required section {s!r}" for s in sections if s not in text)
        budget = evaluate_document_word_budget(doc["path"], text, max_words=doc.get("max_words"),
                                               warn_words=doc.get("warn_words"))
        errors.extend(budget.errors)
        warnings.extend(budget.warnings)
        if doc.get("min_words") is not None and len(text.split()) < int(doc["min_words"]):
            errors.append(f"{doc['path']}: shorter than declared min_words")
        if doc.get("quality_checks", True):
            errors.extend(check_document_quality(doc["path"], text))
    scope = load_documentation_registry_scope(ws.root)
    errors.extend(scope.errors)
    required.extend(scope.required_files)
    for directory in scope.required_paths:
        if not _local_file(ws, directory).is_dir():
            errors.append(f"missing required documentation directory: {directory}")
    for name in required:
        if not _local_file(ws, name).is_file():
            errors.append(f"missing required documentation file: {name}")
    registered = {entry.get("path") for entry in registry.get("documents", [])}
    errors.extend(f"required-scope document is unregistered: {name}"
                  for name in required_scope_document_paths(ws.root, scope) if name not in registered)
    if ws.documentation_coverage_path().exists():
        errors.extend(check_documentation_coverage(ws.root))
    return required, errors, warnings


def _versions(ws: Workspace) -> tuple[list[str], list[str]]:
    version = resolve_current_version(ws.root)
    if version is None:
        return [], ["No literal project version authority; version mesh is not applicable."]
    errors: list[str] = []
    for anchor in release_version_anchors(ws.root, version):
        path = _local_file(ws, anchor.path)
        if not path.is_file():
            errors.append(f"missing version anchor: {anchor.path}")
        elif not anchor.matches(path.read_text(encoding="utf-8")):
            errors.append(f"version-mismatch: {anchor.path}: expected {version} ({anchor.label})")
    return errors, []


def _handoff(ws: Workspace) -> tuple[list[str], list[str]]:
    if not ws.modules.get("transfer", False):
        return [], ["Transfer module disabled; successor handoff contracts are not applicable."]
    errors: list[str] = []
    state = ws.handoff_state_path()
    if state.exists():
        errors.extend(f"{ws.path_text(state)}: {e}" for e in validate_handoff_state(_mapping(state)))
    package = ws.handoff_packages_latest()
    if package.exists():
        from agentic_project_kit.successor_handoff_package import validate_successor_outputs

        required = ("successor_context.yaml", "source_manifest.json", "execution_contract.json",
                    "successor_prompt.md", "validation_report.json")
        missing = [name for name in required if not (package / name).is_file()]
        if missing:
            return [*errors, f"Incomplete successor package: missing {', '.join(missing)}"], []
        context = _mapping(package / "successor_context.yaml")
        repo = context.get("repo")
        if not isinstance(repo, dict) or any(not isinstance(repo.get(k), str) or not repo[k]
                                             for k in ("head", "head_short")):
            return ["successor_context.yaml: missing repo.head or repo.head_short"], []
        outputs = {p.name: p.read_text(encoding="utf-8") for p in package.iterdir()
                   if p.is_file() and p.name != "validation_report.json"}
        for name in ("NEXT_CHAT_BOOTSTRAP.md", "START_NEW_CHAT_PROMPT.md", "CLOSEOUT_BEFORE_CHAT_SWITCH_PROMPT.md"):
            path = ws.handoff_file(name)
            if path.exists():
                outputs[ws.path_text(path)] = path.read_text(encoding="utf-8")
        result = validate_successor_outputs(outputs, context, ws)
        errors.extend(f"handoff:{f['code']}: {f['message']}" for f in result["findings"])
    return errors, [] if state.exists() or package.exists() else ["No previous handoff; fresh workspace."]


def build_external_documentation_audit(root: Path) -> DocumentationSystemAuditReport:
    try:
        ws = load_workspace(root, suppress_legacy_profile_warning=True)
        registry, registry_errors = _registry(ws)
        _, document_errors, budget_warnings = _declared_documents(ws, registry)
        version_errors, version_notes = _versions(ws)
        handoff_errors, handoff_notes = _handoff(ws)
        fact_errors, fact_findings = canonical_fact_findings(root, registry)
        lifecycle = build_doc_lifecycle_report(root)
        lifecycle_errors = [f"doc-lifecycle:{f.code}:{f.path}: {f.message}" for f in lifecycle.findings
                            if f.severity in {"FAIL", "BLOCK"}]
        lifecycle_warnings = [f"doc-lifecycle:{f.code}:{f.path}: {f.message}" for f in lifecycle.findings
                              if f.severity not in {"FAIL", "BLOCK"}]
        fact_warnings = [f["message"] for f in fact_findings if f.get("severity") == "WARN"]
    except (OSError, ValueError, RuntimeError, yaml.YAMLError) as exc:
        return DocumentationSystemAuditReport((DocumentationAuditDimension(
            "Korrektheit", False, (f"Invalid external documentation contract: {exc}",)),), scope="external")

    def dimension(name: str, errors: list[str], warnings: list[str] | tuple[str, ...] = ()) -> DocumentationAuditDimension:
        return DocumentationAuditDimension(name, not errors, tuple(errors), tuple(warnings))

    return DocumentationSystemAuditReport((
        dimension("Aktualität", version_errors, [*version_notes, *budget_warnings]),
        dimension("Vollständigkeit", document_errors),
        dimension("Korrektheit", [*registry_errors, *fact_errors, *lifecycle_errors], lifecycle_warnings),
        DocumentationAuditDimension("Redundanzfreiheit", True, (),
                                    ("Semantic redundancy requires advisory review.",), review_only=True),
        dimension("Stringenz der Dokumentenordnung", handoff_errors, handoff_notes),
        dimension("Dokumentationsregistry", registry_errors,
                  [] if registry else ["No documentation registry declared; no Kit class inventory required."]),
        dimension("Konsistenz", [*version_errors, *fact_errors, *lifecycle_errors],
                  [*lifecycle_warnings, *fact_warnings]),
    ), scope="external")
