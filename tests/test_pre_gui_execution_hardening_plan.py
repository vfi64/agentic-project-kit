from pathlib import Path


def test_pre_gui_execution_hardening_plan_defers_tkinter_until_runner() -> None:
    status = Path("docs/STATUS.md").read_text(encoding="utf-8")
    handoff = Path("docs/handoff/CURRENT_HANDOFF.md").read_text(encoding="utf-8")
    combined = status + "\n" + handoff
    assert "v0.3.31 Pre-GUI Execution Hardening Plan" in combined
    assert "GUI expansion is intentionally paused" in combined
    assert "minimal typed Work Order Runner" in combined
    assert "without chat-generated patch scripts" in combined
    assert "dirty-state blocking" in combined
    assert "typed Patch DSL" in combined
    assert "structured State Source of Truth" in combined
    assert "Markdown is a projection" in combined
    assert "shell is a runner, not a patch language" in combined
    assert "Begin v0.3.31 with minimal typed Work Order Runner work before further Tkinter GUI expansion." in handoff
