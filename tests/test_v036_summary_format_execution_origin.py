from pathlib import Path


def contract_text() -> str:
    return Path("docs/governance/FINAL_SUMMARY_CONTRACT.md").read_text(encoding="utf-8")


def test_summary_contract_has_slice_block() -> None:
    text = contract_text()
    assert "SLICE" in text
    assert "NAME: <slice-name>" in text
    assert "SCOPE: <short scope>" in text
    assert "BRANCH: <branch-or-NONE>" in text


def test_summary_contract_has_execution_origin_block() -> None:
    text = contract_text()
    assert "EXECUTION" in text
    assert "ORIGIN: local|remote|mixed" in text
    assert "STATE_MODE: local|remote|unknown" in text
    assert "MODE_CHECK: pass|fail|not_run" in text
    assert "SWITCH_HINT: ./ns mode-write local|remote && ./ns mode-check local|remote" in text


def test_summary_contract_uses_grouped_readable_fields() -> None:
    text = contract_text()
    for section in ["RESULT", "REMOTE", "EVIDENCE FILES", "INTERPRETATION", "NEXT"]:
        assert section in text
    assert "CHAT_REPLY: d|f|w|paste-output|stop" in text
    assert "SAFE_STEP: <next concrete action>" in text
