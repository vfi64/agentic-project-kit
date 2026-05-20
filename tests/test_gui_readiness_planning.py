from pathlib import Path


def test_v0_3_30_gui_readiness_is_before_tkinter() -> None:
    status = Path("docs/STATUS.md").read_text(encoding="utf-8")
    handoff = Path("docs/handoff/CURRENT_HANDOFF.md").read_text(encoding="utf-8")
    combined = status + "\n" + handoff
    assert "v0.3.30 GUI Readiness Hardening Plan" in combined
    assert "GUI readiness hardening, not a Tkinter implementation" in handoff
    assert "Action Registry is the single source of allowed GUI actions" in combined
    assert "remote evidence present" in combined
    assert "already executed command" in combined
    assert "dirty worktrees" in combined
    assert "Tkinter is explicitly deferred until these contracts pass gates" in combined
