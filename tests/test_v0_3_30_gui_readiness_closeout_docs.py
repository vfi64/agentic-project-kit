from pathlib import Path

def test_v0_3_30_gui_readiness_closeout_is_documented() -> None:
    status = Path("docs/STATUS.md").read_text(encoding="utf-8")
    handoff = Path("docs/handoff/CURRENT_HANDOFF.md").read_text(encoding="utf-8")
    combined = status + "\n" + handoff
    assert "v0.3.30 GUI Readiness Hardening Closeout" in combined
    assert "not the Tkinter GUI release" in status
    assert "not the Tkinter cockpit release" in handoff
    assert "PR #463: ActionResult core contract" in combined
    assert "PR #464: `cockpit run --json`" in combined
    assert "PR #465: Registry-only" in combined
    assert "PR #466: Queue-State contract" in combined
    assert "PR #467: Evidence-State contract" in combined
    assert "Tkinter remains explicitly deferred" in status
    assert "prepare release metadata" in handoff
