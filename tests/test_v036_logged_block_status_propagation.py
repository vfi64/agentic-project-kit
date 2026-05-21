from pathlib import Path


def contract_text() -> str:
    return Path("docs/governance/FINAL_SUMMARY_CONTRACT.md").read_text(encoding="utf-8")


def test_logged_block_status_propagation_guard_is_documented() -> None:
    text = contract_text()
    assert "Logged-block status propagation guard" in text
    assert "must not control final PASS or FAIL through `STATUS` mutations inside a pipeline/subshell" in text
    assert "{ ... } | tee" in text


def test_guard_explains_false_pass_risk() -> None:
    text = contract_text()
    assert "STATUS=1" in text
    assert "false PASS" in text
    assert "must not be overwritten by logging plumbing" in text


def test_guard_allows_state_preserving_log_capture() -> None:
    text = contract_text()
    assert "dedicated runner" in text
    assert "command-report path" in text
    assert "file-descriptor redirection" in text
    assert "docs/reports/terminal/" in text
