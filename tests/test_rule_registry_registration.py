from __future__ import annotations

from pathlib import Path

import yaml
from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.rule_registry_registration import register_rule_registry_entry
from agentic_project_kit.rule_registry_validator import validate_rule_registry


def _write_file(path: Path, text: str = "present") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_direct_registry(tmp_path: Path, *, source_text: str = "present") -> None:
    agentic = tmp_path / ".agentic"
    agentic.mkdir()
    _write_file(tmp_path / "source.txt", source_text)
    _write_file(tmp_path / "tests" / "test_existing_rule.py", "def test_existing_rule():\n    assert True\n")
    _write_file(tmp_path / "evidence.txt", "evidence")
    inventory = {
        "schema_version": 1,
        "mechanisms": [
            {
                "id": "existing-rule",
                "status": "active",
                "owner": "test-owner",
                "category": "governance",
                "priority": 1,
                "enforcement_phase": "guard",
                "conflict_domains": ["existing-domain"],
                "surfaces": ["existing-surface"],
                "sources": [{"path": "source.txt", "required_terms": ["present"]}],
                "protected_rule_intent": "keep existing governance rule covered",
                "tests": ["tests/test_existing_rule.py"],
            }
        ],
    }
    migrations = {
        "schema_version": 1,
        "known_legacy_rule_ids": ["legacy-existing-rule"],
        "migrations": [
            {
                "legacy_id": "legacy-existing-rule",
                "status": "migrated",
                "replaced_by": "existing-rule",
                "evidence": ["evidence.txt"],
                "migration_reason": "baseline migration",
            }
        ],
    }
    coverage = {
        "schema_version": 1,
        "coverage": [
            {
                "mechanism_id": "existing-rule",
                "test_coverage": "direct",
                "assertions": [
                    {
                        "assertion_id": "existing-rule-direct",
                        "kind": "guard",
                        "covered_surfaces": ["existing-surface"],
                        "evidence_refs": [
                            {"kind": "source", "path": "source.txt"},
                            {"kind": "test", "path": "tests/test_existing_rule.py"},
                        ],
                        "statement": "existing rule remains directly covered",
                    }
                ],
            }
        ],
    }
    (agentic / "rule_mechanism_inventory.yaml").write_text(
        yaml.safe_dump(inventory, sort_keys=False), encoding="utf-8"
    )
    (agentic / "rule_migrations.yaml").write_text(
        yaml.safe_dump(migrations, sort_keys=False), encoding="utf-8"
    )
    (agentic / "rule_test_coverage.yaml").write_text(
        yaml.safe_dump(coverage, sort_keys=False), encoding="utf-8"
    )
    (agentic / "rule_direct_test_plan.yaml").write_text(
        yaml.safe_dump({"schema_version": 1, "direct_test_followups": []}, sort_keys=False),
        encoding="utf-8",
    )


def _register(tmp_path: Path) -> dict[str, object]:
    _write_file(tmp_path / "new_source.txt", "new required anchor")
    _write_file(tmp_path / "tests" / "test_new_rule.py", "def test_new_rule():\n    assert True\n")
    return register_rule_registry_entry(
        tmp_path,
        mechanism_id="new-rule",
        rule_class="workflow",
        owner="test-owner",
        priority=2,
        enforcement_phase="guard",
        conflict_domains=["new-domain"],
        surfaces=["new-surface"],
        source_path="new_source.txt",
        required_terms=["new required anchor"],
        test_paths=["tests/test_new_rule.py"],
        protected_rule_intent="keep new workflow rule covered",
        assertion_statement="new workflow rule is directly covered",
    )


def _inventory(tmp_path: Path) -> dict[str, object]:
    return yaml.safe_load(
        (tmp_path / ".agentic" / "rule_mechanism_inventory.yaml").read_text(encoding="utf-8")
    )


def _coverage(tmp_path: Path) -> dict[str, object]:
    return yaml.safe_load(
        (tmp_path / ".agentic" / "rule_test_coverage.yaml").read_text(encoding="utf-8")
    )


