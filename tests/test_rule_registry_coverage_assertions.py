from pathlib import Path

import yaml

from agentic_project_kit.rule_registry_validator import validate_rule_registry


def _assertion(assertion_id: str = "mechanism-under-test-source-anchor") -> dict[str, object]:
    return {
        "assertion_id": assertion_id,
        "kind": "anchor",
        "covered_surfaces": ["test-surface"],
        "evidence_refs": [{"kind": "source", "path": "source.txt"}],
        "statement": "source anchors are preserved",
    }


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


def _write_two_mechanism_registry(root: Path, coverage: list[dict[str, object]]) -> None:
    (root / "source.txt").write_text("present", encoding="utf-8")
    (root / "evidence.txt").write_text("evidence", encoding="utf-8")
    agentic = root / ".agentic"
    agentic.mkdir()
    mechanisms = []
    migrations = []
    for mechanism_id in ["mechanism-under-test", "second-mechanism"]:
        mechanisms.append(
            {
                "id": mechanism_id,
                "status": "active",
                "owner": "test-owner",
                "category": "governance",
                "priority": 1,
                "enforcement_phase": "guard",
                "conflict_domains": [mechanism_id],
                "surfaces": ["test-surface"],
                "tests": [],
                "protected_rule_intent": "preserve a tested rule",
                "sources": [{"path": "source.txt", "required_terms": ["present"]}],
            }
        )
        migrations.append(
            {
                "legacy_id": f"legacy-{mechanism_id}",
                "status": "migrated",
                "replaced_by": mechanism_id,
                "evidence": ["evidence.txt"],
                "migration_reason": f"covered by {mechanism_id}",
            }
        )
    (agentic / "rule_mechanism_inventory.yaml").write_text(
        yaml.safe_dump({"schema_version": 1, "mechanisms": mechanisms}), encoding="utf-8"
    )
    (agentic / "rule_migrations.yaml").write_text(
        yaml.safe_dump(
            {
                "schema_version": 1,
                "known_legacy_rule_ids": [m["legacy_id"] for m in migrations],
                "migrations": migrations,
            }
        ),
        encoding="utf-8",
    )
    (agentic / "rule_test_coverage.yaml").write_text(
        yaml.safe_dump({"schema_version": 1, "coverage": coverage}),
        encoding="utf-8",
    )


