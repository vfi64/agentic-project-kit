from __future__ import annotations

import json
import subprocess

from typer.testing import CliRunner
import yaml

from agentic_project_kit.cli import app
from agentic_project_kit.communication_rule_context import REQUIRED_LOADED_SECTIONS
from agentic_project_kit import transfer_repo_actions
from agentic_project_kit.gui_task_editor import (
    CANONICAL_TRANSFER_OUTBOX_PATH,
    CURRENT_USER_TASK_PATH,
    GUI_TRANSFER_TASK_REF,
    TaskEditorState,
    build_initial_llm_prompt,
    read_user_task,
    submit_user_task,
    task_editor_send_enabled,
    task_editor_state_after_read,
    task_editor_state_after_send,
    task_editor_visible_for_mode,
    transfer_state_has_canonical_outbox_result,
)


def test_initial_llm_prompt_returns_pass() -> None:
    result = build_initial_llm_prompt()

    data = result.as_json_data()
    assert data["result_status"] == "PASS"
    assert data["kind"] == "initial_llm_prompt"


def test_initial_llm_prompt_contains_bootstrap_block() -> None:
    text = build_initial_llm_prompt().prompt_text

    assert "NEXT_CHAT_BOOTSTRAP.md" in text
    assert "successor_prompt.md" in text
    assert "validation_report.json" in text
    assert "source_manifest.json" in text
    assert "execution_contract.json" in text


def test_initial_llm_prompt_contains_task_not_found_instruction() -> None:
    text = build_initial_llm_prompt().prompt_text

    assert "TASK_NOT_FOUND" in text
    assert CURRENT_USER_TASK_PATH.as_posix() in text


def test_initial_llm_prompt_contains_rule_refresh_ack_schema() -> None:
    text = build_initial_llm_prompt().prompt_text

    assert "d2" in text
    assert "communication_rule_refresh_ack" in text
    assert "blob_sha" in text
    assert "loaded_sections" in text
    assert "rules_loaded" in text


def test_initial_llm_prompt_ack_sections_match_required_sections() -> None:
    text = build_initial_llm_prompt().prompt_text

    for section in REQUIRED_LOADED_SECTIONS:
        assert f'"{section}"' in text


def test_initial_llm_prompt_contains_stop_rules() -> None:
    text = build_initial_llm_prompt().prompt_text

    assert "TASK_NOT_FOUND" in text
    assert "RULE_REFRESH_NOT_PENDING" in text
    assert "RULE_REFRESH_ACK_BLOCKED" in text


def test_initial_llm_prompt_copy_paste_instruction_updated() -> None:
    instruction = build_initial_llm_prompt().copy_paste_instruction

    assert "bootstrap files" in instruction


def test_gui_initial_llm_prompt_cli_json() -> None:
    result = CliRunner().invoke(app, ["gui", "initial-llm-prompt", "--json"])

    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["result_status"] == "PASS"
    assert data["copy_paste_instruction"]
    assert data["task_ref"] == GUI_TRANSFER_TASK_REF
    assert GUI_TRANSFER_TASK_REF in data["prompt_text"]


def test_initial_llm_prompt_points_go_to_gui_transfer_task_ref() -> None:
    result = build_initial_llm_prompt()

    assert result.task_ref == GUI_TRANSFER_TASK_REF
    assert f"remote ref `{GUI_TRANSFER_TASK_REF}`" in result.prompt_text
    assert "Do not read this transfer order from `main`" in result.prompt_text
    assert "If the ref or file does not exist" in result.prompt_text
    assert CURRENT_USER_TASK_PATH.as_posix() == ".agentic/transfer/inbox/current.yaml"


