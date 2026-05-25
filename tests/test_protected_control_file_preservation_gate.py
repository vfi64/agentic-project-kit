from __future__ import annotations

import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]

def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")

def read_yaml(path: str):
    return yaml.safe_load(read_text(path))

def test_core_yaml_control_files_remain_parseable_dicts() -> None:
    for path in [
        ".agentic/compiled_agent_context.yaml",
        ".agentic/handoff_state.yaml",
        ".agentic/control_file_preservation.yaml",
        ".agentic/rule_mechanism_inventory.yaml",
        "docs/DOCUMENTATION_REGISTRY.yaml",
    ]:
        assert isinstance(read_yaml(path), dict), path

def test_compiled_agent_context_preserves_current_core_anchors() -> None:
    payload = read_yaml(".agentic/compiled_agent_context.yaml")
    for key in ["schema_version", "source_policy", "priority_order", "mandatory_successor_chat_sources", "hard_rules", "final_summary_contract", "communication_rules", "normal_operator_path"]:
        assert key in payload
    assert len(payload["priority_order"]) >= 10
    assert len(payload["mandatory_successor_chat_sources"]) >= 10
    assert len(payload["hard_rules"]) >= 10
    rule_ids = {rule["id"] for rule in payload["hard_rules"]}
    assert "control-file-preservation" in rule_ids
    assert "final-summary-contract" in rule_ids
    assert "chat-communication-contract" in rule_ids

def test_handoff_state_preserves_current_release_anchors() -> None:
    payload = read_yaml(".agentic/handoff_state.yaml")
    for key in ["schema_version", "updated", "repo", "safe_state", "release", "rules", "recent_failure_patterns"]:
        assert key in payload
    assert payload["repo"]["name"] == "agentic-project-kit"
    assert "current_version" in payload["release"]
    assert "tag" in payload["release"]

def test_rule_and_document_registries_preserve_minimum_entries() -> None:
    rules = read_yaml(".agentic/rule_mechanism_inventory.yaml")
    docs = read_yaml("docs/DOCUMENTATION_REGISTRY.yaml")
    assert "mechanisms" in rules
    assert len(rules["mechanisms"]) >= 10
    assert "documents" in docs
    assert len(docs["documents"]) >= 19

def test_append_only_execution_memory_is_present_and_parseable() -> None:
    path = ROOT / ".agentic/commands/executed.jsonl"
    lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert lines
    sample = json.loads(lines[-1])
    assert {"command_id", "outcome", "timestamp_utc"} <= set(sample)

def test_governance_contracts_preserve_summary_and_change_decision_anchors() -> None:
    summary = read_text("docs/governance/FINAL_SUMMARY_CONTRACT.md")
    change = read_text("docs/governance/PROTECTED_CONTROL_FILE_CHANGE_CONTRACT.md")
    normalized_summary = summary.replace("_", " ").upper()
    for anchor in ["WORK RESULT", "EVIDENCE RESULT", "OVERALL RESULT", "REMOTE EVIDENCE", "NEXT CHAT REPLY"]:
        assert anchor in normalized_summary
    for term in ["protected_control", "migration record", "user decision", "keep", "migrate", "obsolete", "abort"]:
        assert term in change