def test_validator_accepts_coverage_assertions(tmp_path: Path) -> None:
    _write_registry(
        tmp_path,
        {
            "test_coverage": "documented",
            "coverage_rationale": "covered by source anchors",
            "assertions": [_assertion()],
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


def test_validator_rejects_free_text_assertions(tmp_path: Path) -> None:
    _write_registry(
        tmp_path,
        {
            "test_coverage": "documented",
            "coverage_rationale": "covered by source anchors",
            "assertions": ["source anchors are preserved"],
        },
    )
    findings = validate_rule_registry(tmp_path)
    assert any("assertion entries must be mappings" in finding.message for finding in findings)


def test_validator_rejects_unknown_assertion_kind(tmp_path: Path) -> None:
    assertion = _assertion()
    assertion["kind"] = "later"
    _write_registry(
        tmp_path,
        {
            "test_coverage": "documented",
            "coverage_rationale": "covered by source anchors",
            "assertions": [assertion],
        },
    )
    findings = validate_rule_registry(tmp_path)
    assert any("assertion kind must be one of" in finding.message for finding in findings)


def test_validator_rejects_duplicate_assertion_id(tmp_path: Path) -> None:
    _write_registry(
        tmp_path,
        {
            "test_coverage": "documented",
            "coverage_rationale": "covered by source anchors",
            "assertions": [_assertion(), _assertion()],
        },
    )
    findings = validate_rule_registry(tmp_path)
    assert any("duplicate assertion_id: mechanism-under-test-source-anchor" in finding.message for finding in findings)


def test_validator_rejects_assertion_without_statement(tmp_path: Path) -> None:
    assertion = _assertion()
    assertion["statement"] = ""
    _write_registry(
        tmp_path,
        {
            "test_coverage": "documented",
            "coverage_rationale": "covered by source anchors",
            "assertions": [assertion],
        },
    )
    findings = validate_rule_registry(tmp_path)
    assert any("assertion missing statement" in finding.message for finding in findings)


def test_validator_rejects_assertion_without_covered_surfaces(tmp_path: Path) -> None:
    assertion = _assertion()
    assertion.pop("covered_surfaces")
    _write_registry(
        tmp_path,
        {
            "test_coverage": "documented",
            "coverage_rationale": "covered by source anchors",
            "assertions": [assertion],
        },
    )
    findings = validate_rule_registry(tmp_path)
    assert any("assertion missing covered_surfaces list" in finding.message for finding in findings)


def test_validator_rejects_empty_covered_surfaces(tmp_path: Path) -> None:
    assertion = _assertion()
    assertion["covered_surfaces"] = []
    _write_registry(
        tmp_path,
        {
            "test_coverage": "documented",
            "coverage_rationale": "covered by source anchors",
            "assertions": [assertion],
        },
    )
    findings = validate_rule_registry(tmp_path)
    assert any("assertion covered_surfaces must list at least one entry" in finding.message for finding in findings)


def test_validator_rejects_unknown_covered_surface(tmp_path: Path) -> None:
    assertion = _assertion()
    assertion["covered_surfaces"] = ["not-a-mechanism-surface"]
    _write_registry(
        tmp_path,
        {
            "test_coverage": "documented",
            "coverage_rationale": "covered by source anchors",
            "assertions": [assertion],
        },
    )
    findings = validate_rule_registry(tmp_path)
    assert any("assertion references unknown covered_surface" in finding.message for finding in findings)


def test_validator_rejects_assertion_id_without_mechanism_prefix(tmp_path: Path) -> None:
    _write_registry(
        tmp_path,
        {
            "test_coverage": "documented",
            "coverage_rationale": "covered by source anchors",
            "assertions": [_assertion("source-anchor")],
        },
    )
    findings = validate_rule_registry(tmp_path)
    assert any("assertion_id must start with mechanism-under-test-" in finding.message for finding in findings)


def test_validator_rejects_globally_duplicate_assertion_id(tmp_path: Path) -> None:
    _write_two_mechanism_registry(
        tmp_path,
        [
            {
                "mechanism_id": "mechanism-under-test",
                "test_coverage": "documented",
                "coverage_rationale": "covered by source anchors",
                "assertions": [_assertion("mechanism-under-test-shared")],
            },
            {
                "mechanism_id": "second-mechanism",
                "test_coverage": "documented",
                "coverage_rationale": "covered by source anchors",
                "assertions": [
                    {
                        "assertion_id": "mechanism-under-test-shared",
                        "kind": "anchor",
                        "covered_surfaces": ["test-surface"],
                        "evidence_refs": [{"kind": "source", "path": "source.txt"}],
                        "statement": "source anchors are preserved",
                    }
                ],
            },
        ],
    )
    findings = validate_rule_registry(tmp_path)
    assert any("assertion_id already used by mechanism-under-test" in finding.message for finding in findings)


def test_validator_rejects_assertion_without_evidence_refs(tmp_path: Path) -> None:
    assertion = _assertion()
    assertion.pop("evidence_refs")
    _write_registry(
        tmp_path,
        {
            "test_coverage": "documented",
            "coverage_rationale": "covered by source anchors",
            "assertions": [assertion],
        },
    )
    findings = validate_rule_registry(tmp_path)
    assert any("assertion missing evidence_refs list" in finding.message for finding in findings)


def test_validator_rejects_empty_evidence_refs(tmp_path: Path) -> None:
    assertion = _assertion()
    assertion["evidence_refs"] = []
    _write_registry(
        tmp_path,
        {
            "test_coverage": "documented",
            "coverage_rationale": "covered by source anchors",
            "assertions": [assertion],
        },
    )
    findings = validate_rule_registry(tmp_path)
    assert any("assertion evidence_refs must list at least one entry" in finding.message for finding in findings)


def test_validator_rejects_unregistered_source_evidence_ref(tmp_path: Path) -> None:
    assertion = _assertion()
    assertion["evidence_refs"] = [{"kind": "source", "path": "other-source.txt"}]
    _write_registry(
        tmp_path,
        {
            "test_coverage": "documented",
            "coverage_rationale": "covered by source anchors",
            "assertions": [assertion],
        },
    )
    findings = validate_rule_registry(tmp_path)
    assert any("evidence_refs source path is not registered" in finding.message for finding in findings)


def test_validator_rejects_unregistered_test_evidence_ref(tmp_path: Path) -> None:
    assertion = _assertion()
    assertion["evidence_refs"] = [{"kind": "test", "path": "tests/test_missing.py"}]
    _write_registry(
        tmp_path,
        {
            "test_coverage": "documented",
            "coverage_rationale": "covered by source anchors",
            "assertions": [assertion],
        },
    )
    findings = validate_rule_registry(tmp_path)
    assert any("evidence_refs test path is not registered" in finding.message for finding in findings)
