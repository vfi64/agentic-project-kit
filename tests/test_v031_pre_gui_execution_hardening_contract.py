from pathlib import Path


def test_v031_pre_gui_execution_hardening_contract_is_documented() -> None:
    text = Path("docs/archive/PRE_GUI_EXECUTION_HARDENING.md").read_text(encoding="utf-8")
    required = [
        "No false PASS after failed gate",
        "Clean base before log creation",
        "No nested quote patch generator",
        "Evidence finalization contract",
        "GUI boundary",
        "typed work orders",
        "A workflow must not commit, push, merge, tag, or publish after a required targeted test",
        "must not be written to again after the evidence commit",
    ]
    missing = [needle for needle in required if needle not in text]
    assert not missing, missing
