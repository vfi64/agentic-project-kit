from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

INVENTORY_PATH = Path(".agentic/rule_mechanism_inventory.yaml")
MIGRATIONS_PATH = Path(".agentic/rule_migrations.yaml")
VALID_MECHANISM_CATEGORIES = {"communication", "execution", "governance", "workflow", "preflight"}
VALID_ENFORCEMENT_PHASES = {"runtime", "guard", "preflight"}
VALID_CATEGORY_PHASES = {
    ("communication", "runtime"),
    ("execution", "runtime"),
    ("governance", "guard"),
    ("workflow", "guard"),
    ("preflight", "preflight"),
}
VALID_MIGRATION_STATUSES = {"migrated", "archived", "rejected"}
TERMINAL_MIGRATION_STATUSES = {"archived", "rejected"}
MIN_PRIORITY = 1
MAX_PRIORITY = 5

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


def _validate_string_list(
    *,
    value: Any,
    label: str,
    mechanism_id: str,
    required_non_empty: bool,
    findings: list[RuleRegistryFinding],
) -> list[str]:
    if not isinstance(value, list):
        findings.append(RuleRegistryFinding(str(INVENTORY_PATH), f"{mechanism_id}: {label} must be a list"))
        return []
    if required_non_empty and not value:
        findings.append(RuleRegistryFinding(str(INVENTORY_PATH), f"{mechanism_id}: {label} must list at least one entry"))
    entries: list[str] = []
    for item in value:
        text = str(item).strip()
        if not text:
            findings.append(RuleRegistryFinding(str(INVENTORY_PATH), f"{mechanism_id}: {label} entries must be non-empty strings"))
            continue
        entries.append(text)
    return entries


def _validate_mechanism_metadata(
    mechanism: dict[str, Any], mechanism_id: str, findings: list[RuleRegistryFinding]
) -> None:
    owner = mechanism.get("owner")
    if not isinstance(owner, str) or not owner.strip():
        findings.append(RuleRegistryFinding(str(INVENTORY_PATH), f"{mechanism_id}: owner must be a non-empty string"))
    category = mechanism.get("category")
    if category not in VALID_MECHANISM_CATEGORIES:
        findings.append(
            RuleRegistryFinding(
                str(INVENTORY_PATH),
                f"{mechanism_id}: category must be one of: {', '.join(sorted(VALID_MECHANISM_CATEGORIES))}",
            )
        )
    priority = mechanism.get("priority")
    if not isinstance(priority, int) or not MIN_PRIORITY <= priority <= MAX_PRIORITY:
        findings.append(
            RuleRegistryFinding(
                str(INVENTORY_PATH),
                f"{mechanism_id}: priority must be an integer from {MIN_PRIORITY} to {MAX_PRIORITY}",
            )
        )
    enforcement_phase = mechanism.get("enforcement_phase")
    if enforcement_phase not in VALID_ENFORCEMENT_PHASES:
        findings.append(
            RuleRegistryFinding(
                str(INVENTORY_PATH),
                f"{mechanism_id}: enforcement_phase must be one of: {', '.join(sorted(VALID_ENFORCEMENT_PHASES))}",
            )
        )
    if (
        category in VALID_MECHANISM_CATEGORIES
        and enforcement_phase in VALID_ENFORCEMENT_PHASES
        and (category, enforcement_phase) not in VALID_CATEGORY_PHASES
    ):
        findings.append(
            RuleRegistryFinding(
                str(INVENTORY_PATH),
                f"{mechanism_id}: incompatible category/enforcement_phase combination: {category}/{enforcement_phase}",
            )
        )

def _validate_mechanism_conflicts(mechanisms: list[Any], findings: list[RuleRegistryFinding]) -> None:
    seen: dict[tuple[str, int, str], str] = {}
    for mechanism in mechanisms:
        if not isinstance(mechanism, dict) or mechanism.get("status") != "active":
            continue
        mechanism_id = str(mechanism.get("id", ""))
        priority = mechanism.get("priority")
        enforcement_phase = mechanism.get("enforcement_phase")
        conflict_domains = _as_list(mechanism.get("conflict_domains"))
        if (
            not isinstance(priority, int)
            or not MIN_PRIORITY <= priority <= MAX_PRIORITY
            or enforcement_phase not in VALID_ENFORCEMENT_PHASES
        ):
            continue
        for domain in conflict_domains:
            domain_text = str(domain).strip()
            if not domain_text:
                continue
            key = (domain_text, priority, str(enforcement_phase))
            previous = seen.get(key)
            if previous is not None:
                findings.append(
                    RuleRegistryFinding(
                        str(INVENTORY_PATH),
                        f"ambiguous enforcement order: {previous} and {mechanism_id} share conflict_domain={domain_text}, priority={priority}, enforcement_phase={enforcement_phase}",
                    )
                )
            else:
                seen[key] = mechanism_id

