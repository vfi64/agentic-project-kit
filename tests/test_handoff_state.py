from pathlib import Path

import yaml

from agentic_project_kit.handoff_state import load_handoff_state, validate_handoff_state

def test_handoff_state_yaml_is_parseable_and_valid():
    data = load_handoff_state()
    assert data["schema_version"] == 1
    assert validate_handoff_state(data) == []

def test_no_copy_policy_is_referenced():
    data = yaml.safe_load(Path(".agentic/handoff_state.yaml").read_text(encoding="utf-8"))
    assert data["policies"]["no_copy_terminal_policy"] == ".agentic/no_copy_terminal_policy.yaml"
    active_rule_ids = {rule["id"] for rule in data["rules"] if rule["status"] == "active"}
    assert "no-copy-terminal-evidence" in active_rule_ids

def test_superseded_rules_have_successor():
    data = load_handoff_state()
    for rule in data["rules"]:
        if rule["status"] == "superseded":
            assert rule.get("superseded_by") or rule.get("reason")
