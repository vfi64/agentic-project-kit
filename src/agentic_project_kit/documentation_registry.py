from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

REGISTRY_PATH = Path("docs/DOCUMENTATION_REGISTRY.yaml")

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
    """Load the additive documentation registry schema file."""
    path = project_root / REGISTRY_PATH
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{REGISTRY_PATH}: root must be a mapping")
    return data


def check_documentation_registry(project_root: Path) -> list[str]:
    """Return deterministic documentation registry schema findings.

    This first guard validates only structural, machine-checkable registry rules.
    It does not migrate documents and does not claim semantic documentation quality.
    """
    registry_file = project_root / REGISTRY_PATH
    if not registry_file.exists():
        return [f"Missing documentation registry: {REGISTRY_PATH}"]

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
                errors.append(f"{REGISTRY_PATH}: {class_name!r} missing class rule field {field!r}")

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
            errors.append(f"{REGISTRY_PATH}: {relative_path or index} has unknown class {document_class!r}")

        if relative_path:
            if relative_path in seen_paths:
                errors.append(f"{REGISTRY_PATH}: duplicate document path {relative_path!r}")
            seen_paths.add(relative_path)
            if not (project_root / relative_path).exists():
                errors.append(f"{REGISTRY_PATH}: registered document does not exist: {relative_path}")

    return errors
