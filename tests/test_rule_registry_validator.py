from pathlib import Path

import yaml
from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.rule_registry_validator import validate_rule_registry


def _valid_mechanism() -> dict[str, object]:
    return {
        "id": "m",
        "status": "active",
        "category": "governance",
        "priority": 1,
        "enforcement_phase": "guard",
        "protected_rule_intent": "intent",
        "sources": [
            {"path": "source.txt", "required_terms": ["present"]},
        ],
    }


def _write_registry(
    tmp_path: Path,
    mechanism: dict[str, object],
    replaced_by: str = "m",
    extra_mechanisms: list[dict[str, object]] | None = None,
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
    inventory = {
        "schema_version": 1,
        "mechanisms": mechanisms,
    }
    migrations = {
        "schema_version": 1,
        "migrations": [
            {
                "legacy_id": "old",
                "status": "migrated",
                "replaced_by": replaced_by,
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
