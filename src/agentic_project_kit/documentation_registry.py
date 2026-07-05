from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from fnmatch import fnmatchcase
from pathlib import Path
from typing import Any

import yaml

REGISTRY_PATH = Path("docs/DOCUMENTATION_REGISTRY.yaml")
SCOPE_PATH = Path("docs/DOC_REGISTRY_SCOPE.yaml")
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
SCOPE_REQUIRED_SUFFIXES = frozenset({".md"})


@dataclass(frozen=True)
class ScopeExemption:
    path: str
    reason: str


@dataclass(frozen=True)
class DocumentationRegistryScope:
    present: bool
    required_files: tuple[str, ...]
    required_paths: tuple[str, ...]
    exempt_paths: tuple[ScopeExemption, ...]
    errors: tuple[str, ...] = ()


def load_documentation_registry(project_root: Path) -> dict[str, Any]:
    path = project_root / REGISTRY_PATH
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{REGISTRY_PATH}: root must be a mapping")
    return data


def load_documentation_registry_scope(project_root: Path) -> DocumentationRegistryScope:
    path = project_root / SCOPE_PATH
    if not path.exists():
        return DocumentationRegistryScope(
            present=False,
            required_files=(),
            required_paths=(),
            exempt_paths=(),
        )

    errors: list[str] = []
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        return DocumentationRegistryScope(
            present=True,
            required_files=(),
            required_paths=(),
            exempt_paths=(),
            errors=(f"{SCOPE_PATH}: invalid scope ({exc})",),
        )

    if data is None:
        data = {}
    if not isinstance(data, dict):
        return DocumentationRegistryScope(
            present=True,
            required_files=(),
            required_paths=(),
            exempt_paths=(),
            errors=(f"{SCOPE_PATH}: root must be a mapping",),
        )

    if data.get("schema_version") != 1:
        errors.append(f"{SCOPE_PATH}: schema_version must be 1")

    required_files = _parse_scope_required_files(data.get("required_files"), errors)
    required_paths = _parse_scope_required_paths(data.get("required_paths"), errors)
    exempt_paths = _parse_scope_exempt_paths(data.get("exempt_paths"), errors)
    return DocumentationRegistryScope(
        present=True,
        required_files=tuple(required_files),
        required_paths=tuple(required_paths),
        exempt_paths=tuple(exempt_paths),
        errors=tuple(errors),
    )


