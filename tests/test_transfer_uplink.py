from __future__ import annotations

import json
import sys

from agentic_project_kit.transfer_uplink import (
    LATEST_JSON,
    LATEST_LOG,
    run_and_log_transfer_command,
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
