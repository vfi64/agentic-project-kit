from __future__ import annotations

import re
import shutil
import tempfile
from pathlib import Path
from typing import Any

import yaml

from agentic_project_kit.rule_registry_validator import (
    COVERAGE_PATH,
    INVENTORY_PATH,
    VALID_ASSERTION_KINDS,
    VALID_CATEGORY_PHASES,
    VALID_MECHANISM_CATEGORIES,
    VALID_ENFORCEMENT_PHASES,
    validate_rule_registry,
)


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def _write_yaml(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def _as_clean_list(values: list[str] | tuple[str, ...] | None) -> list[str]:
    return [str(value).strip() for value in values or () if str(value).strip()]


def _missing_required_fields(
    *,
    mechanism_id: str,
    owner: str,
    category: str,
    priority: int,
    enforcement_phase: str,
    conflict_domains: list[str],
    surfaces: list[str],
    source_path: str,
    required_terms: list[str],
    test_paths: list[str],
    protected_rule_intent: str,
    assertion_statement: str,
) -> list[str]:
    missing: list[str] = []
    if not mechanism_id:
        missing.append("id")
    if not owner:
        missing.append("owner")
    if category not in VALID_MECHANISM_CATEGORIES:
        missing.append("class")
    if not isinstance(priority, int) or priority < 1:
        missing.append("priority")
    if enforcement_phase not in VALID_ENFORCEMENT_PHASES:
        missing.append("enforcement_phase")
    if category in VALID_MECHANISM_CATEGORIES and enforcement_phase in VALID_ENFORCEMENT_PHASES:
        if (category, enforcement_phase) not in VALID_CATEGORY_PHASES:
            missing.append("class/enforcement_phase")
    if not conflict_domains:
        missing.append("conflict_domain")
    if not surfaces:
        missing.append("surface")
    if not source_path:
        missing.append("source")
    if not required_terms:
        missing.append("required_term")
    if not test_paths:
        missing.append("test")
    if not protected_rule_intent:
        missing.append("protected_rule_intent")
    if not assertion_statement:
        missing.append("assertion_statement")
    return missing


def _collect_referenced_paths(
    *,
    inventory: dict[str, Any],
    coverage: dict[str, Any],
    migrations: dict[str, Any],
) -> set[str]:
    paths: set[str] = set()
    for mechanism in inventory.get("mechanisms", []) or []:
        if not isinstance(mechanism, dict):
            continue
        for source in mechanism.get("sources", []) or []:
            if isinstance(source, dict) and str(source.get("path", "")).strip():
                paths.add(str(source["path"]).strip())
        for test_path in mechanism.get("tests", []) or []:
            if str(test_path).strip():
                paths.add(str(test_path).strip())
    for entry in coverage.get("coverage", []) or []:
        if not isinstance(entry, dict):
            continue
        for assertion in entry.get("assertions", []) or []:
            if not isinstance(assertion, dict):
                continue
            for ref in assertion.get("evidence_refs", []) or []:
                if isinstance(ref, dict) and str(ref.get("path", "")).strip():
                    paths.add(str(ref["path"]).strip())
    for migration in migrations.get("migrations", []) or []:
        if not isinstance(migration, dict):
            continue
        for evidence in migration.get("evidence", []) or []:
            if str(evidence).strip():
                paths.add(str(evidence).strip())
    return paths


def _mirror_referenced_paths(root: Path, tmp_root: Path, paths: set[str]) -> None:
    registry_paths = {INVENTORY_PATH.as_posix(), COVERAGE_PATH.as_posix(), ".agentic/rule_migrations.yaml"}
    for relative in sorted(paths):
        if relative in registry_paths or relative.startswith("/"):
            continue
        source = root / relative
        if not source.exists() or not source.is_file():
            continue
        target = tmp_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            target.symlink_to(source)
        except OSError:
            shutil.copy2(source, target)


def _validate_candidate_without_writing(
    root: Path,
    *,
    inventory: dict[str, Any],
    coverage: dict[str, Any],
) -> list[str]:
    migrations_path = root / ".agentic/rule_migrations.yaml"
    direct_plan_path = root / ".agentic/rule_direct_test_plan.yaml"
    migrations = _load_yaml(migrations_path)
    direct_plan = _load_yaml(direct_plan_path) if direct_plan_path.exists() else {}
    with tempfile.TemporaryDirectory(prefix="agentic-rule-registry-") as tmp:
        tmp_root = Path(tmp)
        _mirror_referenced_paths(
            root,
            tmp_root,
            _collect_referenced_paths(
                inventory=inventory,
                coverage=coverage,
                migrations=migrations,
            ),
        )
        _write_yaml(tmp_root / INVENTORY_PATH, inventory)
        _write_yaml(tmp_root / COVERAGE_PATH, coverage)
        _write_yaml(tmp_root / ".agentic/rule_migrations.yaml", migrations)
        if direct_plan:
            _write_yaml(tmp_root / ".agentic/rule_direct_test_plan.yaml", direct_plan)
        return [
            f"{finding.path}: {finding.message}"
            for finding in validate_rule_registry(tmp_root)
        ]


def _gate_relevant(category: str, enforcement_phase: str) -> bool:
    return category in {"governance", "workflow", "preflight"} or enforcement_phase in {"guard", "preflight"}


def _assertion_id(mechanism_id: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_-]+", "-", mechanism_id).strip("-")
    return f"{cleaned}-direct-coverage"


def register_rule_registry_entry(
    root: Path,
    *,
    mechanism_id: str,
    rule_class: str,
    owner: str,
    priority: int,
    enforcement_phase: str,
    conflict_domains: list[str] | tuple[str, ...] | None,
    surfaces: list[str] | tuple[str, ...] | None,
    source_path: str,
    required_terms: list[str] | tuple[str, ...] | None,
    test_paths: list[str] | tuple[str, ...] | None,
    protected_rule_intent: str,
    assertion_statement: str,
    assertion_kind: str = "guard",
) -> dict[str, Any]:
    mechanism_id = mechanism_id.strip()
    rule_class = rule_class.strip()
    owner = owner.strip()
    enforcement_phase = enforcement_phase.strip()
    conflict_domains_clean = _as_clean_list(conflict_domains)
    surfaces_clean = _as_clean_list(surfaces)
    source_path = source_path.strip()
    required_terms_clean = _as_clean_list(required_terms)
    test_paths_clean = _as_clean_list(test_paths)
    protected_rule_intent = protected_rule_intent.strip()
    assertion_statement = assertion_statement.strip()
    assertion_kind = assertion_kind.strip()

    base_payload: dict[str, Any] = {
        "schema_version": 1,
        "kind": "rule_registry_register_result",
        "result_status": "FAIL",
        "code": "FAIL_UNKNOWN",
        "id": mechanism_id,
        "class": rule_class,
        "owner": owner,
        "inventory_path": INVENTORY_PATH.as_posix(),
        "coverage_path": COVERAGE_PATH.as_posix(),
        "written": False,
        "gate_relevant": _gate_relevant(rule_class, enforcement_phase),
    }

    missing = _missing_required_fields(
        mechanism_id=mechanism_id,
        owner=owner,
        category=rule_class,
        priority=priority,
        enforcement_phase=enforcement_phase,
        conflict_domains=conflict_domains_clean,
        surfaces=surfaces_clean,
        source_path=source_path,
        required_terms=required_terms_clean,
        test_paths=test_paths_clean,
        protected_rule_intent=protected_rule_intent,
        assertion_statement=assertion_statement,
    )
    if assertion_kind not in VALID_ASSERTION_KINDS:
        missing.append("assertion_kind")
    if missing:
        return {
            **base_payload,
            "code": "FAIL_MISSING_RULE_FIELDS",
            "missing_fields": sorted(set(missing)),
            "allowed_classes": sorted(VALID_MECHANISM_CATEGORIES),
        }

    existing_findings = validate_rule_registry(root)
    if existing_findings:
        return {
            **base_payload,
            "code": "FAIL_INVALID_REGISTRY",
            "findings": [f"{finding.path}: {finding.message}" for finding in existing_findings],
        }

    inventory = _load_yaml(root / INVENTORY_PATH)
    coverage = _load_yaml(root / COVERAGE_PATH)
    mechanisms = inventory.get("mechanisms")
    coverage_entries = coverage.get("coverage")
    if not isinstance(mechanisms, list) or not isinstance(coverage_entries, list):
        return {
            **base_payload,
            "code": "FAIL_INVALID_REGISTRY",
            "findings": ["rule registry inventory and coverage must contain list entries"],
        }

    if any(isinstance(mechanism, dict) and mechanism.get("id") == mechanism_id for mechanism in mechanisms):
        return {**base_payload, "code": "FAIL_DUPLICATE_RULE_ID"}

    new_mechanism = {
        "id": mechanism_id,
        "status": "active",
        "owner": owner,
        "category": rule_class,
        "priority": priority,
        "enforcement_phase": enforcement_phase,
        "conflict_domains": conflict_domains_clean,
        "surfaces": surfaces_clean,
        "sources": [{"path": source_path, "required_terms": required_terms_clean}],
        "protected_rule_intent": protected_rule_intent,
        "tests": test_paths_clean,
    }
    new_coverage = {
        "mechanism_id": mechanism_id,
        "test_coverage": "direct",
        "assertions": [
            {
                "assertion_id": _assertion_id(mechanism_id),
                "kind": assertion_kind,
                "covered_surfaces": surfaces_clean,
                "evidence_refs": (
                    [{"kind": "source", "path": source_path}]
                    + [{"kind": "test", "path": path} for path in test_paths_clean]
                ),
                "statement": assertion_statement,
            }
        ],
    }

    candidate_inventory = dict(inventory)
    candidate_inventory["mechanisms"] = [*mechanisms, new_mechanism]
    candidate_coverage = dict(coverage)
    candidate_coverage["coverage"] = [*coverage_entries, new_coverage]
    candidate_findings = _validate_candidate_without_writing(
        root,
        inventory=candidate_inventory,
        coverage=candidate_coverage,
    )
    if candidate_findings:
        return {
            **base_payload,
            "code": "FAIL_VALIDATION",
            "findings": candidate_findings,
        }

    _write_yaml(root / INVENTORY_PATH, candidate_inventory)
    _write_yaml(root / COVERAGE_PATH, candidate_coverage)
    return {
        **base_payload,
        "result_status": "PASS",
        "code": "PASS",
        "written": True,
        "registered_paths": [INVENTORY_PATH.as_posix(), COVERAGE_PATH.as_posix()],
        "gate_participation_note": (
            "This rule participates in guard/preflight gate behavior; review its sources and tests."
            if _gate_relevant(rule_class, enforcement_phase)
            else "This rule is runtime-scoped; review its sources and tests."
        ),
    }
