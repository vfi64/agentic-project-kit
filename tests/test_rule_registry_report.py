import json
from pathlib import Path

import yaml
from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.rule_registry_report import (
    build_rule_registry_report,
    render_rule_registry_report,
)


def _write_registry(root: Path) -> None:
    (root / "source.txt").write_text("present", encoding="utf-8")
    (root / "test_module.py").write_text("def test_present():\n    assert True\n", encoding="utf-8")
    (root / "evidence.txt").write_text("evidence", encoding="utf-8")
    agentic = root / ".agentic"
    agentic.mkdir()
    (agentic / "rule_mechanism_inventory.yaml").write_text(
        yaml.safe_dump(
            {
                "schema_version": 1,
                "mechanisms": [
                    {
                        "id": "direct-mechanism",
                        "status": "active",
                        "owner": "test-owner",
                        "category": "governance",
                        "priority": 1,
                        "enforcement_phase": "guard",
                        "conflict_domains": ["direct-domain"],
                        "surfaces": ["direct-surface"],
                        "tests": ["test_module.py"],
                        "protected_rule_intent": "preserve direct behavior",
                        "sources": [{"path": "source.txt", "required_terms": ["present"]}],
                    },
                    {
                        "id": "documented-mechanism",
                        "status": "active",
                        "owner": "test-owner",
                        "category": "communication",
                        "priority": 2,
                        "enforcement_phase": "runtime",
                        "conflict_domains": ["documented-domain"],
                        "surfaces": ["documented-surface"],
                        "tests": [],
                        "protected_rule_intent": "preserve documented behavior",
                        "sources": [{"path": "source.txt", "required_terms": ["present"]}],
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    (agentic / "rule_migrations.yaml").write_text(
        yaml.safe_dump(
            {
                "schema_version": 1,
                "known_legacy_rule_ids": ["old-direct", "old-documented"],
                "migrations": [
                    {
                        "legacy_id": "old-direct",
                        "status": "migrated",
                        "replaced_by": "direct-mechanism",
                        "evidence": ["evidence.txt"],
                        "migration_reason": "direct mechanism covers it",
                    },
                    {
                        "legacy_id": "old-documented",
                        "status": "migrated",
                        "replaced_by": "documented-mechanism",
                        "evidence": ["evidence.txt"],
                        "migration_reason": "documented mechanism covers it",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    (agentic / "rule_test_coverage.yaml").write_text(
        yaml.safe_dump(
            {
                "schema_version": 1,
                "coverage": [
                    {
                        "mechanism_id": "direct-mechanism",
                        "test_coverage": "direct",
                        "assertions": [
                            {
                                "assertion_id": "direct-mechanism-direct-assertion",
                                "kind": "guard",
                                "covered_surfaces": ["direct-surface"],
                                "evidence_refs": [
                                    {"kind": "source", "path": "source.txt"},
                                    {"kind": "test", "path": "test_module.py"},
                                ],
                                "statement": "direct behavior is tested",
                            }
                        ],
                    },
                    {
                        "mechanism_id": "documented-mechanism",
                        "test_coverage": "documented",
                        "coverage_rationale": "source anchors cover this until direct tests are added",
                        "assertions": [
                            {
                                "assertion_id": "documented-mechanism-anchor-assertion",
                                "kind": "anchor",
                                "covered_surfaces": ["documented-surface"],
                                "evidence_refs": [{"kind": "source", "path": "source.txt"}],
                                "statement": "documented behavior is anchored",
                            }
                        ],
                    },
                ],
            }
        ),
        encoding="utf-8",
    )


def test_build_rule_registry_report_summarizes_coverage(tmp_path: Path) -> None:
    _write_registry(tmp_path)
    report = build_rule_registry_report(tmp_path)
    assert report["summary"]["active_mechanism_count"] == 2
    assert report["summary"]["direct_mechanism_count"] == 1
    assert report["summary"]["documented_mechanism_count"] == 1
    assert report["summary"]["mechanisms_without_direct_tests"] == 1
    assert report["summary"]["assertion_count"] == 2
    assert report["summary"]["evidence_ref_count"] == 3
    assert report["summary"]["validation_finding_count"] == 0


def test_render_rule_registry_report_includes_machine_counts(tmp_path: Path) -> None:
    _write_registry(tmp_path)
    rendered = render_rule_registry_report(build_rule_registry_report(tmp_path))
    assert "active_mechanisms: 2" in rendered
    assert "direct: 1" in rendered
    assert "documented: 1" in rendered
    assert "documented-mechanism: coverage=documented" in rendered


def test_rule_registry_report_cli_emits_json_for_current_repo() -> None:
    result = CliRunner().invoke(app, ["rule-registry", "report", "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["schema_version"] == 1
    assert payload["summary"]["active_mechanism_count"] >= 1
    assert payload["summary"]["validation_finding_count"] == 0


def test_rule_registry_report_cli_emits_human_summary_for_current_repo() -> None:
    result = CliRunner().invoke(app, ["rule-registry", "report"])
    assert result.exit_code == 0
    assert "Rule registry report" in result.output
    assert "validation_findings: 0" in result.output
