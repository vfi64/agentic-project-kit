from pathlib import Path

import yaml

from agentic_project_kit.rule_registry_validator import validate_rule_registry


def _write_registry(root: Path, coverage_entry: dict[str, object]) -> None:
    (root / "source.txt").write_text("present", encoding="utf-8")
    (root / "evidence.txt").write_text("evidence", encoding="utf-8")
    agentic = root / ".agentic"
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
    entry = {"mechanism_id": "mechanism-under-test", **coverage_entry}
    (agentic / "rule_test_coverage.yaml").write_text(
        yaml.safe_dump({"schema_version": 1, "coverage": [entry]}),
        encoding="utf-8",
    )


def test_validator_accepts_coverage_assertions(tmp_path: Path) -> None:
    _write_registry(
        tmp_path,
        {
            "test_coverage": "documented",
            "coverage_rationale": "covered by source anchors",
            "assertions": ["source anchors are preserved"],
        },
    )
    assert validate_rule_registry(tmp_path) == []


def test_validator_rejects_missing_coverage_assertions(tmp_path: Path) -> None:
    _write_registry(
        tmp_path,
        {
            "test_coverage": "documented",
            "coverage_rationale": "covered by source anchors",
        },
    )
    findings = validate_rule_registry(tmp_path)
    assert any("assertions must be a list" in finding.message for finding in findings)


def test_validator_rejects_empty_coverage_assertions(tmp_path: Path) -> None:
    _write_registry(
        tmp_path,
        {
            "test_coverage": "documented",
            "coverage_rationale": "covered by source anchors",
            "assertions": [],
        },
    )
    findings = validate_rule_registry(tmp_path)
    assert any("assertions must list at least one entry" in finding.message for finding in findings)
