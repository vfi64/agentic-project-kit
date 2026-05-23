from pathlib import Path

import yaml

YAML_GOVERNANCE_FILES = [
    ".agentic/handoff_state.yaml",
    ".agentic/no_copy_terminal_policy.yaml",
    "docs/DOCUMENTATION_COVERAGE.yaml",
    "docs/DOCUMENTATION_REGISTRY.yaml",
]


def test_yaml_governance_files_are_parseable() -> None:
    for path in YAML_GOVERNANCE_FILES:
        loaded = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
        assert loaded is not None, path


def test_yaml_integrity_rule_is_recorded() -> None:
    data = yaml.safe_load(Path(".agentic/handoff_state.yaml").read_text(encoding="utf-8"))
    rule_ids = {item.get("id") for item in data.get("rules", []) if isinstance(item, dict)}
    pattern_ids = {
        item.get("id")
        for item in data.get("recent_failure_patterns", [])
        if isinstance(item, dict)
    }
    assert "yaml-structured-mutation-only" in rule_ids
    assert "repeated-yaml-governance-file-corruption" in pattern_ids
