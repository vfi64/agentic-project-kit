from agentic_project_kit.final_summary_contract import validate_final_summary

GOOD_PASS = """================================================================\nSUMMARY\nWORK RESULT: PASS\nEVIDENCE RESULT: PASS\nOVERALL RESULT: PASS\nREMOTE_EVIDENCE: PASS\nterminal_log=docs/reports/terminal/example.log\ncommand_report=NONE\nNEXT_CHAT_REPLY: p\n### RESULT: PASS ###\n================================================================\n"""

def test_final_summary_accepts_log_backed_pass():
    assert validate_final_summary(GOOD_PASS) == []

def test_final_summary_rejects_pass_without_remote_evidence():
    bad = GOOD_PASS.replace("REMOTE_EVIDENCE: PASS", "REMOTE_EVIDENCE: PARTIAL")
    bad = bad.replace("NEXT_CHAT_REPLY: p", "NEXT_CHAT_REPLY: paste-output")
    assert "OVERALL RESULT: PASS requires REMOTE_EVIDENCE: PASS or NOT_REQUIRED" in validate_final_summary(bad)

def test_final_summary_rejects_inner_fail_relabelled_as_pass():
    text = "### RESULT: FAIL ###\n" + GOOD_PASS
    assert "previous inner FAIL cannot be relabeled as OVERALL RESULT: PASS" in validate_final_summary(text)

def test_final_summary_allows_failed_work_with_pushed_evidence():
    text = """================================================================\nSUMMARY\nWORK RESULT: FAIL\nEVIDENCE RESULT: PASS\nOVERALL RESULT: FAIL\nREMOTE_EVIDENCE: PASS\nterminal_log=docs/reports/terminal/failure.log\ncommand_report=NONE\nNEXT_CHAT_REPLY: f\n### RESULT: FAIL ###\n================================================================\n"""
    assert validate_final_summary(text) == []
