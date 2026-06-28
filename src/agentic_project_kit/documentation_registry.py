from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

import yaml

REGISTRY_PATH = Path("docs/DOCUMENTATION_REGISTRY.yaml")
COMPILED_CONTEXT_PATH = Path(".agentic/compiled_agent_context.yaml")
REGISTRY_CONTRACT_PATH = Path("docs/governance/DOCUMENTATION_REGISTRY_CONTRACT.md")
COMMUNICATION_ARTIFACTS_PATH = Path(".agentic/communication_artifacts.yaml")

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

DOCUMENT_REGISTRATION_SCAN_SUFFIXES = frozenset({".md", ".yaml", ".yml"})
DOCUMENT_REGISTRATION_SCAN_ROOTS = (Path("docs"),)
DOCUMENT_REGISTRATION_EXCLUDED_PREFIXES = (
    "docs/reports/handoff-packages/",
    "docs/reports/terminal/",
    "docs/reports/transfer_runs/",
)


def load_documentation_registry(project_root: Path) -> dict[str, Any]:
    path = project_root / REGISTRY_PATH
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{REGISTRY_PATH}: root must be a mapping")
    return data


def load_communication_artifact_policy(project_root: Path) -> dict[str, Any]:
    path = project_root / COMMUNICATION_ARTIFACTS_PATH
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{COMMUNICATION_ARTIFACTS_PATH}: root must be a mapping")
    return data


def build_artifact_policy_summary(project_root: Path) -> dict[str, Any]:
    """Build a read-only summary of communication artifact policy.

    This intentionally consumes the machine-readable artifact policy without
    changing cleanup behavior. It is a small integration step between the
    documentation registry and the artifact retention policy.
    """
    try:
        policy = load_communication_artifact_policy(project_root)
    except FileNotFoundError:
        return {
            "policy_path": str(COMMUNICATION_ARTIFACTS_PATH),
            "present": False,
            "rule_count": 0,
            "delete_allowed_counts": {},
            "default_action_counts": {},
            "protected_rule_ids": [],
        }

    rules = policy.get("rules", [])
    if not isinstance(rules, list):
        rules = []

    delete_allowed_counts: Counter[str] = Counter()
    default_action_counts: Counter[str] = Counter()
    protected_rule_ids: list[str] = []
    for rule in rules:
        if not isinstance(rule, dict):
            continue
        delete_allowed = str(rule.get("delete_allowed", "<missing>")).strip() or "<missing>"
        default_action = str(rule.get("default_action", "<missing>")).strip() or "<missing>"
        rule_id = str(rule.get("id", "")).strip()
        delete_allowed_counts[delete_allowed] += 1
        default_action_counts[default_action] += 1
        if delete_allowed in {"false", "False"} or default_action in {"keep", "keep-or-repair"}:
            if rule_id:
                protected_rule_ids.append(rule_id)

    return {
        "policy_path": str(COMMUNICATION_ARTIFACTS_PATH),
        "present": True,
        "schema_version": policy.get("schema_version"),
        "rule_count": len(rules),
        "delete_allowed_counts": dict(sorted(delete_allowed_counts.items())),
        "default_action_counts": dict(sorted(default_action_counts.items())),
        "protected_rule_ids": sorted(protected_rule_ids),
    }


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
    registered_paths: set[str] = set()
    for entry in documents:
        if not isinstance(entry, dict):
            continue
        document_class = str(entry.get("class", "")).strip() or "<missing>"
        owner = str(entry.get("owner", "")).strip() or "<missing>"
        path = str(entry.get("path", "")).strip()
        if path:
            registered_paths.add(path)
        class_counts[document_class] += 1
        owner_counts[owner] += 1

    unregistered_candidates = find_unregistered_document_candidates(
        project_root,
        registered_paths=registered_paths,
    )

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
        "registration_policy": {
            "status": "inventory_only",
            "mutation_allowed": False,
            "next_step": (
                "Review unregistered candidates, classify them, then patch "
                "docs/DOCUMENTATION_REGISTRY.yaml explicitly through the normal PR lifecycle."
            ),
        },
        "unregistered_candidate_count": len(unregistered_candidates),
        "unregistered_candidates": unregistered_candidates,
        "artifact_policy": build_artifact_policy_summary(project_root),
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
    lines.extend(
        [
            "registration policy:",
            "- status: inventory_only",
            f"- unregistered_candidates: {summary.get('unregistered_candidate_count', 0)}",
        ]
    )

    artifact_policy = summary.get("artifact_policy", {})
    if isinstance(artifact_policy, dict) and artifact_policy.get("present"):
        lines.extend(
            [
                "artifact policy:",
                f"- policy: {artifact_policy['policy_path']}",
                f"- rules: {artifact_policy['rule_count']}",
                "- delete_allowed:",
            ]
        )
        delete_counts = artifact_policy.get("delete_allowed_counts", {})
        if isinstance(delete_counts, dict):
            for value, count in delete_counts.items():
                lines.append(f"  - {value}: {count}")
        lines.append("- protected rules:")
        protected = artifact_policy.get("protected_rule_ids", [])
        if isinstance(protected, list):
            for rule_id in protected:
                lines.append(f"  - {rule_id}")
    return "\n".join(lines)


def find_unregistered_document_candidates(
    project_root: Path,
    *,
    registered_paths: set[str] | None = None,
) -> list[str]:
    """Return document-like files that are not registered yet.

    This is intentionally inventory-only. It does not mutate the protected
    registry, because document classification still requires explicit review.
    """
    if registered_paths is None:
        try:
            registry = load_documentation_registry(project_root)
            documents = registry.get("documents", [])
            registered_paths = {
                str(entry.get("path", "")).strip()
                for entry in documents
                if isinstance(entry, dict) and str(entry.get("path", "")).strip()
            }
        except (FileNotFoundError, OSError, ValueError, yaml.YAMLError):
            registered_paths = set()
    candidates: list[str] = []
    for root in DOCUMENT_REGISTRATION_SCAN_ROOTS:
        scan_root = project_root / root
        if not scan_root.exists():
            continue
        for path in sorted(scan_root.rglob("*")):
            if not path.is_file() or path.is_symlink():
                continue
            if path.suffix.lower() not in DOCUMENT_REGISTRATION_SCAN_SUFFIXES:
                continue
            rel = path.relative_to(project_root).as_posix()
            if rel in registered_paths:
                continue
            if any(rel.startswith(prefix) for prefix in DOCUMENT_REGISTRATION_EXCLUDED_PREFIXES):
                continue
            candidates.append(rel)
    return candidates


def write_documentation_registry_summary_json(
    summary: dict[str, Any], report_path: Path
) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


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
