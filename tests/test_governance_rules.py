from pathlib import Path

import yaml


def test_rule_hardening_rule_is_documented_and_gated() -> None:
    agents = Path("AGENTS.md").read_text(encoding="utf-8")
    test_gates = Path("docs/TEST_GATES.md").read_text(encoding="utf-8")
    coverage = yaml.safe_load(Path("docs/DOCUMENTATION_COVERAGE.yaml").read_text(encoding="utf-8"))

    assert "## Rule Hardening Rule" in agents
    assert "## Rule Hardening Gate" in test_gates
    assert "Governance rule change" in test_gates

    rule_ids = {rule["id"] for rule in coverage["rules"]}
    assert "rule-hardening-coverage" in rule_ids

    required_terms = {
        "Rule Hardening Rule",
        "deterministic unit or integration test",
        "documentation coverage requirement",
        "explicit review-only exception",
        "Rule Hardening Gate",
        "documented review-only exception",
    }
    combined = agents + "\n" + test_gates + "\n" + Path("docs/DOCUMENTATION_COVERAGE.yaml").read_text(encoding="utf-8")
    for term in required_terms:
        assert term in combined


def test_next_step_terminal_workflow_is_documented_and_gated() -> None:
    agents = Path("AGENTS.md").read_text(encoding="utf-8")
    workflow_doc = Path("docs/WORKFLOW_OUTPUT_CYCLE.md").read_text(encoding="utf-8")
    coverage_text = Path("docs/DOCUMENTATION_COVERAGE.yaml").read_text(encoding="utf-8")
    coverage = yaml.safe_load(coverage_text)

    rule_ids = {rule["id"] for rule in coverage["rules"]}
    assert "next-step-terminal-workflow-coverage" in rule_ids

    assert "## Standard next-step terminal workflow" in agents
    assert "## Standard next-step terminal workflow" in workflow_doc

    required_terms = {
        "cd /Users/hof/Dropbox/Privat/GitHub/agentic-project-kit",
        "python tools/next-step.py",
        "done",
        "The short acknowledgement `d` is also valid",
        "instead of long manual Copy-and-Paste terminal blocks",
        "agentic-kit workflow request",
        "agentic-kit workflow run",
        "agentic-kit workflow status",
        "agentic-kit workflow cleanup",
    }
    combined = agents + "\n" + workflow_doc + "\n" + coverage_text
    for term in required_terms:
        assert term in combined
