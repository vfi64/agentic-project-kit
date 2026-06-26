from __future__ import annotations

import json

from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.gui_task_editor import (
    CURRENT_USER_TASK_PATH,
    TaskEditorState,
    build_initial_llm_prompt,
    submit_user_task,
    task_editor_send_enabled,
    task_editor_state_after_read,
    task_editor_state_after_send,
    task_editor_visible_for_mode,
)


def test_initial_llm_prompt_returns_pass() -> None:
    result = build_initial_llm_prompt()

    data = result.as_json_data()
    assert data["result_status"] == "PASS"
    assert data["kind"] == "initial_llm_prompt"


def test_initial_llm_prompt_contains_go_instruction() -> None:
    text = build_initial_llm_prompt().prompt_text

    assert "g" in text
    assert "go" in text
    assert CURRENT_USER_TASK_PATH.as_posix() in text


def test_initial_llm_prompt_contains_d2_instruction() -> None:
    text = build_initial_llm_prompt().prompt_text

    assert "d2" in text
    assert "RULE_REFRESH_ACK" in text


def test_gui_initial_llm_prompt_cli_json() -> None:
    result = CliRunner().invoke(app, ["gui", "initial-llm-prompt", "--json"])

    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["result_status"] == "PASS"
    assert data["copy_paste_instruction"]


def test_submit_user_task_writes_current_task_json(tmp_path) -> None:
    result = submit_user_task(
        tmp_path,
        title="Demo",
        body="Implement the safe thing.",
        created_at_utc="2026-06-26T00:00:00+00:00",
    )

    payload = json.loads((tmp_path / CURRENT_USER_TASK_PATH).read_text(encoding="utf-8"))
    assert result.result_status == "PASS"
    assert result.remote_path == CURRENT_USER_TASK_PATH.as_posix()
    assert result.next_reply == "g"
    assert payload["title"] == "Demo"
    assert payload["body"] == "Implement the safe thing."


def test_transfer_submit_user_task_cli_json(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    body = tmp_path / "task.md"
    body.write_text("Please do the safe task.\n", encoding="utf-8")

    result = CliRunner().invoke(
        app,
        ["transfer", "submit-user-task", "--title", "Demo", "--body-file", str(body), "--json"],
    )

    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["result_status"] == "PASS"
    assert data["button_next_state"] == "SENT"
    assert (tmp_path / CURRENT_USER_TASK_PATH).exists()


def test_task_editor_send_button_disabled_when_text_empty() -> None:
    assert not task_editor_send_enabled(
        "",
        traffic_light_state="READY",
        communication_context_fresh=True,
        required_next_reply=None,
    )


def test_task_editor_send_button_disabled_when_d2_pending() -> None:
    assert not task_editor_send_enabled(
        "Do it",
        traffic_light_state="WAIT_FOR_D2",
        communication_context_fresh=False,
        required_next_reply="d2",
    )


def test_task_editor_send_transitions_to_read_on_pass() -> None:
    assert task_editor_state_after_send("PASS") == TaskEditorState.SENT
    assert task_editor_state_after_send("FAIL") == TaskEditorState.BLOCKED


def test_task_editor_read_fetches_result_state() -> None:
    assert task_editor_state_after_read("PASS") == TaskEditorState.IDLE
    assert task_editor_state_after_read("FAIL") == TaskEditorState.BLOCKED


def test_task_editor_hidden_outside_file_transfer_mode() -> None:
    assert task_editor_visible_for_mode("file_transfer")
    assert not task_editor_visible_for_mode("remote")
    assert not task_editor_visible_for_mode("copy_paste")