def test_submit_user_task_writes_canonical_transfer_inbox(tmp_path) -> None:
    result = submit_user_task(
        tmp_path,
        title="Demo",
        body="Implement the safe thing.",
        created_at_utc="2026-06-26T00:00:00+00:00",
    )

    payload = yaml.safe_load((tmp_path / CURRENT_USER_TASK_PATH).read_text(encoding="utf-8"))
    assert result.result_status == "PASS"
    assert result.remote_path == CURRENT_USER_TASK_PATH.as_posix()
    assert result.task_path == CURRENT_USER_TASK_PATH.as_posix()
    assert result.next_reply == "g"
    assert result.published_ref is None
    assert result.local_only is True
    assert result.remote_readable is False
    assert result.blob_sha == ""
    assert result.commit_status == "SKIPPED"
    assert result.push_status == "SKIPPED"
    assert result.button_next_state == TaskEditorState.BLOCKED.value
    assert payload["title"] == "Demo"
    assert payload["kind"] == "gui_user_task_transfer_order"
    assert payload["id"] == result.task_id
    assert payload["status"] == "active"
    assert payload["user_task"]["body"] == "Implement the safe thing."
    assert payload["actions"][0]["command"] == [
        "./.venv/bin/agentic-kit",
        "transfer",
        "state",
        "--json",
    ]


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
    assert data["button_next_state"] == "BLOCKED"
    assert data["task_path"] == CURRENT_USER_TASK_PATH.as_posix()
    assert data["published_ref"] is None
    assert data["local_only"] is True
    assert data["remote_readable"] is False
    assert (tmp_path / CURRENT_USER_TASK_PATH).exists()


def test_transfer_submit_user_task_cli_publish_json(tmp_path, monkeypatch) -> None:
    import agentic_project_kit.gui_task_editor as task_editor

    monkeypatch.chdir(tmp_path)
    body = tmp_path / "task.md"
    body.write_text("Please publish the safe task.\n", encoding="utf-8")

    def fake_submit(project_root, *, title, body, publish=False, **_kwargs):
        return task_editor.SubmittedUserTask(
            result_status="PASS",
            kind="gui_file_transfer_user_task_submission",
            task_id="task123",
            title=title,
            remote_path=CURRENT_USER_TASK_PATH.as_posix(),
            task_path=CURRENT_USER_TASK_PATH.as_posix(),
            published_ref=GUI_TRANSFER_TASK_REF,
            next_reply="g",
            next_action=(
                "Send g/go to the LLM; assistant must read the transfer order from ref gui-transfer-tasks."
            ),
            button_next_state=TaskEditorState.SENT.value,
            body_sha256="sha",
            created_at_utc="2026-06-26T00:00:00+00:00",
            head_sha="head",
            blob_sha="blob123",
            commit_status="PASS",
            push_status="PASS",
            local_only=False,
            remote_readable=publish,
            reason="remote_carrier_verified",
        )

    monkeypatch.setattr(task_editor, "submit_user_task", fake_submit)

    result = CliRunner().invoke(
        app,
        ["transfer", "submit-user-task", "--title", "Demo", "--body-file", str(body), "--publish", "--json"],
    )

    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["published_ref"] == GUI_TRANSFER_TASK_REF
    assert data["remote_path"] == CURRENT_USER_TASK_PATH.as_posix()
    assert data["remote_readable"] is True
    assert data["blob_sha"] == "blob123"
    assert data["commit_status"] == "PASS"
    assert data["push_status"] == "PASS"
    assert data["next_reply"] == "g"


