from pathlib import Path

import yaml

from agentic_project_kit.rule_registry_validator import validate_rule_registry


def _write_minimal_registry(root: Path, mechanism: dict[str, object]) -> None:
    (root / "source.txt").write_text("present", encoding="utf-8")
    (root / "evidence.txt").write_text("evidence", encoding="utf-8")
    agentic = root / ".agentic"
    agentic.mkdir()
    (agentic / "rule_mechanism_inventory.yaml").write_text(
        yaml.safe_dump({"schema_version": 1, "mechanisms": [mechanism]}),
        encoding="utf-8",
    )
    (agentic / "rule_migrations.yaml").write_text(
        yaml.safe_dump(
            {
                "schema_version": 1,
                "known_legacy_rule_ids": ["legacy-rule"],
                "migrations": [
                    {
                        "legacy_id": "legacy-rule",
                        "status": "migrated",
                        "replaced_by": "mechanism-under-test",
                        "evidence": ["evidence.txt"],
                        "migration_reason": "covered by mechanism-under-test",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )


def _valid_mechanism() -> dict[str, object]:
    return {
        "id": "mechanism-under-test",
        "status": "active",
        "owner": "test-owner",
        "category": "governance",
        "priority": 1,
        "enforcement_phase": "guard",
        "conflict_domains": ["test-domain"],
        "surfaces": ["test-surface"],
        "tests": [],
        "protected_rule_intent": "preserve a tested rule",
        "sources": [{"path": "source.txt", "required_terms": ["present"]}],
    }


def test_validator_requires_mechanism_owner(tmp_path: Path) -> None:
    mechanism = _valid_mechanism()
    mechanism.pop("owner")
    _write_minimal_registry(tmp_path, mechanism)
    findings = validate_rule_registry(tmp_path)
    assert any("owner must be a non-empty string" in finding.message for finding in findings)


def test_validator_requires_conflict_domains(tmp_path: Path) -> None:
    mechanism = _valid_mechanism()
    mechanism["conflict_domains"] = []
    _write_minimal_registry(tmp_path, mechanism)
    findings = validate_rule_registry(tmp_path)
    assert any("conflict_domains must list at least one entry" in finding.message for finding in findings)


def test_validator_uses_conflict_domains_for_ordering(tmp_path: Path) -> None:
    first = _valid_mechanism()
    second = _valid_mechanism()
    second["id"] = "second-mechanism"
    second["conflict_domains"] = ["other-domain"]
    _write_minimal_registry(tmp_path, first)
    data_path = tmp_path / ".agentic" / "rule_mechanism_inventory.yaml"
    data = yaml.safe_load(data_path.read_text(encoding="utf-8"))
    data["mechanisms"].append(second)
    data_path.write_text(yaml.safe_dump(data), encoding="utf-8")
    assert validate_rule_registry(tmp_path) == []
