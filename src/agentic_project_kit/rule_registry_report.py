from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from agentic_project_kit.rule_registry_validator import (
    COVERAGE_PATH,
    INVENTORY_PATH,
    RuleRegistryFinding,
    validate_rule_registry,
)


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def _list_of_dicts(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _evidence_refs(assertions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    for assertion in assertions:
        for ref in assertion.get("evidence_refs", []):
            if isinstance(ref, dict):
                refs.append(ref)
    return refs


def _finding_to_dict(finding: RuleRegistryFinding) -> dict[str, str]:
    return {"path": finding.path, "message": finding.message}


def build_rule_registry_report(root: Path | str = ".") -> dict[str, Any]:
    base = Path(root)
    inventory = _load_yaml(base / INVENTORY_PATH)
    coverage_path = base / COVERAGE_PATH
    coverage_data = _load_yaml(coverage_path) if coverage_path.exists() else {}

    coverage_by_mechanism = {
        str(entry.get("mechanism_id", "")): entry
        for entry in _list_of_dicts(coverage_data.get("coverage"))
        if str(entry.get("mechanism_id", "")).strip()
    }

    mechanism_rows: list[dict[str, Any]] = []
    active_mechanisms = [
        item
        for item in _list_of_dicts(inventory.get("mechanisms"))
        if item.get("status") == "active"
    ]

    for mechanism in active_mechanisms:
        mechanism_id = str(mechanism.get("id", ""))
        coverage_entry = coverage_by_mechanism.get(mechanism_id, {})
        tests = mechanism.get("tests", []) if isinstance(mechanism.get("tests"), list) else []
        sources = mechanism.get("sources", []) if isinstance(mechanism.get("sources"), list) else []
        surfaces = mechanism.get("surfaces", []) if isinstance(mechanism.get("surfaces"), list) else []
        assertions = _list_of_dicts(coverage_entry.get("assertions", mechanism.get("assertions", [])))
        evidence_refs = _evidence_refs(assertions)
        test_coverage = str(coverage_entry.get("test_coverage", mechanism.get("test_coverage", "unclassified")))
        row = {
            "id": mechanism_id,
            "owner": mechanism.get("owner"),
            "category": mechanism.get("category"),
            "priority": mechanism.get("priority"),
            "enforcement_phase": mechanism.get("enforcement_phase"),
            "test_coverage": test_coverage,
            "source_count": len(sources),
            "surface_count": len(surfaces),
            "direct_test_count": len(tests),
            "assertion_count": len(assertions),
            "evidence_ref_count": len(evidence_refs),
            "source_evidence_ref_count": sum(1 for ref in evidence_refs if ref.get("kind") == "source"),
            "test_evidence_ref_count": sum(1 for ref in evidence_refs if ref.get("kind") == "test"),
            "has_direct_tests": bool(tests),
            "requires_direct_test_followup": not bool(tests) and test_coverage != "direct",
        }
        mechanism_rows.append(row)

    validation_findings = validate_rule_registry(base)
    by_coverage: dict[str, int] = {}
    for row in mechanism_rows:
        coverage = str(row["test_coverage"])
        by_coverage[coverage] = by_coverage.get(coverage, 0) + 1

    report = {
        "schema_version": 1,
        "summary": {
            "active_mechanism_count": len(mechanism_rows),
            "coverage_counts": by_coverage,
            "direct_mechanism_count": by_coverage.get("direct", 0),
            "documented_mechanism_count": by_coverage.get("documented", 0),
            "indirect_mechanism_count": by_coverage.get("indirect", 0),
            "unclassified_mechanism_count": by_coverage.get("unclassified", 0),
            "mechanisms_without_direct_tests": sum(1 for row in mechanism_rows if not row["has_direct_tests"]),
            "assertion_count": sum(int(row["assertion_count"]) for row in mechanism_rows),
            "evidence_ref_count": sum(int(row["evidence_ref_count"]) for row in mechanism_rows),
            "validation_finding_count": len(validation_findings),
        },
        "mechanisms": mechanism_rows,
        "validation_findings": [_finding_to_dict(finding) for finding in validation_findings],
    }
    return report


def render_rule_registry_report(report: dict[str, Any]) -> str:
    summary = report.get("summary", {}) if isinstance(report.get("summary"), dict) else {}
    lines = [
        "Rule registry report",
        f"active_mechanisms: {summary.get('active_mechanism_count', 0)}",
        f"direct: {summary.get('direct_mechanism_count', 0)}",
        f"documented: {summary.get('documented_mechanism_count', 0)}",
        f"indirect: {summary.get('indirect_mechanism_count', 0)}",
        f"without_direct_tests: {summary.get('mechanisms_without_direct_tests', 0)}",
        f"assertions: {summary.get('assertion_count', 0)}",
        f"evidence_refs: {summary.get('evidence_ref_count', 0)}",
        f"validation_findings: {summary.get('validation_finding_count', 0)}",
    ]
    mechanisms = report.get("mechanisms", [])
    if isinstance(mechanisms, list):
        for row in mechanisms:
            if not isinstance(row, dict):
                continue
            lines.append(
                "- {id}: coverage={coverage}; tests={tests}; assertions={assertions}; evidence_refs={evidence_refs}".format(
                    id=row.get("id"),
                    coverage=row.get("test_coverage"),
                    tests=row.get("direct_test_count"),
                    assertions=row.get("assertion_count"),
                    evidence_refs=row.get("evidence_ref_count"),
                )
            )
    return "\n".join(lines)