def test_rule_register_adds_valid_rule(tmp_path: Path) -> None:
    _write_direct_registry(tmp_path)
    assert validate_rule_registry(tmp_path) == []

    result = _register(tmp_path)

    assert result["result_status"] == "PASS"
    assert result["written"] is True
    assert result["gate_relevant"] is True
    inventory = _inventory(tmp_path)
    assert [item["id"] for item in inventory["mechanisms"]] == ["existing-rule", "new-rule"]
    coverage = _coverage(tmp_path)
    assert [item["mechanism_id"] for item in coverage["coverage"]] == ["existing-rule", "new-rule"]
    assert validate_rule_registry(tmp_path) == []


def test_rule_register_rejects_missing_required_fields(tmp_path: Path) -> None:
    _write_direct_registry(tmp_path)

    result = register_rule_registry_entry(
        tmp_path,
        mechanism_id="new-rule",
        rule_class="workflow",
        owner="test-owner",
        priority=2,
        enforcement_phase="guard",
        conflict_domains=["new-domain"],
        surfaces=[],
        source_path="new_source.txt",
        required_terms=["new required anchor"],
        test_paths=[],
        protected_rule_intent="keep new workflow rule covered",
        assertion_statement="new workflow rule is directly covered",
    )

    assert result["result_status"] == "FAIL"
    assert result["code"] == "FAIL_MISSING_RULE_FIELDS"
    assert "surface" in result["missing_fields"]
    assert "test" in result["missing_fields"]
    assert [item["id"] for item in _inventory(tmp_path)["mechanisms"]] == ["existing-rule"]


def test_rule_register_rejects_duplicate_id(tmp_path: Path) -> None:
    _write_direct_registry(tmp_path)
    _write_file(tmp_path / "new_source.txt", "new required anchor")
    _write_file(tmp_path / "tests" / "test_new_rule.py", "def test_new_rule():\n    assert True\n")

    result = register_rule_registry_entry(
        tmp_path,
        mechanism_id="existing-rule",
        rule_class="workflow",
        owner="test-owner",
        priority=2,
        enforcement_phase="guard",
        conflict_domains=["new-domain"],
        surfaces=["new-surface"],
        source_path="new_source.txt",
        required_terms=["new required anchor"],
        test_paths=["tests/test_new_rule.py"],
        protected_rule_intent="keep new workflow rule covered",
        assertion_statement="new workflow rule is directly covered",
    )

    assert result["result_status"] == "FAIL"
    assert result["code"] == "FAIL_DUPLICATE_RULE_ID"
    assert [item["id"] for item in _inventory(tmp_path)["mechanisms"]] == ["existing-rule"]


def test_rule_register_preserves_existing_rules(tmp_path: Path) -> None:
    _write_direct_registry(tmp_path)
    before_inventory = _inventory(tmp_path)["mechanisms"][0]
    before_coverage = _coverage(tmp_path)["coverage"][0]

    result = _register(tmp_path)

    assert result["result_status"] == "PASS"
    assert _inventory(tmp_path)["mechanisms"][0] == before_inventory
    assert _coverage(tmp_path)["coverage"][0] == before_coverage


def test_rule_register_blocks_on_validate_findings(tmp_path: Path) -> None:
    _write_direct_registry(tmp_path, source_text="wrong text")

    result = _register(tmp_path)

    assert result["result_status"] == "FAIL"
    assert result["code"] == "FAIL_INVALID_REGISTRY"
    assert any("required term missing" in finding for finding in result["findings"])
    assert [item["id"] for item in _inventory(tmp_path)["mechanisms"]] == ["existing-rule"]


def test_rule_register_cli_emits_json(tmp_path: Path) -> None:
    _write_direct_registry(tmp_path)
    _write_file(tmp_path / "new_source.txt", "new required anchor")
    _write_file(tmp_path / "tests" / "test_new_rule.py", "def test_new_rule():\n    assert True\n")

    result = CliRunner().invoke(
        app,
        [
            "rule-registry",
            "register",
            "--root",
            str(tmp_path),
            "--id",
            "new-rule",
            "--class",
            "workflow",
            "--owner",
            "test-owner",
            "--priority",
            "2",
            "--enforcement-phase",
            "guard",
            "--conflict-domain",
            "new-domain",
            "--surface",
            "new-surface",
            "--source",
            "new_source.txt",
            "--required-term",
            "new required anchor",
            "--test",
            "tests/test_new_rule.py",
            "--protected-rule-intent",
            "keep new workflow rule covered",
            "--assertion-statement",
            "new workflow rule is directly covered",
            "--json",
        ],
    )

    assert result.exit_code == 0
    assert '"code": "PASS"' in result.output
