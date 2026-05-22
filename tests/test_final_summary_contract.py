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


def test_final_summary_must_be_printed_by_terminal_block() -> None:
    text = Path("docs/governance/FINAL_SUMMARY_CONTRACT.md").read_text(encoding="utf-8")
    assert "The structured SUMMARY must be printed by the terminal block itself" in text
    assert "captured in the terminal log" in text
    assert "A chat-only summary is not sufficient" in text
    assert "only `### RESULT: PASS ###` or `### RESULT: FAIL ###` is incomplete" in text


def test_chat_communication_contract_requires_terminal_summary_evidence() -> None:
    text = Path("docs/governance/CHAT_COMMUNICATION_CONTRACT.md").read_text(encoding="utf-8")
    assert "a rendered final summary printed in the terminal output" in text
    assert "captured in the terminal log or command report" in text
    assert "A chat-only structured summary is not enough for terminal-directed work" in text


def test_compiled_context_contains_final_summary_rule() -> None:
    text = Path(".agentic/compiled_agent_context.yaml").read_text(encoding="utf-8")
    assert "id: final-summary-contract" in text
    assert "framed SUMMARY contract" in text


def test_human_docs_reference_final_summary_contract() -> None:
    for name in ["docs/STATUS.md", "docs/handoff/CURRENT_HANDOFF.md", "docs/TEST_GATES.md"]:
        text = Path(name).read_text(encoding="utf-8")
        assert "Final summary contract" in text
        assert "OVERALL RESULT" in text


def test_terminal_log_finalization_rule_is_documented() -> None:
    text = Path("docs/governance/FINAL_SUMMARY_CONTRACT.md").read_text(encoding="utf-8")
    assert "Terminal log finalization rule" in text
    assert "must not upload a partial running log" in text
    assert "rendered structured SUMMARY and the FINAL STATE section" in text
    assert "copy the completed log into `docs/reports/terminal/`" in text


def test_remote_log_lookup_rule_requires_direct_path_fetch_first() -> None:
    final = Path("docs/governance/FINAL_SUMMARY_CONTRACT.md").read_text(encoding="utf-8")
    assert "Remote log lookup rule" in final
    assert "verify that exact path directly before claiming the log is missing" in final
    assert "GitHub code search, commit search, and filename search are advisory only" in final
    assert "direct fetch succeeds" in final


def test_chat_contract_rejects_search_only_remote_log_conclusions() -> None:
    chat = Path("docs/governance/CHAT_COMMUNICATION_CONTRACT.md").read_text(encoding="utf-8")
    assert "verify that exact path directly before using search results" in chat
    assert "Search lag is not evidence that a pushed log is missing" in chat


def test_compiled_context_contains_remote_log_direct_path_rule() -> None:
    compiled = Path(".agentic/compiled_agent_context.yaml").read_text(encoding="utf-8")
    assert "id: remote-log-direct-path-first" in compiled
    assert "direct-fetch that path before relying on search results" in compiled