def check_documentation_registry_scope(project_root: Path) -> list[str]:
    scope = load_documentation_registry_scope(project_root)
    return list(scope.errors)


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
            "status": "reviewed_register_command_available",
            "mutation_allowed": True,
            "allowed_command": "agentic-kit doc-registry register",
            "next_step": (
                "Review unregistered candidates, classify them, then register one explicit "
                "path/class entry through the normal PR lifecycle."
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
            "- status: reviewed_register_command_available",
            "- mutation_allowed: True",
            "- allowed_command: agentic-kit doc-registry register",
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


def documentation_registry_findings_for_data(
    project_root: Path,
    registry: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    if registry.get("version") != 1:
        errors.append(f"{REGISTRY_PATH}: version must be 1")

    errors.extend(_check_class_rules(registry))
    errors.extend(_check_document_entries(project_root, registry))
    return errors


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

    return documentation_registry_findings_for_data(project_root, registry) + (
        check_documentation_registry_scope(project_root)
    )


def register_documentation_registry_entry(
    project_root: Path,
    *,
    document_path: str,
    document_class: str,
    owner: str = "maintainers",
) -> dict[str, Any]:
    normalized_path = document_path.strip().lstrip("./")
    normalized_class = document_class.strip()
    normalized_owner = owner.strip() or "maintainers"
    base_payload: dict[str, Any] = {
        "schema_version": 1,
        "kind": "documentation_registry_register_result",
        "registry_path": REGISTRY_PATH.as_posix(),
        "path": normalized_path,
        "class": normalized_class,
        "owner": normalized_owner,
        "written": False,
    }

    registry = load_documentation_registry(project_root)
    existing_findings = documentation_registry_findings_for_data(project_root, registry)
    if existing_findings:
        return {
            **base_payload,
            "result_status": "FAIL",
            "code": "FAIL_INVALID_REGISTRY",
            "findings": existing_findings,
        }

    allowed_classes = set(DOCUMENT_CLASSES)
    if normalized_class not in allowed_classes:
        return {
            **base_payload,
            "result_status": "FAIL",
            "code": "FAIL_UNKNOWN_CLASS",
            "allowed_classes": sorted(allowed_classes),
        }

    if not normalized_path or not (project_root / normalized_path).exists():
        return {
            **base_payload,
            "result_status": "FAIL",
            "code": "FAIL_PATH_NOT_FOUND",
        }

    documents = registry.get("documents")
    if not isinstance(documents, list):
        return {
            **base_payload,
            "result_status": "FAIL",
            "code": "FAIL_INVALID_REGISTRY",
            "findings": [f"{REGISTRY_PATH}: documents must be a list"],
        }

    registered_paths = {
        str(entry.get("path", "")).strip()
        for entry in documents
        if isinstance(entry, dict)
    }
    if normalized_path in registered_paths:
        return {
            **base_payload,
            "result_status": "FAIL",
            "code": "FAIL_DUPLICATE_PATH",
        }

    candidate_registry = dict(registry)
    candidate_documents = list(documents)
    candidate_documents.append(
        {
            "path": normalized_path,
            "class": normalized_class,
            "owner": normalized_owner,
        }
    )
    candidate_registry["documents"] = candidate_documents
    candidate_findings = documentation_registry_findings_for_data(
        project_root,
        candidate_registry,
    )
    if candidate_findings:
        return {
            **base_payload,
            "result_status": "FAIL",
            "code": "FAIL_VALIDATION",
            "findings": candidate_findings,
        }

    registry_path = project_root / REGISTRY_PATH
    registry_path.write_text(
        yaml.safe_dump(candidate_registry, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    return {
        **base_payload,
        "result_status": "PASS",
        "code": "PASS",
        "written": True,
    }


def build_unregistered_document_candidates_report(
    project_root: Path,
    *,
    strict_scope: bool = False,
) -> dict[str, Any]:
    scope = load_documentation_registry_scope(project_root)
    candidates = find_unregistered_document_candidates(project_root)
    candidates, exempted_count = _filter_exempt_candidates(candidates, scope)
    scope_violations = _find_scope_violations(project_root, scope)
    if scope.errors:
        result_status = "FAIL"
        next_action = "Repair docs/DOC_REGISTRY_SCOPE.yaml before checking registry scope."
    elif strict_scope and scope_violations:
        result_status = "FAIL"
        next_action = "Register or exempt unregistered files in required documentation scope paths."
    elif candidates or scope_violations:
        result_status = "WARN"
        next_action = "Review and classify candidates before registering explicit entries."
    else:
        result_status = "PASS"
        next_action = "No unregistered document candidates found."
    return {
        "schema_version": 1,
        "kind": "documentation_registry_unregistered_candidates",
        "registry_path": REGISTRY_PATH.as_posix(),
        "scope_path": SCOPE_PATH.as_posix(),
        "result_status": result_status,
        "final_signal": "d",
        "strict_scope": strict_scope,
        "scope_present": scope.present,
        "scope_required_file_count": len(scope.required_files),
        "scope_required_path_count": len(scope.required_paths),
        "scope_exempt_path_count": len(scope.exempt_paths),
        "scope_errors": list(scope.errors),
        "exempted_count": exempted_count,
        "scope_violation_count": len(scope_violations),
        "scope_violations": scope_violations,
        "candidate_count": len(candidates),
        "candidates": candidates,
        "next_action": next_action,
    }


def build_doc_registry_scope_decision_rows(project_root: Path) -> list[dict[str, int | str]]:
    registered_paths = _registered_document_paths(project_root)
    counters: dict[str, Counter[str]] = {}
    for rel in _iter_docs_markdown_files(
        project_root,
        excluded_prefixes=DOCUMENT_REGISTRATION_EXCLUDED_PREFIXES,
    ):
        group = _docs_subdirectory_group(rel)
        bucket = counters.setdefault(group, Counter())
        bucket["md_files"] += 1
        if rel in registered_paths:
            bucket["registered"] += 1
        else:
            bucket["unregistered"] += 1

    return [
        {
            "docs_path": group,
            "md_files": counters[group]["md_files"],
            "registered": counters[group]["registered"],
            "unregistered": counters[group]["unregistered"],
        }
        for group in sorted(counters, key=lambda value: ("0" if value == "docs/" else value))
    ]


def render_doc_registry_scope_decision_template(project_root: Path) -> str:
    rows = build_doc_registry_scope_decision_rows(project_root)
    lines = [
        "# Documentation Registry Scope Decision Template",
        "",
        "Status: active",
        "Decision status: undecided",
        "Review policy: required",
        "",
        "Generated from the current repository filesystem and `docs/DOCUMENTATION_REGISTRY.yaml`.",
        "Counts exclude generated report prefixes that are already outside the registry candidate scan.",
        "No scope recommendation is encoded here; maintainers fill the proposed column after review.",
        "",
        "| docs path | md files | registered | unregistered | proposed: required / exempt / undecided |",
        "|---|---:|---:|---:|---|",
    ]
    for row in rows:
        lines.append(
            "| {docs_path} | {md_files} | {registered} | {unregistered} |  |".format(
                **row
            )
        )
    lines.extend(
        [
            "",
            "Notes:",
            "- `required_files` means each declared file must have a registry entry.",
            "- `required_paths` means every Markdown file in that declared path must be registered.",
            "- `exempt_paths` means a declared path is intentionally registration-free and must carry a reason.",
            "- This template is evidence for a maintainer decision; it does not modify scope by itself.",
        ]
    )
    return "\n".join(lines) + "\n"


def _parse_scope_required_paths(value: object, errors: list[str]) -> list[str]:
    if value in (None, []):
        return []
    if not isinstance(value, list):
        errors.append(f"{SCOPE_PATH}: required_paths must be a list")
        return []

    required_paths: list[str] = []
    for index, item in enumerate(value, start=1):
        if not isinstance(item, str):
            errors.append(f"{SCOPE_PATH}: required_paths entry {index} must be a string")
            continue
        normalized = _normalize_scope_pattern(item)
        if not normalized:
            errors.append(f"{SCOPE_PATH}: required_paths entry {index} must not be empty")
            continue
        if _scope_pattern_is_unsafe(normalized):
            errors.append(f"{SCOPE_PATH}: required_paths entry {index} is not repository-relative")
            continue
        required_paths.append(normalized)
    return required_paths


def _parse_scope_required_files(value: object, errors: list[str]) -> list[str]:
    if value in (None, []):
        return []
    if not isinstance(value, list):
        errors.append(f"{SCOPE_PATH}: required_files must be a list")
        return []
    required_files: list[str] = []
    for index, entry in enumerate(value, start=1):
        if not isinstance(entry, str):
            errors.append(f"{SCOPE_PATH}: required_files entry {index} must be a string")
            continue
        normalized = _normalize_scope_pattern(entry)
        if not normalized:
            errors.append(f"{SCOPE_PATH}: required_files entry {index} must not be empty")
            continue
        if _scope_pattern_is_unsafe(normalized):
            errors.append(f"{SCOPE_PATH}: required_files entry {index} is not repository-relative")
            continue
        if normalized.endswith("/"):
            errors.append(f"{SCOPE_PATH}: required_files entry {index} must be a file path")
            continue
        required_files.append(normalized)
    return required_files


def _parse_scope_exempt_paths(value: object, errors: list[str]) -> list[ScopeExemption]:
    if value in (None, []):
        return []
    if not isinstance(value, list):
        errors.append(f"{SCOPE_PATH}: exempt_paths must be a list")
        return []

    exempt_paths: list[ScopeExemption] = []
    for index, item in enumerate(value, start=1):
        if not isinstance(item, dict):
            errors.append(f"{SCOPE_PATH}: exempt_paths entry {index} must be a mapping")
            continue
        raw_path = item.get("path")
        raw_reason = item.get("reason")
        path = _normalize_scope_pattern(raw_path) if isinstance(raw_path, str) else ""
        reason = raw_reason.strip() if isinstance(raw_reason, str) else ""
        if not path:
            errors.append(f"{SCOPE_PATH}: exempt_paths entry {index} missing path")
            continue
        if _scope_pattern_is_unsafe(path):
            errors.append(f"{SCOPE_PATH}: exempt_paths entry {index} path is not repository-relative")
            continue
        if not reason:
            errors.append(f"{SCOPE_PATH}: exempt_paths entry {index} missing reason")
            continue
        exempt_paths.append(ScopeExemption(path=path, reason=reason))
    return exempt_paths


def _normalize_scope_pattern(value: str) -> str:
    return value.strip().replace("\\", "/").lstrip("./")


def _scope_pattern_is_unsafe(pattern: str) -> bool:
    return pattern.startswith("/") or any(part == ".." for part in pattern.split("/"))


def _registered_document_paths(project_root: Path) -> set[str]:
    try:
        registry = load_documentation_registry(project_root)
    except (FileNotFoundError, OSError, ValueError, yaml.YAMLError):
        return set()
    documents = registry.get("documents", [])
    if not isinstance(documents, list):
        return set()
    return {
        str(entry.get("path", "")).strip()
        for entry in documents
        if isinstance(entry, dict) and str(entry.get("path", "")).strip()
    }


def _filter_exempt_candidates(
    candidates: list[str],
    scope: DocumentationRegistryScope,
) -> tuple[list[str], int]:
    if scope.errors or not scope.exempt_paths:
        return candidates, 0
    filtered = [
        candidate
        for candidate in candidates
        if not _matches_any_scope_pattern(candidate, [exemption.path for exemption in scope.exempt_paths])
    ]
    return filtered, len(candidates) - len(filtered)


def _find_scope_violations(
    project_root: Path,
    scope: DocumentationRegistryScope,
) -> list[str]:
    if scope.errors or (not scope.required_files and not scope.required_paths):
        return []
    registered_paths = _registered_document_paths(project_root)
    exempt_patterns = [exemption.path for exemption in scope.exempt_paths]
    violations = []
    for rel in scope.required_files:
        if rel in registered_paths:
            continue
        if exempt_patterns and _matches_any_scope_pattern(rel, exempt_patterns):
            continue
        violations.append(rel)
    for rel in _iter_docs_markdown_files(project_root):
        if rel in registered_paths:
            continue
        if exempt_patterns and _matches_any_scope_pattern(rel, exempt_patterns):
            continue
        if _matches_any_scope_pattern(rel, scope.required_paths):
            violations.append(rel)
    return sorted(set(violations))


def _iter_docs_markdown_files(
    project_root: Path,
    *,
    excluded_prefixes: tuple[str, ...] = (),
) -> list[str]:
    docs_root = project_root / "docs"
    if not docs_root.exists():
        return []
    result: list[str] = []
    for path in sorted(docs_root.rglob("*")):
        if not path.is_file() or path.is_symlink():
            continue
        if path.suffix.lower() not in SCOPE_REQUIRED_SUFFIXES:
            continue
        rel = path.relative_to(project_root).as_posix()
        if any(rel.startswith(prefix) for prefix in excluded_prefixes):
            continue
        result.append(rel)
    return result


def _docs_subdirectory_group(relative_path: str) -> str:
    parts = relative_path.split("/")
    if len(parts) < 3:
        return "docs/"
    return f"docs/{parts[1]}/"


def _matches_any_scope_pattern(path: str, patterns: list[str] | tuple[str, ...]) -> bool:
    return any(_matches_scope_pattern(path, pattern) for pattern in patterns)


def _matches_scope_pattern(path: str, pattern: str) -> bool:
    if any(token in pattern for token in "*?["):
        return fnmatchcase(path, pattern)
    if pattern.endswith("/"):
        return path.startswith(pattern)
    return path == pattern or path.startswith(f"{pattern}/")


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
