from agentic_project_kit.run_summary import EvidenceResult, NextChatReply, RemoteEvidence, RunSummary, WorkResult, render_run_summary, summary_for_status


def test_render_run_summary_contains_required_contract_fields():
    rendered = render_run_summary(RunSummary(WorkResult.PASS, EvidenceResult.PASS, WorkResult.PASS, RemoteEvidence.PASS, "docs/reports/terminal/example.log", "NONE", NextChatReply.D))
    assert "SUMMARY" in rendered
    assert "WORK RESULT: PASS" in rendered
    assert "EVIDENCE RESULT: PASS" in rendered
    assert "OVERALL RESULT: PASS" in rendered
    assert "REMOTE_EVIDENCE: PASS" in rendered
    assert "terminal_log=docs/reports/terminal/example.log" in rendered
    assert "command_report=NONE" in rendered
    assert "NEXT_CHAT_REPLY: d" in rendered
    assert "### RESULT: PASS ###" in rendered


def test_summary_for_failure_requests_f_not_paste_output():
    rendered = render_run_summary(summary_for_status(1, terminal_log="docs/reports/terminal/fail.log"))
    assert "WORK RESULT: FAIL" in rendered
    assert "NEXT_CHAT_REPLY: f" in rendered
    assert "paste-output" not in rendered
    assert "terminal_log=docs/reports/terminal/fail.log" in rendered
