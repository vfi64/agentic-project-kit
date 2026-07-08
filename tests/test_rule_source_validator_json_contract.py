from __future__ import annotations

import json

from typer.testing import CliRunner

from agentic_project_kit.cli import app

DOC = "docs/governance/RULE_SOURCE_VALIDATOR_JSON_CONTRACT.md"
REGISTRY = "docs/DOCUMENTATION_REGISTRY.yaml"
RULE_PLAN = "docs/planning/RULE_REFRESH_HANDSHAKE_PLAN.md"


def test_rule_source_validator_json_contract_documents_stable_fields() -> None:
    text = open(DOC, encoding="utf-8").read()

    for field in [
        "schema_version",
        "sources_total",
        "is_valid",
        "fail_closed",
        "source_paths",
        "missing_required_paths",
        "yaml_parse_error_paths",
        "handoff_state_errors",
        "blocking_reasons",
    ]:
        assert f"`{field}`" in text

    assert "Exit code `1`" in text
    assert "fail closed" in text
    assert "must not mutate repository files" in text


def test_rule_source_validator_json_contract_matches_cli_shape() -> None:
    result = CliRunner().invoke(app, ["rules", "validate-sources", "--json"])

    assert result.exit_code == 0, result.output
    data = json.loads(result.output)

    assert data["schema_version"] == 1
    assert isinstance(data["sources_total"], int)
    assert isinstance(data["is_valid"], bool)
    assert isinstance(data["fail_closed"], bool)
    assert isinstance(data["source_paths"], list)
    assert isinstance(data["missing_required_paths"], list)
    assert isinstance(data["yaml_parse_error_paths"], list)
    assert isinstance(data["handoff_state_errors"], list)
    assert isinstance(data["blocking_reasons"], list)
    assert data["is_valid"] is (not bool(data["blocking_reasons"]))
    assert data["fail_closed"] is bool(data["blocking_reasons"])


def test_documentation_registry_contains_rule_source_validator_json_contract() -> None:
    text = open(REGISTRY, encoding="utf-8").read()

    assert "docs/governance/RULE_SOURCE_VALIDATOR_JSON_CONTRACT.md" in text
    assert "Stable JSON contract for the read-only canonical rule source validator" in text


def test_rule_refresh_plan_links_rule_source_validator_json_contract() -> None:
    text = open(RULE_PLAN, encoding="utf-8").read()

    assert "RULE_SOURCE_VALIDATOR_JSON_CONTRACT.md" in text
    assert "Rule-source validator JSON contract" in text
