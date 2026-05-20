from pathlib import Path

def test_v031_status_and_handoff_closeout_is_documented() -> None:
    status = Path("docs/STATUS.md").read_text(encoding="utf-8")
    handoff = Path("docs/handoff/CURRENT_HANDOFF.md").read_text(encoding="utf-8")
    combined = status + "\n" + handoff
    required = [
        "v0.3.31 Pre-GUI Execution Hardening Closeout",
        "v0.3.31 is the current pre-GUI execution hardening line.",
        "It does not ship the Tkinter GUI.",
        "Terminal Evidence Guard with CLI command `agentic-kit evidence guard LOGFILE`.",
        "Local shortcut `./ns evidence-guard LOGFILE`.",
        "Typed Work Order Evidence Contract.",
        "Typed Work Order Evidence Runtime Check.",
        "validate_typed_work_order_evidence",
        "Next safe step: prepare and release v0.3.31.",
        "Do not start Tkinter before v0.3.31 is released and post-release verified.",
    ]
    missing = [needle for needle in required if needle not in combined]
    assert not missing, missing

def test_v031_closeout_does_not_claim_tkinter_release() -> None:
    combined = Path("docs/STATUS.md").read_text(encoding="utf-8") + "\n" + Path("docs/handoff/CURRENT_HANDOFF.md").read_text(encoding="utf-8")
    forbidden = [
        "v0.3.31 ships the Tkinter GUI",
        "Tkinter GUI release is complete",
        "Tkinter is released in v0.3.31",
    ]
    present = [needle for needle in forbidden if needle in combined]
    assert not present, present
