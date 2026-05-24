from pathlib import Path

import yaml
from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.rule_registry_validator import validate_rule_registry


def _valid_mechanism() -> dict[str, object]:
    return {
        "id": "m",
        "status": "active",
        "owner": "validator-owner",
        "category": "governance",
        "priority": 1,
        "enforcement_phase": "guard",
        "conflict_domains": ["validator-conflict-domain"],
        "surfaces": ["validator-test-surface"],
        "tests": [],
        "protected_rule_intent": "intent",
        "sources": [
            {"path": "source.txt", "required_terms": ["present"]},
        ],
    }


def _valid_migration(replaced_by: str = "m") -> dict[str, object]:
    return {
        "legacy_id": "old",
        "status": "migrated",
        "replaced_by": replaced_by,
        "evidence": ["evidence.txt"],
        "migration_reason": "reason",
    }


def _write_registry(
    tmp_path: Path,
    mechanism: dict[str, object],
    replaced_by: str = "m",
    extra_mechanisms: list[dict[str, object]] | None = None,
    migrations_override: list[dict[str, object]] | None = None,
    known_legacy_rule_ids: list[str] | None = None,
) -> None:
    source = tmp_path / "source.txt"
    source.write_text("present", encoding="utf-8")
    evidence = tmp_path / "evidence.txt"
    evidence.write_text("evidence", encoding="utf-8")
    agentic = tmp_path / ".agentic"
    agentic.mkdir()
    mechanisms = [mechanism]
    if extra_mechanisms:
        mechanisms.extend(extra_mechanisms)
    migrations = migrations_override if migrations_override is not None else [_valid_migration(replaced_by)]
    if known_legacy_rule_ids is None:
        known_legacy_rule_ids = [str(item["legacy_id"]) for item in migrations]
    inventory = {
        "schema_version": 1,
        "mechanisms": mechanisms,
    }
    migrations_data = {
        "schema_version": 1,
        "known_legacy_rule_ids": known_legacy_rule_ids,
        "migrations": migrations,
    }
    (agentic / "rule_mechanism_inventory.yaml").write_text(
        yaml.safe_dump(inventory), encoding="utf-8"
    )
    (agentic / "rule_migrations.yaml").write_text(
        yaml.safe_dump(migrations_data), encoding="utf-8"
    )


def test_current_rule_registry_validates() -> None:
    assert validate_rule_registry() == []


def test_rule_registry_cli_passes_current_repository_state() -> None:
    result = CliRunner().invoke(app, ["rule-registry", "check"])
    assert result.exit_code == 0
    assert "Rule registry validation passed" in result.output


def test_validator_rejects_missing_required_term(tmp_path: Path) -> None:
    mechanism = _valid_mechanism()
    mechanism["sources"] = [{"path": "source.txt", "required_terms": ["missing"]}]
    _write_registry(tmp_path, mechanism)
    findings = validate_rule_registry(tmp_path)
    assert any("required term missing" in finding.message for finding in findings)


def test_validator_rejects_missing_mechanism_sources(tmp_path: Path) -> None:
    mechanism = _valid_mechanism()
    mechanism["sources"] = []
    _write_registry(tmp_path, mechanism)
    findings = validate_rule_registry(tmp_path)
    assert any("sources must list at least one source" in finding.message for finding in findings)


def test_validator_rejects_source_without_required_terms(tmp_path: Path) -> None:
    mechanism = _valid_mechanism()
    mechanism["sources"] = [{"path": "source.txt", "required_terms": []}]
    _write_registry(tmp_path, mechanism)
    findings = validate_rule_registry(tmp_path)
    assert any("must list at least one required_terms entry" in finding.message for finding in findings)



def test_validator_rejects_missing_surfaces_field(tmp_path: Path) -> None:
    mechanism = _valid_mechanism()
    mechanism.pop("surfaces")
    _write_registry(tmp_path, mechanism)
    findings = validate_rule_registry(tmp_path)
    assert any("surfaces must be a list" in finding.message for finding in findings)

def test_validator_rejects_empty_surfaces(tmp_path: Path) -> None:
    mechanism = _valid_mechanism()
    mechanism["surfaces"] = []
    _write_registry(tmp_path, mechanism)
    findings = validate_rule_registry(tmp_path)
    assert any("surfaces must list at least one entry" in finding.message for finding in findings)

def test_validator_rejects_missing_tests_field(tmp_path: Path) -> None:
    mechanism = _valid_mechanism()
    mechanism.pop("tests")
    _write_registry(tmp_path, mechanism)
    findings = validate_rule_registry(tmp_path)
    assert any("tests must be a list" in finding.message for finding in findings)

def test_validator_rejects_missing_test_path(tmp_path: Path) -> None:
    mechanism = _valid_mechanism()
    mechanism["tests"] = ["tests/missing_test_file.py"]
    _write_registry(tmp_path, mechanism)
    findings = validate_rule_registry(tmp_path)
    assert any("missing test path: tests/missing_test_file.py" in finding.message for finding in findings)


def test_validator_rejects_migration_to_unknown_mechanism(tmp_path: Path) -> None:
    _write_registry(tmp_path, _valid_mechanism(), replaced_by="unknown")
    findings = validate_rule_registry(tmp_path)
    assert any(
        "replaced_by must reference an active mechanism" in finding.message
        for finding in findings
    )


