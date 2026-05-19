from pathlib import Path


REQUIRED = [
    "WORK RESULT:",
    "EVIDENCE RESULT:",
    "OVERALL RESULT:",
    "REMOTE_EVIDENCE:",
    "terminal_log=",
    "command_report=",
    "NEXT_CHAT_REPLY:",
    "### RESULT:",
]


def test_final_summary_contract_is_documented() -> None:
    text = Path("docs/governance/FINAL_SUMMARY_CONTRACT.md").read_text(encoding="utf-8")
    assert "================================================================" in text
    for required in REQUIRED:
        assert required in text


def test_compiled_context_contains_final_summary_rule() -> None:
    text = Path(".agentic/compiled_agent_context.yaml").read_text(encoding="utf-8")
    assert "id: final-summary-contract" in text
    assert "framed SUMMARY contract" in text


def test_human_docs_reference_final_summary_contract() -> None:
    for name in ["docs/STATUS.md", "docs/handoff/CURRENT_HANDOFF.md", "docs/TEST_GATES.md"]:
        text = Path(name).read_text(encoding="utf-8")
        assert "Final summary contract" in text
        assert "OVERALL RESULT" in text
