from pathlib import Path


REQUIRED = [
    "SLICE",
    "NAME: <slice-name>",
    "SCOPE: <short scope>",
    "BRANCH: <branch-or-NONE>",
    "EXECUTION",
    "ORIGIN: local|remote|mixed",
    "STATE_MODE: local|remote|unknown",
    "MODE_CHECK: pass|fail|not_run",
    "SWITCH_HINT: ./ns mode-write local|remote && ./ns mode-check local|remote",
    "RESULT",
    "WORK: PASS|FAIL|PENDING|HARD-FAIL|NO-COMMAND",
    "EVIDENCE: PASS|FAIL|PARTIAL|CHAT_ONLY|NOT_REQUIRED",
    "OVERALL: PASS|FAIL|PENDING|HARD-FAIL|NO-COMMAND",
    "REMOTE",
    "REMOTE_EVIDENCE: PASS|FAIL|PARTIAL|NOT_REQUIRED",
    "PR: #<number> open|merged|none",
    "HEAD_SHA: <sha-or-NONE>",
    "CI: pass|fail|in_progress|not_started|unknown",
    "MERGE: done|not_done|blocked|not_required",
    "EVIDENCE FILES",
    "terminal_log: docs/reports/terminal/<file>.log|NONE",
    "command_report: docs/reports/command_runs/<file>.md|NONE",
    "INTERPRETATION",
    "NEXT",
    "SAFE_STEP: <next concrete action>",
    "CHAT_REPLY: d|f|w|paste-output|stop",
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
