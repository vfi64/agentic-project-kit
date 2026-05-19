from agentic_project_kit.agent_command_runner import print_agent_next_footer


def test_print_agent_next_footer_frames_pass_reply(capsys):
    print_agent_next_footer("PASS", "p")
    out = capsys.readouterr().out
    assert "================================================================" in out
    assert "SUMMARY" in out
    assert "WORK RESULT: PASS" in out
    assert "EVIDENCE RESULT: PASS" in out
    assert "OVERALL RESULT: PASS" in out
    assert "NEXT CHAT REPLY: p" in out


def test_print_agent_next_footer_frames_fail_reply(capsys):
    print_agent_next_footer("FAIL", "f", "normal command failure")
    out = capsys.readouterr().out
    assert "SUMMARY" in out
    assert "WORK RESULT: FAIL" in out
    assert "EVIDENCE RESULT: PASS" in out
    assert "OVERALL RESULT: FAIL" in out
    assert "REASON: normal command failure" in out
    assert "NEXT CHAT REPLY: f" in out


def test_print_agent_next_footer_frames_hard_fail_reply(capsys):
    print_agent_next_footer("HARD-FAIL", "paste-output", "FAIL_PULL")
    out = capsys.readouterr().out
    assert "SUMMARY" in out
    assert "WORK RESULT: HARD-FAIL" in out
    assert "EVIDENCE RESULT: FAIL" in out
    assert "OVERALL RESULT: HARD-FAIL" in out
    assert "NEXT CHAT REPLY: paste-output" in out
