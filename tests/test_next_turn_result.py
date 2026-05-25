from __future__ import annotations

import json
from pathlib import Path

from agentic_project_kit.next_turn_result import (
    publish_local_evidence,
    build_result,
    classify_next_chat_reply,
    render_summary,
    result_paths,
    write_result,
)


def test_classify_next_chat_reply_pass() -> None:
    assert classify_next_chat_reply("PASS", "NOT_REQUIRED") == "d"
    assert classify_next_chat_reply("PASS_ALREADY_DONE", "PARTIAL") == "d"
    assert classify_next_chat_reply("NOOP", "PASS") == "d"


def test_classify_next_chat_reply_fail_with_remote_evidence() -> None:
    assert classify_next_chat_reply("FAIL", "PASS") == "f"
    assert classify_next_chat_reply("FAIL", "PARTIAL") == "f"


def test_classify_next_chat_reply_fail_without_remote_evidence() -> None:
    assert classify_next_chat_reply("FAIL", "FAIL") == "paste-output"


def test_write_result_writes_report_and_latest(tmp_path: Path) -> None:
    result = build_result(
        run_id="example-run",
        work_result="FAIL",
        evidence_result="LOCAL_LOG",
        remote_evidence="PASS",
        terminal_log="/tmp/example.log",
        remote_terminal_log="docs/reports/terminal/example-run.log",
        reason="test",
    )
    report, latest = write_result(result, tmp_path)
    assert report.exists()
    assert latest.exists()
    payload = json.loads(report.read_text(encoding="utf-8"))
    latest_payload = json.loads(latest.read_text(encoding="utf-8"))
    assert payload == latest_payload
    assert payload["next_chat_reply"] == "f"
    assert payload["remote_evidence"] == "PASS"


def test_result_paths_are_repo_relative(tmp_path: Path) -> None:
    report, latest, terminal = result_paths("abc", tmp_path)
    assert report.as_posix().endswith("docs/reports/command_runs/abc.json")
    assert latest.as_posix().endswith("docs/reports/command_runs/next-turn-latest.json")
    assert terminal.as_posix().endswith("docs/reports/terminal/abc.log")


def test_render_summary_contains_contract_lines() -> None:
    result = build_result(
        run_id="summary-run",
        work_result="PASS",
        evidence_result="PASS",
        remote_evidence="PASS",
    )
    summary = render_summary(result)
    assert "WORK RESULT: PASS" in summary
    assert "REMOTE_EVIDENCE: PASS" in summary
    assert "NEXT_CHAT_REPLY: d" in summary
    assert "### RESULT: PASS ###" in summary


def test_publish_local_evidence_copies_log_and_writes_result(tmp_path: Path) -> None:
    source = tmp_path / "local.log"
    source.write_text("hello evidence\n", encoding="utf-8")
    result = publish_local_evidence(
        run_id="publish-run",
        local_terminal_log=source,
        work_result="FAIL",
        root=tmp_path,
        reason="publish test",
    )
    assert result.remote_evidence == "PARTIAL"
    assert result.next_chat_reply == "f"
    remote_log = tmp_path / "docs" / "reports" / "terminal" / "publish-run.log"
    report = tmp_path / "docs" / "reports" / "command_runs" / "publish-run.json"
    latest = tmp_path / "docs" / "reports" / "command_runs" / "next-turn-latest.json"
    assert remote_log.read_text(encoding="utf-8") == "hello evidence\n"
    assert report.exists()
    assert latest.exists()


def test_publish_local_evidence_missing_log_records_failure(tmp_path: Path) -> None:
    result = publish_local_evidence(
        run_id="missing-log",
        local_terminal_log=tmp_path / "missing.log",
        work_result="FAIL",
        root=tmp_path,
    )
    assert result.remote_evidence == "FAIL"
    assert result.next_chat_reply == "paste-output"
    report = tmp_path / "docs" / "reports" / "command_runs" / "missing-log.json"
    assert report.exists()
