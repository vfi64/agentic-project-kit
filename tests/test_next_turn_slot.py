from __future__ import annotations

from agentic_project_kit.next_turn_slot import fixed_slot_status, render_status, write_fixed_slot

def test_fixed_slot_status_empty(tmp_path):
    status = fixed_slot_status(tmp_path)
    assert status.state == "empty"
    assert status.overwrite_allowed is True

def test_write_fixed_slot_creates_yaml_and_script(tmp_path):
    status = write_fixed_slot(tmp_path, command_id="abc")
    assert status.state == "ready"
    assert (tmp_path / ".agentic/commands/inbox/next-turn.yaml").exists()
    assert (tmp_path / ".agentic/commands/inbox/next-turn.py").exists()
    yaml_text = (tmp_path / ".agentic/commands/inbox/next-turn.yaml").read_text(encoding="utf-8")
    assert "command_id: abc" in yaml_text
    assert "local_terminal_log: /tmp/agentic-project-kit/next-turn-latest.log" in yaml_text
    assert "remote_terminal_log: docs/reports/terminal/next-turn-latest.log" in yaml_text

def test_write_fixed_slot_refuses_existing_without_force(tmp_path):
    write_fixed_slot(tmp_path)
    try:
        write_fixed_slot(tmp_path)
    except RuntimeError as exc:
        assert "fixed slot is not empty" in str(exc)
    else:
        raise AssertionError("expected RuntimeError")

def test_render_status_contract(tmp_path):
    rendered = render_status(fixed_slot_status(tmp_path))
    assert "NEXT_TURN_FIXED_SLOT_STATUS" in rendered
    assert "### RESULT: PASS ###" in rendered
