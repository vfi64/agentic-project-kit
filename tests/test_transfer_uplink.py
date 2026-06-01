from __future__ import annotations

import json
import sys

from agentic_project_kit.transfer_uplink import (
    LATEST_JSON,
    LATEST_LOG,
    run_and_log_transfer_command,
    run_and_log_transfer_sequence,
)


def test_run_and_log_transfer_command_records_success_with_chat_reply(tmp_path):
    script = "print('FINAL_SIGNAL=d'); print('FINAL_NEXT=continue now'); print('CHAT_REPLY=d | NEXT=continue now')"

    result = run_and_log_transfer_command(
        [sys.executable, "-c", script],
        label="success-case",
        cwd=tmp_path,
    )

    assert result.returncode == 0
    assert result.final_signal == "d"
    assert result.chat_reply == "d"
    assert result.next_action == "continue now"
    assert (tmp_path / LATEST_LOG).exists()
    data = json.loads((tmp_path / LATEST_JSON).read_text(encoding="utf-8"))
    assert data["final_signal"] == "d"
    assert data["next_action"] == "continue now"
    assert "CHAT_REPLY=d | NEXT=continue now" in (tmp_path / LATEST_LOG).read_text(encoding="utf-8")


def test_run_and_log_transfer_command_records_failure_without_explicit_signal(tmp_path):
    result = run_and_log_transfer_command(
        [sys.executable, "-c", "import sys; print('broken'); sys.exit(3)"],
        label="failure-case",
        cwd=tmp_path,
    )

    assert result.returncode == 3
    assert result.final_signal == "f"
    assert result.chat_reply == "f"
    assert result.next_action == "Inspect latest-transfer-uplink log before continuing."
    assert "broken" in (tmp_path / LATEST_LOG).read_text(encoding="utf-8")


def test_run_sequence_stops_on_first_failure_and_keeps_overall_failure(tmp_path):
    result = run_and_log_transfer_sequence(
        [
            [sys.executable, "-c", "print('FINAL_SIGNAL=f'); print('FINAL_NEXT=fix first')"],
            [sys.executable, "-c", "print('FINAL_SIGNAL=d'); print('FINAL_NEXT=continue')"],
        ],
        label="sequence-failure",
        cwd=tmp_path,
    )

    assert result.returncode == 1
    assert result.final_signal == "f"
    assert result.chat_reply == "f"
    assert result.next_action == "fix first"
    data = json.loads((tmp_path / LATEST_JSON).read_text(encoding="utf-8"))
    assert data["final_signal"] == "f"
    assert len(data["sequence_steps"]) == 1
    log = (tmp_path / LATEST_LOG).read_text(encoding="utf-8")
    assert "TRANSFER_REPORT_WRITTEN=d" in log
    assert "TRANSFER_REPORT_PATH=docs/reports/terminal/latest-transfer-uplink.json" in log
    assert "CHAT_REPLY=f | NEXT=fix first" in log


def test_run_sequence_records_success_when_all_steps_succeed(tmp_path):
    result = run_and_log_transfer_sequence(
        [
            [sys.executable, "-c", "print('FINAL_SIGNAL=d'); print('FINAL_NEXT=step one')"],
            [sys.executable, "-c", "print('FINAL_SIGNAL=d'); print('FINAL_NEXT=step two')"],
        ],
        label="sequence-success",
        cwd=tmp_path,
    )

    assert result.returncode == 0
    assert result.final_signal == "d"
    assert result.chat_reply == "d"
    assert result.next_action == "Continue with the next safe transfer step."
    data = json.loads((tmp_path / LATEST_JSON).read_text(encoding="utf-8"))
    assert data["final_signal"] == "d"
    assert len(data["sequence_steps"]) == 2
