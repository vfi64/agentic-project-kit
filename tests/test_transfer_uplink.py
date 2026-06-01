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
    assert result.chat_reply == "g"
    assert result.next_action == "continue now"
    assert (tmp_path / LATEST_LOG).exists()
    assert result.transfer_upload == "done"
    assert result.remote_report_path.startswith("docs/reports/transfer_runs/")
    assert (tmp_path / result.remote_report_path).exists()
    data = json.loads((tmp_path / LATEST_JSON).read_text(encoding="utf-8"))
    assert data["final_signal"] == "d"
    assert data["next_action"] == "continue now"
    assert "CHAT_REPLY=g" in (tmp_path / LATEST_LOG).read_text(encoding="utf-8")


def test_run_and_log_transfer_command_records_failure_without_explicit_signal(tmp_path):
    result = run_and_log_transfer_command(
        [sys.executable, "-c", "import sys; print('broken'); sys.exit(3)"],
        label="failure-case",
        cwd=tmp_path,
    )

    assert result.returncode == 3
    assert result.final_signal == "f"
    assert result.chat_reply == "g"
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
    assert result.chat_reply == "g"
    assert result.next_action == "fix first"
    data = json.loads((tmp_path / LATEST_JSON).read_text(encoding="utf-8"))
    assert data["final_signal"] == "f"
    assert len(data["sequence_steps"]) == 1
    log = (tmp_path / LATEST_LOG).read_text(encoding="utf-8")
    assert "TRANSFER_UPLOAD=done" in log
    assert "REMOTE_REPORT=docs/reports/transfer_runs/" in log
    assert "CHAT_REPLY=g" in log


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
    assert result.chat_reply == "g"
    assert result.next_action == "Continue with the next safe transfer step."
    data = json.loads((tmp_path / LATEST_JSON).read_text(encoding="utf-8"))
    assert data["final_signal"] == "d"
    assert len(data["sequence_steps"]) == 2

def test_run_and_log_cli_prints_only_human_go_lines(tmp_path, monkeypatch):
    from typer.testing import CliRunner
    from agentic_project_kit.cli import app

    monkeypatch.chdir(tmp_path)
    script = "print('FINAL_SIGNAL=d'); print('FINAL_NEXT=continue now')"

    result = CliRunner().invoke(
        app,
        ["transfer", "run-and-log", "--label", "quiet-ok", "--", sys.executable, "-c", script],
    )

    assert result.exit_code == 0
    lines = result.stdout.splitlines()
    assert lines[0] == "TRANSFER_UPLOAD=done"
    assert lines[1].startswith("REMOTE_REPORT=docs/reports/transfer_runs/")
    assert lines[2] == "CHAT_REPLY=g"
    assert len(lines) == 3
    report_path = lines[1].split("=", 1)[1]
    data = json.loads((tmp_path / report_path).read_text(encoding="utf-8"))
    assert data["final_signal"] == "d"
    assert data["chat_reply"] == "g"


def test_run_sequence_cli_prints_go_even_when_step_failed_but_report_written(tmp_path, monkeypatch):
    from typer.testing import CliRunner
    from agentic_project_kit.cli import app

    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(
        app,
        [
            "transfer",
            "run-sequence-and-log",
            "--label",
            "quiet-fail",
            "--step",
            f"{sys.executable} -c \"import sys; print('broken'); sys.exit(3)\"",
        ],
    )

    assert result.exit_code == 3
    lines = result.stdout.splitlines()
    assert lines[0] == "TRANSFER_UPLOAD=done"
    assert lines[1].startswith("REMOTE_REPORT=docs/reports/transfer_runs/")
    assert lines[2] == "CHAT_REPLY=g"
    assert len(lines) == 3
    report_path = lines[1].split("=", 1)[1]
    data = json.loads((tmp_path / report_path).read_text(encoding="utf-8"))
    assert data["final_signal"] == "f"
    assert data["returncode"] == 3