def test_submit_user_task_publish_uses_gui_transfer_branch_and_verifies_remote(
    tmp_path,
    monkeypatch,
) -> None:
    calls: list[object] = []

    def fake_git_runner(root, args):
        calls.append(("git", args))
        if args == ("branch", "--show-current"):
            return subprocess.CompletedProcess(["git", *args], 0, "main\n", "")
        if args == ("rev-parse", "HEAD"):
            return subprocess.CompletedProcess(["git", *args], 0, "abc123\n", "")
        if args == ("rev-parse", "--short", "HEAD"):
            return subprocess.CompletedProcess(["git", *args], 0, "abc123\n", "")
        if args == ("rev-parse", "origin/main"):
            return subprocess.CompletedProcess(["git", *args], 0, "originmain123\n", "")
        if args == ("fetch", "origin", GUI_TRANSFER_TASK_REF):
            return subprocess.CompletedProcess(["git", *args], 0, "", "")
        if args == ("rev-parse", "--verify", "--quiet", GUI_TRANSFER_TASK_REF):
            return subprocess.CompletedProcess(["git", *args], 1, "", "")
        if args == ("rev-parse", "--verify", "--quiet", f"origin/{GUI_TRANSFER_TASK_REF}"):
            return subprocess.CompletedProcess(["git", *args], 1, "", "")
        if args == (
            "rev-parse",
            "--verify",
            f"origin/{GUI_TRANSFER_TASK_REF}:{CURRENT_USER_TASK_PATH.as_posix()}",
        ):
            return subprocess.CompletedProcess(["git", *args], 0, "blob123\n", "")
        if args == ("show", f"origin/{GUI_TRANSFER_TASK_REF}:{CURRENT_USER_TASK_PATH.as_posix()}"):
            payload = (tmp_path / CURRENT_USER_TASK_PATH).read_text(encoding="utf-8")
            return subprocess.CompletedProcess(["git", *args], 0, payload, "")
        return subprocess.CompletedProcess(["git", *args], 99, "", f"unexpected git args: {args}")

    def repo_result(action: str, status: str = "PASS"):
        return transfer_repo_actions.RepoActionResult(
            action=action,
            result_status=status,
            returncode=0 if status == "PASS" else 2,
            command=[action],
            stdout="ok\n",
            stderr="",
            next_action="next",
        )

    monkeypatch.setattr(
        transfer_repo_actions,
        "branch_create",
        lambda branch, start_point="main": calls.append(("branch_create", branch, start_point))
        or repo_result("branch-create"),
    )
    monkeypatch.setattr(
        transfer_repo_actions,
        "commit_paths",
        lambda message, paths, required_branch="", allow_main=False: calls.append(
            ("commit_paths", message, tuple(paths), required_branch, allow_main)
        )
        or repo_result("commit"),
    )
    monkeypatch.setattr(
        transfer_repo_actions,
        "push_current",
        lambda required_branch="": calls.append(("push_current", required_branch))
        or repo_result("push-current"),
    )
    monkeypatch.setattr(
        transfer_repo_actions,
        "branch_switch",
        lambda branch, pull=False: calls.append(("branch_switch", branch, pull))
        or repo_result("branch-switch"),
    )

    result = submit_user_task(
        tmp_path,
        title="Demo",
        body="Publish this task.",
        publish=True,
        created_at_utc="2026-06-26T00:00:00+00:00",
        git_runner=fake_git_runner,
    )

    assert result.result_status == "PASS"
    assert result.published_ref == GUI_TRANSFER_TASK_REF
    assert result.remote_path == CURRENT_USER_TASK_PATH.as_posix()
    assert result.remote_readable is True
    assert result.blob_sha == "blob123"
    assert result.commit_status == "PASS"
    assert result.push_status == "PASS"
    assert result.local_only is False
    assert result.button_next_state == TaskEditorState.SENT.value
    assert result.next_reply == "g"
    assert (
        result.next_action
        == "Send g/go to the LLM; assistant must read the transfer order from ref gui-transfer-tasks."
    )
    assert ("branch_create", GUI_TRANSFER_TASK_REF, "main") in calls
    assert (
        "commit_paths",
        "Publish GUI transfer order",
        (CURRENT_USER_TASK_PATH.as_posix(),),
        GUI_TRANSFER_TASK_REF,
        False,
    ) in calls
    assert ("push_current", GUI_TRANSFER_TASK_REF) in calls
    assert ("branch_switch", "main", False) in calls
    assert ("git", ("rev-parse", "--verify", f"origin/{GUI_TRANSFER_TASK_REF}:{CURRENT_USER_TASK_PATH.as_posix()}")) in calls


