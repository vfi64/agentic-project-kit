from pathlib import Path


def test_no_remote_command_deadlock_rule_is_compiled():
    text = Path(".agentic/compiled_agent_context.yaml").read_text(encoding="utf-8")
    assert "no-remote-command-deadlock" in text
    assert "NO-COMMAND" in text


def test_no_remote_command_deadlock_rule_is_documented():
    for path in ["docs/TEST_GATES.md", "docs/STATUS.md", "docs/handoff/CURRENT_HANDOFF.md"]:
        text = Path(path).read_text(encoding="utf-8")
        assert "no-remote-command-deadlock" in text
        assert "Remote command first is a delivery preference" in text
