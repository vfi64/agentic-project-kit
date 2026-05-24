from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

INVENTORY_PATH = Path(".agentic/rule_mechanism_inventory.yaml")
MIGRATIONS_PATH = Path(".agentic/rule_migrations.yaml")

@dataclass(frozen=True)
class RuleRegistryFinding:
    path: str
    message: str

def _load_yaml(path: Path) -> Any:
    if not path.exists():
        raise FileNotFoundError(path)
    return yaml.safe_load(path.read_text(encoding="utf-8"))

def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []

def validate_rule_registry(root: Path | str = ".") -> list[RuleRegistryFinding]:
    base = Path(root)
    inventory_path = base / INVENTORY_PATH
    migrations_path = base / MIGRATIONS_PATH
    findings: list[RuleRegistryFinding] = []
    try:
        inventory = _load_yaml(inventory_path)
    except Exception as exc:
        return [RuleRegistryFinding(str(INVENTORY_PATH), f"cannot load inventory: {exc}")]
    try:
        migrations = _load_yaml(migrations_path)
    except Exception as exc:
        return [RuleRegistryFinding(str(MIGRATIONS_PATH), f"cannot load migrations: {exc}")]
    if inventory.get("schema_version") != 1:
        findings.append(RuleRegistryFinding(str(INVENTORY_PATH), "schema_version must be 1"))
    if migrations.get("schema_version") != 1:
        findings.append(RuleRegistryFinding(str(MIGRATIONS_PATH), "schema_version must be 1"))
    mechanisms = _as_list(inventory.get("mechanisms"))
    mechanism_ids: set[str] = set()
    for mechanism in mechanisms:
        mid = str(mechanism.get("id", ""))
        if not mid:
            findings.append(RuleRegistryFinding(str(INVENTORY_PATH), "mechanism missing id"))
            continue
        if mid in mechanism_ids:
            findings.append(RuleRegistryFinding(str(INVENTORY_PATH), f"duplicate mechanism id: {mid}"))
        mechanism_ids.add(mid)
        if mechanism.get("status") != "active":
            findings.append(RuleRegistryFinding(str(INVENTORY_PATH), f"{mid}: status must be active"))
        if not str(mechanism.get("protected_rule_intent", "")).strip():
            findings.append(RuleRegistryFinding(str(INVENTORY_PATH), f"{mid}: missing protected_rule_intent"))
        for source in _as_list(mechanism.get("sources")):
            rel = str(source.get("path", ""))
            source_path = base / rel
            if not rel or not source_path.exists():
                findings.append(RuleRegistryFinding(str(INVENTORY_PATH), f"{mid}: missing source path: {rel}"))
                continue
            text = source_path.read_text(encoding="utf-8")
            for term in _as_list(source.get("required_terms")):
                if str(term) not in text:
                    findings.append(RuleRegistryFinding(rel, f"{mid}: required term missing: {term}"))
    legacy_ids: set[str] = set()
    for migration in _as_list(migrations.get("migrations")):
        legacy_id = str(migration.get("legacy_id", ""))
        if not legacy_id:
            findings.append(RuleRegistryFinding(str(MIGRATIONS_PATH), "migration missing legacy_id"))
            continue
        if legacy_id in legacy_ids:
            findings.append(RuleRegistryFinding(str(MIGRATIONS_PATH), f"duplicate legacy_id: {legacy_id}"))
        legacy_ids.add(legacy_id)
        if migration.get("status") != "migrated":
            findings.append(RuleRegistryFinding(str(MIGRATIONS_PATH), f"{legacy_id}: status must be migrated"))
        if migration.get("replaced_by") not in mechanism_ids:
            findings.append(RuleRegistryFinding(str(MIGRATIONS_PATH), f"{legacy_id}: replaced_by must reference an active mechanism"))
        if not str(migration.get("migration_reason", "")).strip():
            findings.append(RuleRegistryFinding(str(MIGRATIONS_PATH), f"{legacy_id}: missing migration_reason"))
        for evidence in _as_list(migration.get("evidence")):
            if not (base / str(evidence)).exists():
                findings.append(RuleRegistryFinding(str(MIGRATIONS_PATH), f"{legacy_id}: missing evidence path: {evidence}"))
    return findings

def render_rule_registry_findings(findings: list[RuleRegistryFinding]) -> str:
    if not findings:
        return "Rule registry validation passed"
    lines = ["Rule registry validation failed"]
    lines.extend(f"[HARD-FAIL] {finding.path}: {finding.message}" for finding in findings)
    return "\n".join(lines)