def test_submit_user_task_publish_does_not_mark_remote_readable_without_verification(
    tmp_path,
    monkeypatch,
) -> None:
    def fake_git_runner(root, args):
        if args == ("branch", "--show-current"):
            return subprocess.CompletedProcess(["git", *args], 0, "main\n", "")
        if args == ("rev-parse", "HEAD"):
            return subprocess.CompletedProcess(["git", *args], 0, "abc123\n", "")
        if args == ("rev-parse", "--short", "HEAD"):
            return subprocess.CompletedProcess(["git", *args], 0, "abc123\n", "")
        if args == ("rev-parse", "origin/main"):
            return subprocess.CompletedProcess(["git", *args], 0, "originmain123\n", "")
        if args == ("fetch", "origin", GUI_TRANSFER_TASK_REF):
            return subprocess.CompletedProcess(["git", *args], 0, "", "")
        if args == ("rev-parse", "--verify", "--quiet", GUI_TRANSFER_TASK_REF):
            return subprocess.CompletedProcess(["git", *args], 1, "", "")
        if args == ("rev-parse", "--verify", "--quiet", f"origin/{GUI_TRANSFER_TASK_REF}"):
            return subprocess.CompletedProcess(["git", *args], 1, "", "")
        if args == (
            "rev-parse",
            "--verify",
            f"origin/{GUI_TRANSFER_TASK_REF}:{CURRENT_USER_TASK_PATH.as_posix()}",
        ):
            return subprocess.CompletedProcess(["git", *args], 1, "", "missing\n")
        return subprocess.CompletedProcess(["git", *args], 0, "", "")

    def repo_result(action: str):
        return transfer_repo_actions.RepoActionResult(
            action=action,
            result_status="PASS",
            returncode=0,
            command=[action],
            stdout="ok\n",
            stderr="",
            next_action="next",
        )

    monkeypatch.setattr(transfer_repo_actions, "branch_create", lambda branch, start_point="main": repo_result("branch-create"))
    monkeypatch.setattr(transfer_repo_actions, "commit_paths", lambda message, paths, required_branch="", allow_main=False: repo_result("commit"))
    monkeypatch.setattr(transfer_repo_actions, "push_current", lambda required_branch="": repo_result("push-current"))
    monkeypatch.setattr(transfer_repo_actions, "branch_switch", lambda branch, pull=False: repo_result("branch-switch"))

    result = submit_user_task(
        tmp_path,
        title="Demo",
        body="Publish this task.",
        publish=True,
        created_at_utc="2026-06-26T00:00:00+00:00",
        git_runner=fake_git_runner,
    )

    assert result.result_status == "FAIL"
    assert result.remote_readable is False
    assert result.blob_sha == ""
    assert result.commit_status == "PASS"
    assert result.push_status == "PASS"
    assert result.reason == "remote_blob_missing"
    assert result.button_next_state == TaskEditorState.BLOCKED.value


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


def test_task_editor_send_transitions_to_read_only_when_remote_readable() -> None:
    assert task_editor_state_after_send("PASS", remote_readable=True) == TaskEditorState.SENT
    assert task_editor_state_after_send("PASS", remote_readable=False) == TaskEditorState.BLOCKED
    assert task_editor_state_after_send("FAIL", remote_readable=True) == TaskEditorState.BLOCKED


def test_task_editor_read_fetches_result_state() -> None:
    assert task_editor_state_after_read("PASS") == TaskEditorState.IDLE
    assert task_editor_state_after_read("FAIL") == TaskEditorState.BLOCKED


def test_transfer_state_outbox_result_detector_uses_canonical_transfer_file() -> None:
    assert transfer_state_has_canonical_outbox_result(
        {
            "transfer_files": {
                "outbox": {
                    "last_result": {
                        "path": CANONICAL_TRANSFER_OUTBOX_PATH.as_posix(),
                        "exists": True,
                    }
                }
            }
        }
    )
    assert not transfer_state_has_canonical_outbox_result({"outbox": {"last_result": {"exists": False}}})
    assert not transfer_state_has_canonical_outbox_result({"task_path": CURRENT_USER_TASK_PATH.as_posix()})


def test_task_editor_hidden_outside_file_transfer_mode() -> None:
    assert task_editor_visible_for_mode("file_transfer")
    assert not task_editor_visible_for_mode("remote")
    assert not task_editor_visible_for_mode("copy_paste")


def test_read_user_task_missing_reports_task_not_found(tmp_path) -> None:
    result = read_user_task(tmp_path)

    assert result["result_status"] == "FAIL"
    assert result["reason"] == "TASK_NOT_FOUND"
    assert result["task_path"] == CURRENT_USER_TASK_PATH.as_posix()


def test_read_user_task_reads_submit_path(tmp_path) -> None:
    submit_user_task(
        tmp_path,
        title="Demo",
        body="Implement the safe thing.",
        created_at_utc="2026-06-26T00:00:00+00:00",
    )

    result = read_user_task(tmp_path)

    assert result["result_status"] == "PASS"
    assert result["task_path"] == CURRENT_USER_TASK_PATH.as_posix()
    assert result["task"]["title"] == "Demo"
    assert result["task"]["user_task"]["body"] == "Implement the safe thing."


def test_transfer_read_user_task_cli_reports_missing(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(app, ["transfer", "read-user-task", "--json"])

    assert result.exit_code == 2
    data = json.loads(result.output)
    assert data["reason"] == "TASK_NOT_FOUND"
