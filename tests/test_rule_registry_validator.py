from pathlib import Path

import yaml
from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.rule_registry_validator import validate_rule_registry


def test_current_rule_registry_validates() -> None:
    assert validate_rule_registry() == []


def test_rule_registry_cli_passes_current_repository_state() -> None:
    result = CliRunner().invoke(app, ["rule-registry", "check"])
    assert result.exit_code == 0
    assert "Rule registry validation passed" in result.output


def test_validator_rejects_missing_required_term(tmp_path: Path) -> None:
    source = tmp_path / "source.txt"
    source.write_text("present", encoding="utf-8")
    evidence = tmp_path / "evidence.txt"
    evidence.write_text("evidence", encoding="utf-8")
    agentic = tmp_path / ".agentic"
    agentic.mkdir()
    inventory = {
        "schema_version": 1,
        "mechanisms": [
            {
                "id": "m",
                "status": "active",
                "protected_rule_intent": "intent",
                "sources": [
                    {"path": "source.txt", "required_terms": ["missing"]},
                ],
            }
        ],
    }
    migrations = {
        "schema_version": 1,
        "migrations": [
            {
                "legacy_id": "old",
                "status": "migrated",
                "replaced_by": "m",
                "evidence": ["evidence.txt"],
                "migration_reason": "reason",
            }
        ],
    }
    (agentic / "rule_mechanism_inventory.yaml").write_text(
        yaml.safe_dump(inventory), encoding="utf-8"
    )
    (agentic / "rule_migrations.yaml").write_text(
        yaml.safe_dump(migrations), encoding="utf-8"
    )
    findings = validate_rule_registry(tmp_path)
    assert any("required term missing" in finding.message for finding in findings)


def test_validator_rejects_migration_to_unknown_mechanism(tmp_path: Path) -> None:
    source = tmp_path / "source.txt"
    source.write_text("present", encoding="utf-8")
    evidence = tmp_path / "evidence.txt"
    evidence.write_text("evidence", encoding="utf-8")
    agentic = tmp_path / ".agentic"
    agentic.mkdir()
    inventory = {
        "schema_version": 1,
        "mechanisms": [
            {
                "id": "m",
                "status": "active",
                "protected_rule_intent": "intent",
                "sources": [
                    {"path": "source.txt", "required_terms": ["present"]},
                ],
            }
        ],
    }
    migrations = {
        "schema_version": 1,
        "migrations": [
            {
                "legacy_id": "old",
                "status": "migrated",
                "replaced_by": "unknown",
                "evidence": ["evidence.txt"],
                "migration_reason": "reason",
            }
        ],
    }
    (agentic / "rule_mechanism_inventory.yaml").write_text(
        yaml.safe_dump(inventory), encoding="utf-8"
    )
    (agentic / "rule_migrations.yaml").write_text(
        yaml.safe_dump(migrations), encoding="utf-8"
    )
    findings = validate_rule_registry(tmp_path)
    assert any(
        "replaced_by must reference an active mechanism" in finding.message
        for finding in findings
    )
