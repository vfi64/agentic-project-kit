from pathlib import Path


def test_no_copy_policy_requires_f_for_normal_fail() -> None:
    text = Path("docs/workflow/NO_COPY_TERMINAL_EVIDENCE.md").read_text(encoding="utf-8")
    assert "Normal FAIL handoff must use f and repo-backed evidence" in text
    assert "Manual terminal output is required only when FAIL evidence is unavailable" in text
    assert "Manual terminal output is required only for FAIL," not in text


def test_handoff_state_records_f_for_log_backed_fail() -> None:
    text = Path(".agentic/handoff_state.yaml").read_text(encoding="utf-8")
    assert "use d for log-backed PASS and f for log-backed FAIL" in text
    assert "Manual terminal" in text