def _validate_migration_completeness(
    migrations: dict[str, Any], legacy_ids: set[str], findings: list[RuleRegistryFinding]
) -> None:
    known_legacy_rule_ids = {str(item) for item in _as_list(migrations.get("known_legacy_rule_ids"))}
    if not known_legacy_rule_ids:
        findings.append(
            RuleRegistryFinding(
                str(MIGRATIONS_PATH),
                "known_legacy_rule_ids must list every known legacy rule id",
            )
        )
        return
    missing = sorted(known_legacy_rule_ids - legacy_ids)
    extra = sorted(legacy_ids - known_legacy_rule_ids)
    for legacy_id in missing:
        findings.append(
            RuleRegistryFinding(
                str(MIGRATIONS_PATH),
                f"known legacy rule missing migration entry: {legacy_id}",
            )
        )
    for legacy_id in extra:
        findings.append(
            RuleRegistryFinding(
                str(MIGRATIONS_PATH),
                f"migration entry missing from known legacy rule index: {legacy_id}",
            )
        )

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
        _validate_mechanism_metadata(mechanism, mid, findings)
        _validate_string_list(
            value=mechanism.get("conflict_domains"),
            label="conflict_domains",
            mechanism_id=mid,
            required_non_empty=True,
            findings=findings,
        )
        _validate_string_list(
            value=mechanism.get("surfaces"),
            label="surfaces",
            mechanism_id=mid,
            required_non_empty=True,
            findings=findings,
        )
        tests = _validate_string_list(
            value=mechanism.get("tests"),
            label="tests",
            mechanism_id=mid,
            required_non_empty=False,
            findings=findings,
        )
        for test_path in tests:
            if not (base / test_path).exists():
                findings.append(RuleRegistryFinding(str(INVENTORY_PATH), f"{mid}: missing test path: {test_path}"))
        if not str(mechanism.get("protected_rule_intent", "")).strip():
            findings.append(RuleRegistryFinding(str(INVENTORY_PATH), f"{mid}: missing protected_rule_intent"))
        sources = _as_list(mechanism.get("sources"))
        if not sources:
            findings.append(RuleRegistryFinding(str(INVENTORY_PATH), f"{mid}: sources must list at least one source"))
        for source in sources:
            if not isinstance(source, dict):
                findings.append(RuleRegistryFinding(str(INVENTORY_PATH), f"{mid}: source entry must be a mapping"))
                continue
            rel = str(source.get("path", ""))
            required_terms = _as_list(source.get("required_terms"))
            if not required_terms:
                label = rel if rel else "<missing path>"
                findings.append(
                    RuleRegistryFinding(
                        str(INVENTORY_PATH),
                        f"{mid}: source {label} must list at least one required_terms entry",
                    )
                )
            source_path = base / rel
            if not rel or not source_path.exists():
                findings.append(RuleRegistryFinding(str(INVENTORY_PATH), f"{mid}: missing source path: {rel}"))
                continue
            text = source_path.read_text(encoding="utf-8")
            for term in required_terms:
                if str(term) not in text:
                    findings.append(RuleRegistryFinding(rel, f"{mid}: required term missing: {term}"))
    _validate_mechanism_conflicts(mechanisms, findings)
    legacy_ids: set[str] = set()
    for migration in _as_list(migrations.get("migrations")):
        legacy_id = str(migration.get("legacy_id", ""))
        if not legacy_id:
            findings.append(RuleRegistryFinding(str(MIGRATIONS_PATH), "migration missing legacy_id"))
            continue
        if legacy_id in legacy_ids:
            findings.append(RuleRegistryFinding(str(MIGRATIONS_PATH), f"duplicate legacy_id: {legacy_id}"))
        legacy_ids.add(legacy_id)
        status = migration.get("status")
        if status not in VALID_MIGRATION_STATUSES:
            findings.append(
                RuleRegistryFinding(
                    str(MIGRATIONS_PATH),
                    f"{legacy_id}: status must be one of: {', '.join(sorted(VALID_MIGRATION_STATUSES))}",
                )
            )
        if status == "migrated" and migration.get("replaced_by") not in mechanism_ids:
            findings.append(RuleRegistryFinding(str(MIGRATIONS_PATH), f"{legacy_id}: replaced_by must reference an active mechanism"))
        if status in TERMINAL_MIGRATION_STATUSES and migration.get("replaced_by"):
            findings.append(
                RuleRegistryFinding(
                    str(MIGRATIONS_PATH),
                    f"{legacy_id}: terminal migration status must not set replaced_by",
                )
            )
        if not str(migration.get("migration_reason", "")).strip():
            findings.append(RuleRegistryFinding(str(MIGRATIONS_PATH), f"{legacy_id}: missing migration_reason"))
        evidence_entries = _as_list(migration.get("evidence"))
        if not evidence_entries:
            findings.append(
                RuleRegistryFinding(
                    str(MIGRATIONS_PATH),
                    f"{legacy_id}: evidence must list at least one evidence path",
                )
            )
        for evidence in evidence_entries:
            if not (base / str(evidence)).exists():
                findings.append(RuleRegistryFinding(str(MIGRATIONS_PATH), f"{legacy_id}: missing evidence path: {evidence}"))
    _validate_migration_completeness(migrations, legacy_ids, findings)
    return findings

def render_rule_registry_findings(findings: list[RuleRegistryFinding]) -> str:
    if not findings:
        return "Rule registry validation passed"
    lines = ["Rule registry validation failed"]
    lines.extend(f"[HARD-FAIL] {finding.path}: {finding.message}" for finding in findings)
    return "\n".join(lines)
