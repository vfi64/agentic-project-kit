from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

import yaml

REGISTRY_PATH = Path("docs/DOCUMENTATION_REGISTRY.yaml")
COMPILED_CONTEXT_PATH = Path(".agentic/compiled_agent_context.yaml")
REGISTRY_CONTRACT_PATH = Path("docs/governance/DOCUMENTATION_REGISTRY_CONTRACT.md")

DOCUMENT_CLASSES = (
    "governance/system",
    "planning",
    "architecture",
    "release",
    "operational/automation",
    "user-facing description",
    "evidence/log",
    "generated artifact",
    "temporary artifact",
    "historical archive",
)

REQUIRED_CLASS_RULE_FIELDS = (
    "ownership",
    "freshness",
    "language_policy",
    "redundancy_boundary",
    "machine_readability",
    "retention_gc_behavior",
    "update_triggers",
    "portability_local_path_scanning",
    "gate_coverage",
)

REQUIRED_DOCUMENT_FIELDS = (
    "path",
    "class",
    "owner",
)


def load_documentation_registry(project_root: Path) -> dict[str, Any]:
    path = project_root / REGISTRY_PATH
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{REGISTRY_PATH}: root must be a mapping")
    return data


def build_documentation_registry_summary(project_root: Path) -> dict[str, Any]:
    """Build a read-only summary for the documentation registry.

    This summary is intentionally non-mutating. It is a narrow second-slice
    consumer that makes the registry inspectable without starting a broad
    migration or changing any document lifecycle policy.
    """
    registry = load_documentation_registry(project_root)
    documents = registry.get("documents", [])
    if not isinstance(documents, list):
        documents = []

    class_counts: Counter[str] = Counter()
    owner_counts: Counter[str] = Counter()
    for entry in documents:
        if not isinstance(entry, dict):
            continue
        document_class = str(entry.get("class", "")).strip() or "<missing>"
        owner = str(entry.get("owner", "")).strip() or "<missing>"
        class_counts[document_class] += 1
        owner_counts[owner] += 1

    return {
        "registry_path": str(REGISTRY_PATH),
        "version": registry.get("version"),
        "lifecycle": (registry.get("status") or {}).get("lifecycle")
        if isinstance(registry.get("status"), dict)
        else None,
        "broad_migration_allowed": (registry.get("status") or {}).get(
            "broad_migration_allowed"
        )
        if isinstance(registry.get("status"), dict)
        else None,
        "document_count": len(documents),
        "class_counts": dict(sorted(class_counts.items())),
        "owner_counts": dict(sorted(owner_counts.items())),
    }


def render_documentation_registry_summary(summary: dict[str, Any]) -> str:
    lines = [
        "Documentation registry summary",
        f"registry: {summary['registry_path']}",
        f"version: {summary['version']}",
        f"lifecycle: {summary['lifecycle']}",
        f"broad_migration_allowed: {summary['broad_migration_allowed']}",
        f"documents: {summary['document_count']}",
        "classes:",
    ]
    class_counts = summary.get("class_counts", {})
    if isinstance(class_counts, dict):
        for class_name, count in class_counts.items():
            lines.append(f"- {class_name}: {count}")
    lines.append("owners:")
    owner_counts = summary.get("owner_counts", {})
    if isinstance(owner_counts, dict):
        for owner, count in owner_counts.items():
            lines.append(f"- {owner}: {count}")
    return "\n".join(lines)


def check_documentation_registry(project_root: Path) -> list[str]:
    registry_file = project_root / REGISTRY_PATH
    if not registry_file.exists():
        if _registry_required(project_root):
            return [f"Missing documentation registry: {REGISTRY_PATH}"]
        return []

    try:
        registry = load_documentation_registry(project_root)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        return [f"{REGISTRY_PATH}: invalid registry ({exc})"]

    errors: list[str] = []
    if registry.get("version") != 1:
        errors.append(f"{REGISTRY_PATH}: version must be 1")

    errors.extend(_check_class_rules(registry))
    errors.extend(_check_document_entries(project_root, registry))
    return errors


def _registry_required(project_root: Path) -> bool:
    if (project_root / REGISTRY_CONTRACT_PATH).exists():
        return True
    compiled_context = project_root / COMPILED_CONTEXT_PATH
    if not compiled_context.exists():
        return False
    try:
        context = yaml.safe_load(compiled_context.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        return True
    return str(REGISTRY_PATH) in str(context)


def _check_class_rules(registry: dict[str, Any]) -> list[str]:
    class_rules = registry.get("class_rules")
    if not isinstance(class_rules, dict):
        return [f"{REGISTRY_PATH}: class_rules must be a mapping"]

    errors: list[str] = []
    allowed = set(DOCUMENT_CLASSES)
    present = set(str(name) for name in class_rules)
    for missing in sorted(allowed - present):
        errors.append(f"{REGISTRY_PATH}: missing class rule for {missing!r}")
    for unknown in sorted(present - allowed):
        errors.append(f"{REGISTRY_PATH}: unknown document class {unknown!r}")

    for class_name in DOCUMENT_CLASSES:
        rules = class_rules.get(class_name)
        if not isinstance(rules, dict):
            continue
        for field in REQUIRED_CLASS_RULE_FIELDS:
            value = rules.get(field)
            if value in (None, "", []):
                errors.append(
                    f"{REGISTRY_PATH}: {class_name!r} "
                    f"missing class rule field {field!r}"
                )

    return errors


def _check_document_entries(project_root: Path, registry: dict[str, Any]) -> list[str]:
    documents = registry.get("documents")
    if not isinstance(documents, list) or not documents:
        return [f"{REGISTRY_PATH}: documents must be a non-empty list"]

    errors: list[str] = []
    seen_paths: set[str] = set()
    allowed = set(DOCUMENT_CLASSES)

    for index, entry in enumerate(documents, start=1):
        if not isinstance(entry, dict):
            errors.append(f"{REGISTRY_PATH}: document entry {index} must be a mapping")
            continue

        for field in REQUIRED_DOCUMENT_FIELDS:
            if not str(entry.get(field, "")).strip():
                errors.append(f"{REGISTRY_PATH}: document entry {index} missing field {field!r}")

        relative_path = str(entry.get("path", "")).strip()
        document_class = str(entry.get("class", "")).strip()
        if document_class and document_class not in allowed:
            errors.append(
                f"{REGISTRY_PATH}: {relative_path or index} "
                f"has unknown class {document_class!r}"
            )

        if relative_path:
            if relative_path in seen_paths:
                errors.append(f"{REGISTRY_PATH}: duplicate document path {relative_path!r}")
            seen_paths.add(relative_path)
            if not (project_root / relative_path).exists():
                errors.append(
                    f"{REGISTRY_PATH}: registered document does not exist: {relative_path}"
                )

    return errors
