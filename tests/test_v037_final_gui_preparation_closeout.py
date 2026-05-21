from pathlib import Path

def read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")

def test_v037_closeout_report_declares_gui_preparation_complete():
    text = read("docs/reports/V0.3.37_FINAL_GUI_PREPARATION_CLOSEOUT.md")
    assert "STANDARD_ERROR_REDUCTION: 100%" in text
    assert "GUI_PREPARATION: 100%" in text
    assert "SHELL_ADAPTER_REMOVAL: 100%" in text
    assert "bounded/read-only-or-safe GUI MVP" in text

def test_v037_docs_lock_post_release_gate_separation():
    text = read("docs/governance/FINAL_SUMMARY_CONTRACT.md") + read("docs/TEST_GATES.md")
    assert "release-check" in text
    assert "pre-publication" in text
    assert "post-release-check" in text
    assert "tag or GitHub Release exists" in text

def test_v037_docs_lock_pr_no_checks_and_stop_after_fail():
    text = read("docs/governance/FINAL_SUMMARY_CONTRACT.md") + read("docs/TEST_GATES.md")
    assert "not `CI: PASS`" in text
    assert "CI: not_reported" in text
    assert "must not continue into later mutation" in text
    assert "Stop-after-fail" in text

def test_v037_zero_direct_ns_shell_adapter_state():
    tracked = list(Path("tools").glob("ns_*.sh"))
    assert tracked == []
    assert "tools/ns_" not in read("ns")
