from pathlib import Path
import yaml

RULE_ID = "remote-first-no-guess"

def test_remote_first_no_guess_rule_is_active_in_handoff_state():
    data = yaml.safe_load(Path(".agentic/handoff_state.yaml").read_text(encoding="utf-8"))
    rules = data.get("rules", [])
    matches = [rule for rule in rules if isinstance(rule, dict) and rule.get("id") == RULE_ID]
    assert matches
    assert matches[0].get("status") == "active"
    text = matches[0].get("text", "").lower()
    assert "do not guess" in text
    assert "remote repository" in text
    assert "command help" in text

def test_remote_first_no_guess_rule_is_documented_in_user_facing_state_docs():
    for path in ["docs/TEST_GATES.md", "docs/STATUS.md", "docs/handoff/CURRENT_HANDOFF.md"]:
        text = Path(path).read_text(encoding="utf-8").lower()
        assert "remote-first no-guess" in text
        assert "command help" in text
        assert "chat memory is not a source of truth" in text

def test_guessing_before_inspection_failure_pattern_is_recorded():
    data = yaml.safe_load(Path(".agentic/handoff_state.yaml").read_text(encoding="utf-8"))
    patterns = data.get("recent_failure_patterns", [])
    matches = [item for item in patterns if isinstance(item, dict) and item.get("id") == "guessing-before-inspection"]
    assert matches
    assert "inspect the remote repository" in matches[0].get("prevention", "").lower()
