from pathlib import Path

def test_final_summary_no_executable_placeholder_rule_is_persistent() -> None:
    files = [
        Path(".agentic/compiled_agent_context.yaml"),
        Path("docs/governance/FINAL_SUMMARY_CONTRACT.md"),
        Path("docs/TEST_GATES.md"),
        Path("docs/STATUS.md"),
        Path("docs/handoff/CURRENT_HANDOFF.md"),
    ]
    for path in files:
        text = path.read_text(encoding="utf-8")
        assert "No executable placeholder summaries" in text or "final-summary-no-executable-placeholders" in text
    compiled = Path(".agentic/compiled_agent_context.yaml").read_text(encoding="utf-8")
    assert "id: final-summary-no-executable-placeholders" in compiled
    assert "PASS|FAIL" in compiled
    assert "never placeholder alternatives" in compiled
