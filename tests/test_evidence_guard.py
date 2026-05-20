from pathlib import Path

from agentic_project_kit.evidence_guard import check_terminal_log
from agentic_project_kit.evidence_guard import last_result_marker

def test_last_result_marker_uses_last_marker() -> None:
    text = "### RESULT: FAIL ###\nnoise\n### RESULT: PASS ###\n"
    assert last_result_marker(text) == "PASS"

def test_evidence_guard_rejects_final_pass_after_failed_gate(tmp_path: Path) -> None:
    log = tmp_path / "false-pass.log"
    log.write_text("FAILED tests/example.py\n### RESULT: PASS ###\n", encoding="utf-8")
    result = check_terminal_log(log)
    assert not result.ok
    assert result.final_result == "PASS"
    assert "final PASS conflicts" in result.findings[0]

def test_evidence_guard_accepts_clean_pass(tmp_path: Path) -> None:
    log = tmp_path / "pass.log"
    log.write_text("all good\n### RESULT: PASS ###\n", encoding="utf-8")
    result = check_terminal_log(log)
    assert result.ok
    assert result.final_result == "PASS"

def test_evidence_guard_rejects_missing_final_marker(tmp_path: Path) -> None:
    log = tmp_path / "missing.log"
    log.write_text("all good\n", encoding="utf-8")
    result = check_terminal_log(log)
    assert not result.ok
    assert result.final_result == "UNKNOWN"


def test_evidence_guard_accepts_expected_negative_smoke_log(tmp_path: Path) -> None:
    log = tmp_path / "expected-negative-smoke.log"
    log.write_text(
        "FAIL: targeted tests failed\n"
        "### RESULT: PASS ###\n"
        "PASS: false-pass log was rejected with exit 1\n"
        "### RESULT: PASS ###\n",
        encoding="utf-8",
    )
    result = check_terminal_log(log)
    assert result.ok
    assert result.final_result == "PASS"