def test_validator_rejects_missing_mechanism_classification(tmp_path: Path) -> None:
    mechanism = _valid_mechanism()
    mechanism.pop("category")
    _write_registry(tmp_path, mechanism)
    findings = validate_rule_registry(tmp_path)
    assert any("category must be one of" in finding.message for finding in findings)


def test_validator_rejects_invalid_priority(tmp_path: Path) -> None:
    mechanism = _valid_mechanism()
    mechanism["priority"] = 0
    _write_registry(tmp_path, mechanism)
    findings = validate_rule_registry(tmp_path)
    assert any("priority must be an integer" in finding.message for finding in findings)


def test_validator_rejects_invalid_enforcement_phase(tmp_path: Path) -> None:
    mechanism = _valid_mechanism()
    mechanism["enforcement_phase"] = "later"
    _write_registry(tmp_path, mechanism)
    findings = validate_rule_registry(tmp_path)
    assert any("enforcement_phase must be one of" in finding.message for finding in findings)


def test_validator_rejects_incompatible_category_phase(tmp_path: Path) -> None:
    mechanism = _valid_mechanism()
    mechanism["category"] = "communication"
    mechanism["enforcement_phase"] = "guard"
    _write_registry(tmp_path, mechanism)
    findings = validate_rule_registry(tmp_path)
    assert any(
        "incompatible category/enforcement_phase combination" in finding.message
        for finding in findings
    )


def test_validator_rejects_ambiguous_enforcement_order(tmp_path: Path) -> None:
    first = _valid_mechanism()
    second = _valid_mechanism()
    second["id"] = "other"
    _write_registry(tmp_path, first, extra_mechanisms=[second])
    findings = validate_rule_registry(tmp_path)
    assert any("ambiguous enforcement order" in finding.message for finding in findings)


def test_validator_allows_same_category_with_different_priority(tmp_path: Path) -> None:
    first = _valid_mechanism()
    second = _valid_mechanism()
    second["id"] = "other"
    second["priority"] = 2
    _write_registry(tmp_path, first, extra_mechanisms=[second])
    findings = validate_rule_registry(tmp_path)
    assert findings == []


def test_validator_rejects_missing_known_legacy_index(tmp_path: Path) -> None:
    _write_registry(tmp_path, _valid_mechanism(), known_legacy_rule_ids=[])
    findings = validate_rule_registry(tmp_path)
    assert any("known_legacy_rule_ids must list" in finding.message for finding in findings)


def test_validator_rejects_missing_migration_for_known_legacy_rule(tmp_path: Path) -> None:
    _write_registry(tmp_path, _valid_mechanism(), known_legacy_rule_ids=["old", "missing"])
    findings = validate_rule_registry(tmp_path)
    assert any("known legacy rule missing migration entry: missing" in finding.message for finding in findings)


def test_validator_rejects_unindexed_migration_entry(tmp_path: Path) -> None:
    _write_registry(tmp_path, _valid_mechanism(), known_legacy_rule_ids=[])
    data_path = tmp_path / ".agentic" / "rule_migrations.yaml"
    data = yaml.safe_load(data_path.read_text(encoding="utf-8"))
    data["known_legacy_rule_ids"] = ["different"]
    data_path.write_text(yaml.safe_dump(data), encoding="utf-8")
    findings = validate_rule_registry(tmp_path)
    assert any("migration entry missing from known legacy rule index: old" in finding.message for finding in findings)


def test_validator_rejects_invalid_migration_status(tmp_path: Path) -> None:
    migration = _valid_migration()
    migration["status"] = "unknown"
    _write_registry(tmp_path, _valid_mechanism(), migrations_override=[migration])
    findings = validate_rule_registry(tmp_path)
    assert any("status must be one of" in finding.message for finding in findings)


def test_validator_rejects_missing_migration_evidence(tmp_path: Path) -> None:
    migration = _valid_migration()
    migration["evidence"] = []
    _write_registry(tmp_path, _valid_mechanism(), migrations_override=[migration])
    findings = validate_rule_registry(tmp_path)
    assert any("evidence must list at least one evidence path" in finding.message for finding in findings)


def test_validator_allows_archived_terminal_migration_status(tmp_path: Path) -> None:
    migration = {
        "legacy_id": "old",
        "status": "archived",
        "evidence": ["evidence.txt"],
        "migration_reason": "obsolete and intentionally archived",
    }
    _write_registry(tmp_path, _valid_mechanism(), migrations_override=[migration])
    findings = validate_rule_registry(tmp_path)
    assert findings == []


def test_validator_rejects_terminal_status_with_replacement(tmp_path: Path) -> None:
    migration = {
        "legacy_id": "old",
        "status": "rejected",
        "replaced_by": "m",
        "evidence": ["evidence.txt"],
        "migration_reason": "not a valid active rule",
    }
    _write_registry(tmp_path, _valid_mechanism(), migrations_override=[migration])
    findings = validate_rule_registry(tmp_path)
    assert any("terminal migration status must not set replaced_by" in finding.message for finding in findings)
