from pathlib import Path


def test_typed_work_orders_are_documented_as_pre_gui_execution_path() -> None:
    status = Path("docs/STATUS.md").read_text(encoding="utf-8")
    handoff = Path("docs/handoff/CURRENT_HANDOFF.md").read_text(encoding="utf-8")
    combined = status + chr(10) + handoff
    assert "Typed Work Orders Pre-GUI Execution Path" in combined
    assert "preferred pre-GUI execution path" in status
    assert "agentic-kit typed-run <path>" in handoff
    assert "agentic-kit typed-queue-status --json" in handoff
    assert "agentic-kit typed-next --json" in handoff
    assert "no_command" in combined
    assert "exactly_one_command" in combined
    assert "multiple_commands" in combined
    assert "already_executed" in combined
    assert "long chat-generated shell or Python patch blocks" in status
    assert "thin Tkinter cockpit must consume these typed contracts" in status
    assert "GUI work remains deferred" in handoff
