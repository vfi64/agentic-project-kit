from pathlib import Path

from agentic_project_kit.next_turn_status import (
    detect_next_turn_status,
    find_last_result,
    render_last_result,
    render_status,
)


def test_next_turn_status_empty_slot(tmp_path: Path) -> None:
    status = detect_next_turn_status(tmp_path)
    assert status.state == "empty"
    assert status.overwrite_allowed is True
    rendered = render_status(status)
    assert "state=empty" in rendered
    assert "docs/reports/command_runs/next-turn-latest.json" in rendered


def test_next_turn_status_blocks_partial_slot(tmp_path: Path) -> None:
    commands = tmp_path / ".agentic" / "commands"
    commands.mkdir(parents=True)
    (commands / "next-turn.yaml").write_text("state: prepared\n", encoding="utf-8")
    status = detect_next_turn_status(tmp_path)
    assert status.state == "blocked"
    assert status.overwrite_allowed is False
    assert status.reason == "partial fixed-slot state"


def test_next_turn_status_reads_declared_state(tmp_path: Path) -> None:
    commands = tmp_path / ".agentic" / "commands"
    commands.mkdir(parents=True)
    (commands / "next-turn.yaml").write_text("id: next-turn\nstate: running\n", encoding="utf-8")
    (commands / "next-turn.py").write_text("pass\n", encoding="utf-8")
    status = detect_next_turn_status(tmp_path)
    assert status.state == "running"
    assert status.overwrite_allowed is False
    assert "running slot must not be overwritten" in status.reason


def test_next_turn_last_result_no_result_is_clean_state(tmp_path: Path) -> None:
    rendered = render_last_result(tmp_path)
    assert "status=NO_RESULT_FOUND" in rendered
    assert "docs/reports/terminal/next-turn-latest.log" in rendered
    assert "### RESULT: PASS ###" in rendered


def test_next_turn_last_result_prefers_json(tmp_path: Path) -> None:
    result_dir = tmp_path / "docs" / "reports" / "command_runs"
    result_dir.mkdir(parents=True)
    (result_dir / "next-turn-latest.json").write_text("{\"overall_result\": \"PASS\"}", encoding="utf-8")
    rendered = render_last_result(tmp_path)
    assert "status=FOUND" in rendered
    assert "next-turn-latest.json" in rendered
    assert "\"overall_result\": \"PASS\"" in rendered

def test_next_turn_last_result_classifies_json_failure_with_remote_evidence(tmp_path: Path) -> None:
    result_dir = tmp_path / "docs" / "reports" / "command_runs"
    result_dir.mkdir(parents=True)
    (result_dir / "next-turn-latest.json").write_text(
        "{\"overall_result\": \"FAIL\", \"remote_evidence\": \"PASS\", \"next_chat_reply\": \"f\"}",
        encoding="utf-8",
    )
    result = find_last_result(tmp_path)
    assert result.status == "FOUND_FAIL"
    assert result.evidence_verdict == "FAIL_DIAGNOSE"
    assert result.recommended_chat_reply == "f"
    rendered = render_last_result(tmp_path)
    assert "status=FOUND_FAIL" in rendered
    assert "recommended_chat_reply=f" in rendered


def test_next_turn_last_result_classifies_terminal_fail_when_no_json(tmp_path: Path) -> None:
    terminal_dir = tmp_path / "docs" / "reports" / "terminal"
    terminal_dir.mkdir(parents=True)
    (terminal_dir / "next-turn-latest.log").write_text("boom\n### RESULT: FAIL ###\n", encoding="utf-8")
    result = find_last_result(tmp_path)
    assert result.status == "FOUND_FAIL"
    assert result.evidence_verdict == "FAIL_DIAGNOSE"
    assert result.recommended_chat_reply == "f"


def test_next_turn_last_result_missing_result_recommends_paste_output_only_after_lookup(tmp_path: Path) -> None:
    result = find_last_result(tmp_path)
    assert result.status == "NO_RESULT_FOUND"
    assert result.evidence_verdict == "MISSING_EVIDENCE_UPLOAD_FIRST"
    assert result.recommended_chat_reply == "paste-output"
    assert "next-turn --status" in result.recovery


def test_next_turn_last_result_classifies_executed_jsonl_pass(tmp_path: Path) -> None:
    ledger = tmp_path / ".agentic" / "commands" / "executed.jsonl"
    ledger.parent.mkdir(parents=True)
    ledger.write_text(
        '{"command_id": "ledger-pass", "exit_code": 0, "outcome": "PASS_EXECUTED"}\n',
        encoding="utf-8",
    )
    result = find_last_result(tmp_path)
    assert result.status == "FOUND_PASS"
    assert result.evidence_verdict == "PASS_CONTINUE"
    assert result.recommended_chat_reply == "d"
    assert "executed command ledger" in result.recovery


def test_next_turn_last_result_classifies_executed_jsonl_fail(tmp_path: Path) -> None:
    ledger = tmp_path / ".agentic" / "commands" / "executed.jsonl"
    ledger.parent.mkdir(parents=True)
    ledger.write_text(
        '{"command_id": "ledger-fail", "exit_code": 7, "outcome": "FAIL_EXECUTED"}\n',
        encoding="utf-8",
    )
    result = find_last_result(tmp_path)
    assert result.status == "FOUND_FAIL"
    assert result.evidence_verdict == "FAIL_DIAGNOSE"
    assert result.recommended_chat_reply == "f"


def test_next_turn_last_result_classifies_unreadable_executed_jsonl_as_unusable(tmp_path: Path) -> None:
    ledger = tmp_path / ".agentic" / "commands" / "executed.jsonl"
    ledger.parent.mkdir(parents=True)
    ledger.write_text('not json\n', encoding="utf-8")
    result = find_last_result(tmp_path)
    assert result.status == "FOUND_UNUSABLE"
    assert result.evidence_verdict == "AMBIGUOUS_SUMMARY_REVIEW_REQUIRED"
    assert result.recommended_chat_reply == "paste-output"
