from pathlib import Path

import yaml

from agentic_project_kit.rule_registry_validator import validate_rule_registry


def test_validator_rejects_missing_coverage_for_active_mechanism(tmp_path: Path) -> None:
    (tmp_path / "source.txt").write_text("present", encoding="utf-8")
    (tmp_path / "evidence.txt").write_text("evidence", encoding="utf-8")
    agentic = tmp_path / ".agentic"
    agentic.mkdir()
    (agentic / "rule_mechanism_inventory.yaml").write_text(
        yaml.safe_dump(
            {
                "schema_version": 1,
                "mechanisms": [
                    {
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
                ],
            }
        ),
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
    (agentic / "rule_test_coverage.yaml").write_text(
        yaml.safe_dump({"schema_version": 1, "coverage": []}),
        encoding="utf-8",
    )

    findings = validate_rule_registry(tmp_path)

    assert any(
        "missing coverage entry for active mechanism: mechanism-under-test" in finding.message
        for finding in findings
    )
