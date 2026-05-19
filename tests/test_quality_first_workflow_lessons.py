from pathlib import Path

import yaml

def test_quality_first_rules_are_recorded_in_handoff_state() -> None:
    data = yaml.safe_load(Path(".agentic/handoff_state.yaml").read_text(encoding="utf-8"))
    rule_ids = {rule.get("id") for rule in data.get("rules", []) if isinstance(rule, dict)}
    assert "quality-first-no-shortcuts" in rule_ids
    assert "patch-artifact-preflight-before-application" in rule_ids
    assert "generated-code-syntax-first" in rule_ids
    assert "coverage-yaml-terms-must-be-strings" in rule_ids
    assert "final-summary-self-validation" in rule_ids

def test_recent_patch_failure_patterns_are_recorded() -> None:
    data = yaml.safe_load(Path(".agentic/handoff_state.yaml").read_text(encoding="utf-8"))
    pattern_ids = {item.get("id") for item in data.get("recent_failure_patterns", []) if isinstance(item, dict)}
    assert "nested-triple-quote-code-generator" in pattern_ids
    assert "yaml-colon-term-reinterpreted-as-mapping" in pattern_ids
    assert "final-pass-after-inner-fail" in pattern_ids
