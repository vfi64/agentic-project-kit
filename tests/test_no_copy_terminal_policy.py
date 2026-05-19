from pathlib import Path

import yaml


def test_no_copy_terminal_policy_is_active_and_log_backed():
    data = yaml.safe_load(Path(".agentic/no_copy_terminal_policy.yaml").read_text(encoding="utf-8"))
    assert data["status"] == "active"
    rule_ids = {rule["id"] for rule in data["rules"]}
    assert "full-output-log-required" in rule_ids
    assert "d-means-log-backed-pass" in rule_ids
    assert "no-unconditional-pass" in rule_ids
    assert data["handoff_integration"]["generated_handoff_prompt_must_not_request_copy_paste_on_pass"] is True


def test_no_copy_policy_requires_remote_evidence_summary():
    text = Path(".agentic/no_copy_terminal_policy.yaml").read_text(encoding="utf-8")
    assert "mandatory_remote_evidence_contract" in text
    assert "REMOTE_EVIDENCE: PASS" in text
    assert "paste-output is still required" in text
    assert "must not be written again after it has been committed" in text
