from pathlib import Path

import yaml

from agentic_project_kit.rule_registry_validator import validate_rule_registry


def _write_registry(root: Path, coverage: list[dict[str, object]]) -> None:
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
    (agentic / "rule_test_coverage.yaml").write_text(
        yaml.safe_dump({"schema_version": 1, "coverage": coverage}),
        encoding="utf-8",
    )


def test_validator_accepts_documented_coverage_with_rationale(tmp_path: Path) -> None:
    _write_registry(
        tmp_path,
        [
            {
                "mechanism_id": "mechanism-under-test",
                "test_coverage": "documented",
                "coverage_rationale": "covered by preserved source anchors",
                "assertions": ["source anchors are preserved"],
            }
        ],
    )
    assert validate_rule_registry(tmp_path) == []


def test_validator_rejects_unclassified_coverage(tmp_path: Path) -> None:
    _write_registry(
        tmp_path,
        [{"mechanism_id": "mechanism-under-test", "test_coverage": "later"}],
    )
    findings = validate_rule_registry(tmp_path)
    assert any("test_coverage must be one of" in finding.message for finding in findings)


def test_validator_rejects_documented_coverage_without_rationale(tmp_path: Path) -> None:
    _write_registry(
        tmp_path,
        [{"mechanism_id": "mechanism-under-test", "test_coverage": "documented"}],
    )
    findings = validate_rule_registry(tmp_path)
    assert any("coverage_rationale is required" in finding.message for finding in findings)


def test_validator_rejects_coverage_for_unknown_mechanism(tmp_path: Path) -> None:
    _write_registry(
        tmp_path,
        [
            {
                "mechanism_id": "mechanism-under-test",
                "test_coverage": "documented",
                "coverage_rationale": "covered by preserved source anchors",
                "assertions": ["source anchors are preserved"],
            },
            {
                "mechanism_id": "unknown-mechanism",
                "test_coverage": "documented",
                "coverage_rationale": "orphaned entry",
                "assertions": ["orphaned coverage is rejected"],
            },
        ],
    )
    findings = validate_rule_registry(tmp_path)
    assert any("coverage entry references unknown mechanism" in finding.message for finding in findings)
