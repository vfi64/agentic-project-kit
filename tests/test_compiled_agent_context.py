from pathlib import Path

import yaml


def test_compiled_agent_context_yaml_is_valid_and_prioritized():
    data = yaml.safe_load(Path(".agentic/compiled_agent_context.yaml").read_text(encoding="utf-8"))
    assert data["schema_version"] == 1
    assert data["source_policy"]["remote_first_no_guess"] is True
    assert data["source_policy"]["new_rules_need_docs_yaml_tests"] is True
    assert data["priority_order"][0] == ".agentic/compiled_agent_context.yaml"


def test_compiled_agent_context_contains_active_hard_rules():
    data = yaml.safe_load(Path(".agentic/compiled_agent_context.yaml").read_text(encoding="utf-8"))
    ids = {item["id"] for item in data["hard_rules"]}
    required = {
        "remote-first-no-guess",
        "final-summary-contract",
        "patch-artifact-preflight",
        "rules-must-be-test-backed",
        "successor-handoff-freshness-guard",
    }
    assert required <= ids


def test_compiled_agent_context_lists_handoff_freshness_sources():
    data = yaml.safe_load(Path(".agentic/compiled_agent_context.yaml").read_text(encoding="utf-8"))
    sources = set(data["mandatory_successor_chat_sources"])
    assert "docs/STATUS.md" in sources
    assert ".agentic/handoff_state.yaml" in sources
    assert "docs/handoff/CURRENT_HANDOFF.md" in sources
    assert "docs/releases/VERIFIED_RELEASES.md" in sources
    assert "stale successor handoff prompt after newer main merge" in data["drift_detection"]["drift_classes"]
