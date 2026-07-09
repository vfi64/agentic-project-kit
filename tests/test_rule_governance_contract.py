from pathlib import Path

import yaml


RULE_ID = "rules-must-be-test-backed"


def test_rule_governance_rule_is_active_in_handoff_state() -> None:
    data = yaml.safe_load(Path(".agentic/handoff_state.yaml").read_text(encoding="utf-8"))
    rules = data.get("rules", [])
    matching = [rule for rule in rules if isinstance(rule, dict) and rule.get("id") == RULE_ID]
    assert matching, "durable workflow rules must be tracked by rule id in handoff_state.yaml"
    assert matching[0].get("status") == "active"
    assert "deterministic test" in matching[0].get("text", "")


def test_rule_governance_is_documented() -> None:
    text = Path("docs/governance/RULE_GOVERNANCE.md").read_text(encoding="utf-8")
    assert RULE_ID in text
    assert "stable rule id" in text
    assert "deterministic test" in text
    assert "not done" in text


def test_rule_governance_test_itself_references_rule_id() -> None:
    text = Path(__file__).read_text(encoding="utf-8")
    assert RULE_ID in text
