from __future__ import annotations

import json
from pathlib import Path
import subprocess

from typer.testing import CliRunner
import yaml

from agentic_project_kit.cli import app
from agentic_project_kit.communication_rule_context import REQUIRED_LOADED_SECTIONS
from agentic_project_kit import transfer_repo_actions
from agentic_project_kit import gui_transfer_contract
from agentic_project_kit.command_manifest import load_manifest
from agentic_project_kit.gui_task_editor import (
    CANONICAL_REMOTE_TRANSFER_REPORT_PATH,
    CANONICAL_TRANSFER_PAYLOAD_PATH,
    CANONICAL_TRANSFER_OUTBOX_PATH,
    CURRENT_USER_TASK_PATH,
    GUI_TRANSFER_TASK_REF,
    INITIAL_LLM_PROMPT_RELATIVE_PATH,
    REMOTE_STATUS_COMMAND,
    TRANSFER_CONTINUE_COMMAND,
    TaskEditorState,
    build_terminal_launch_plan,
    build_initial_llm_prompt,
    communication_reply_contract,
    normalize_communication_mode,
    read_user_task,
    standard_command_args_for_communication_mode,
    standard_command_for_communication_mode,
    submit_user_task,
    task_editor_send_enabled,
    task_editor_state_after_read,
    task_editor_state_after_send,
    task_editor_visible_for_mode,
    transfer_state_has_canonical_outbox_result,
)


FETCH_GUI_TRANSFER_REF = (
    "fetch",
    "origin",
    gui_transfer_contract.gui_transfer_refspec(),
)
EXPECTED_GUI_TASK_NEXT_ACTION = (
    "Send g/go to the LLM; assistant must read "
    "the GUI task carrier .agentic/transfer/inbox/current.yaml from remote ref gui-transfer-tasks."
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
    assert "Bootstrap is accepted only after all required bootstrap files have been read" in text
    assert "reply exactly BOOTSTRAP_BLOCKED" in text


def test_initial_llm_prompt_contains_task_not_found_instruction() -> None:
    text = build_initial_llm_prompt().prompt_text

    assert "TASK_NOT_FOUND" in text
    assert CURRENT_USER_TASK_PATH.as_posix() in text


def test_initial_llm_prompt_forces_go_to_reread_transfer_file_and_compare_identity() -> None:
    text = build_initial_llm_prompt().prompt_text

    assert "Never answer a bare g/go from chat memory" in text
    assert "Read the task carrier first every time" in text
    assert "Extract task_id and user_task.body_sha256" in text
    assert "discard prior task context" in text


def test_initial_llm_prompt_prioritizes_transfer_result_before_gui_task_carrier() -> None:
    text = build_initial_llm_prompt().prompt_text

    assert CANONICAL_REMOTE_TRANSFER_REPORT_PATH.as_posix() in text
    assert "First inspect the latest repo-backed transfer result" in text
    assert "If no fresh transfer result exists, read the GUI task carrier" in text
    assert "neither a fresh transfer result nor the GUI task carrier" in text


def test_initial_llm_prompt_explains_three_reply_modes() -> None:
    text = build_initial_llm_prompt().prompt_text

    assert "a = remote GitHub/PR/CI work" in text
    assert "b = transfer files" in text
    assert "c = copy-and-paste fallback" in text
    assert "agentic-kit transfer patch-cycle-status --json" in text
    assert "agentic-kit transfer continue --json" in text
    assert "status: active" in text
    assert "branch: gui-transfer-tasks" in text
    assert CANONICAL_TRANSFER_PAYLOAD_PATH.as_posix() in text


def test_initial_llm_prompt_contains_rule_refresh_ack_schema() -> None:
    text = build_initial_llm_prompt().prompt_text

    assert "d2" in text
    assert "communication_rule_refresh_ack" in text
    assert "blob_sha" in text
    assert "loaded_sections" in text
    assert "rules_loaded" in text
    assert "remote_ref in the pending state" in text
    assert "sha1(\"blob \" + byte_length" in text
    assert '"remote": "<remote_ref from pending state, or main if absent>"' in text


def test_initial_llm_prompt_ack_sections_match_required_sections() -> None:
    text = build_initial_llm_prompt().prompt_text

    for section in REQUIRED_LOADED_SECTIONS:
        assert f'"{section}"' in text


def test_initial_llm_prompt_contains_stop_rules() -> None:
    text = build_initial_llm_prompt().prompt_text

    assert "BOOTSTRAP_BLOCKED" in text
    assert "TASK_NOT_FOUND" in text
    assert "RULE_REFRESH_NOT_PENDING" in text
    assert "RULE_REFRESH_ACK_BLOCKED" in text
    assert "REQUIRED_RESULT_WRAPPER_MISSING" in text


def test_initial_llm_prompt_forbids_ad_hoc_result_protocols() -> None:
    text = build_initial_llm_prompt().prompt_text

    assert "Use existing agentic-kit transfer/result wrappers" in text
    assert "Do not invent new result files, branches, refs, or ad-hoc protocols" in text


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


def test_initial_prompt_prefers_target_file(tmp_path: Path) -> None:
    target = tmp_path / INITIAL_LLM_PROMPT_RELATIVE_PATH
    target.parent.mkdir(parents=True)
    target.write_text("CUSTOM TARGET PROMPT\n", encoding="utf-8")

    result = build_initial_llm_prompt(project_root=tmp_path)

    assert result.prompt_text.startswith("CUSTOM TARGET PROMPT")
    assert "NEXT_CHAT_BOOTSTRAP.md" not in result.prompt_text
    assert "must_not_reconstruct_commands_from_memory" in result.prompt_text


def test_gui_initial_llm_prompt_cli_json_accepts_root(tmp_path: Path) -> None:
    target = tmp_path / INITIAL_LLM_PROMPT_RELATIVE_PATH
    target.parent.mkdir(parents=True)
    target.write_text("TARGET CLI PROMPT\n", encoding="utf-8")

    result = CliRunner().invoke(app, ["gui", "initial-llm-prompt", "--root", str(tmp_path), "--json"])

    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["result_status"] == "PASS"
    assert data["prompt_text"].startswith("TARGET CLI PROMPT")


def test_initial_llm_prompt_points_go_to_gui_transfer_task_ref() -> None:
    result = build_initial_llm_prompt()

    assert result.task_ref == GUI_TRANSFER_TASK_REF
    assert f"remote ref `{GUI_TRANSFER_TASK_REF}`" in result.prompt_text
    assert "Do not read this GUI task carrier from `main`" in result.prompt_text
    assert "If neither a fresh transfer result nor the GUI task carrier exists" in result.prompt_text
    assert CURRENT_USER_TASK_PATH.as_posix() == ".agentic/transfer/inbox/current.yaml"


def test_initial_llm_prompt_uses_gui_transfer_contract_constants() -> None:
    result = build_initial_llm_prompt()
    cli = CliRunner().invoke(app, ["gui", "initial-llm-prompt", "--json"])
    data = json.loads(cli.output)

    assert cli.exit_code == 0, cli.output
    assert GUI_TRANSFER_TASK_REF == gui_transfer_contract.GUI_TRANSFER_TASK_REF
    assert CURRENT_USER_TASK_PATH == gui_transfer_contract.CURRENT_USER_TASK_PATH
    assert result.task_ref == gui_transfer_contract.GUI_TRANSFER_TASK_REF
    assert result.task_path == gui_transfer_contract.CURRENT_USER_TASK_PATH.as_posix()
    assert data["task_ref"] == gui_transfer_contract.GUI_TRANSFER_TASK_REF
    assert data["task_path"] == gui_transfer_contract.CURRENT_USER_TASK_PATH.as_posix()
    assert gui_transfer_contract.GUI_TRANSFER_TASK_REF in result.prompt_text
    assert gui_transfer_contract.CURRENT_USER_TASK_PATH.as_posix() in result.prompt_text
    assert "Do not read this GUI task carrier from `main`" in result.prompt_text
    assert "docs/reports/transfer_tasks/current_user_task.json" not in result.prompt_text


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
    assert payload["manifest"] == "docs/reference/agentic-kit-commands.json"
    manifest = load_manifest(Path(".").resolve())
    assert payload["manifest_sha"] == manifest["meta"]["manifest_sha"]
    assert payload["id"] == result.task_id
    assert payload["status"] == "submitted"
    assert "remote_readable" not in payload
    assert payload["user_task"]["body"] == "Implement the safe thing."
    assert payload["communication_mode"] == "file_transfer"
    assert payload["communication_mode_code"] == "b"
    assert payload["communication_mode_label"] == "File Transfer: Transfer files"
    assert payload["task_identity"] == {
        "task_id": result.task_id,
        "body_sha256": result.body_sha256,
    }
    assert payload["g_go_handling"]["forbidden"] == "answering_g_go_from_chat_memory"
    assert payload["g_go_handling"]["read_order"] == [
        "latest_remote_transfer_report_or_outbox_first",
        "gui_task_carrier_if_no_fresh_result_exists",
    ]
    assert payload["task_carrier_contract"]["role"] == "gui_user_task_for_llm"
    assert payload["task_carrier_contract"]["status"] == "submitted"
    assert payload["task_carrier_contract"]["not_executable_by_transfer_continue"] is True
    active_reply = payload["task_carrier_contract"]["same_file_active_reply_contract"]
    assert active_reply["active_order_ref"] == GUI_TRANSFER_TASK_REF
    assert active_reply["active_order_path"] == CURRENT_USER_TASK_PATH.as_posix()
    assert active_reply["active_order_required_status"] == "active"
    assert active_reply["active_order_required_branch"] == GUI_TRANSFER_TASK_REF
    assert active_reply["python_payload_path"] == CANONICAL_TRANSFER_PAYLOAD_PATH.as_posix()
    assert payload["reply_contract"]["selected_code"] == "b"
    assert payload["reply_contract"]["selected_mode"] == "file_transfer"
    assert payload["reply_contract"]["local_execution_command"] == list(TRANSFER_CONTINUE_COMMAND)
    assert payload["reply_contract"]["mode_map"]["a"]["standard_local_command"] == list(REMOTE_STATUS_COMMAND)
    assert payload["reply_contract"]["mode_map"]["b"]["response_order_contract"] == active_reply
    assert payload["local_execution"]["standard_command"] == list(TRANSFER_CONTINUE_COMMAND)
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


def test_transfer_submit_user_task_cli_accepts_communication_mode(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    body = tmp_path / "task.md"
    body.write_text("Please do the safe task.\n", encoding="utf-8")

    result = CliRunner().invoke(
        app,
        [
            "transfer",
            "submit-user-task",
            "--title",
            "Demo",
            "--body-file",
            str(body),
            "--communication-mode",
            "copy_paste",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["communication_mode"] == "copy_paste"
    assert data["communication_mode_code"] == "c"
    assert data["local_execution_command"] == []


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
            next_action=EXPECTED_GUI_TASK_NEXT_ACTION,
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


def test_send_writes_only_canonical_carrier(
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
        if args == FETCH_GUI_TRANSFER_REF:
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
    assert result.next_action == EXPECTED_GUI_TASK_NEXT_ACTION
    assert result.communication_mode == "file_transfer"
    assert result.communication_mode_code == "b"
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
        if args == FETCH_GUI_TRANSFER_REF:
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
    assert task_editor_visible_for_mode("remote")
    assert task_editor_visible_for_mode("copy_paste")


def test_communication_reply_contracts_define_modes_and_execution_command() -> None:
    assert normalize_communication_mode("a") == "remote"
    assert normalize_communication_mode("b") == "file_transfer"
    assert normalize_communication_mode("c") == "copy_paste"

    remote_contract = communication_reply_contract("remote")
    file_contract = communication_reply_contract("file_transfer")
    copy_contract = communication_reply_contract("copy_paste")

    assert remote_contract["selected_code"] == "a"
    assert remote_contract["local_execution_command"] == list(REMOTE_STATUS_COMMAND)
    assert file_contract["selected_code"] == "b"
    assert file_contract["rules"]["forbidden"] == "answering_g_go_from_chat_memory"
    assert file_contract["rules"]["compare_task_id_and_body_sha256"] is True
    assert file_contract["rules"]["g_go_priority"] == [
        "read_latest_remote_transfer_report_or_outbox_first",
        "if_no_fresh_result_read_gui_task_carrier",
    ]
    assert file_contract["rules"]["gui_task_carrier_status"] == "submitted"
    assert file_contract["rules"]["active_transfer_order_status"] == "active"
    assert file_contract["local_execution_command"] == list(TRANSFER_CONTINUE_COMMAND)
    assert file_contract["mode_map"]["b"]["response_order_contract"]["active_order_ref"] == (
        GUI_TRANSFER_TASK_REF
    )
    assert file_contract["mode_map"]["b"]["response_order_contract"]["python_payload_path"] == (
        CANONICAL_TRANSFER_PAYLOAD_PATH.as_posix()
    )
    assert copy_contract["selected_code"] == "c"
    assert copy_contract["local_execution_command"] == []
    assert standard_command_args_for_communication_mode("a") == ("transfer", "patch-cycle-status", "--json")
    assert standard_command_args_for_communication_mode("b") == ("transfer", "continue", "--json")
    assert standard_command_args_for_communication_mode("c") == ()
    assert standard_command_for_communication_mode("a") == REMOTE_STATUS_COMMAND


def test_terminal_launch_plan_is_os_specific_and_uses_standard_transfer_command(tmp_path) -> None:
    darwin = build_terminal_launch_plan(tmp_path, communication_mode="file_transfer", platform_name="Darwin")
    windows = build_terminal_launch_plan(tmp_path, communication_mode="file_transfer", platform_name="Windows")
    remote = build_terminal_launch_plan(tmp_path, communication_mode="remote", platform_name="Darwin")
    copy_paste = build_terminal_launch_plan(tmp_path, communication_mode="copy_paste", platform_name="Darwin")

    assert darwin.result_status == "PASS"
    assert darwin.launch_argv[:3] == ("open", "-a", "Terminal")
    assert darwin.command == TRANSFER_CONTINUE_COMMAND
    assert "agentic-kit transfer continue --json" in (
        tmp_path / "tmp/agentic-kit-file-transfer-standard.command"
    ).read_text(encoding="utf-8")
    assert windows.result_status == "PASS"
    assert windows.launch_argv[:4] == ("cmd.exe", "/c", "start", "Agentic Kit Transfer")
    assert windows.command[-3:] == ("transfer", "continue", "--json")
    assert remote.command == REMOTE_STATUS_COMMAND
    assert "agentic-kit transfer patch-cycle-status --json" in (
        tmp_path / "tmp/agentic-kit-remote-standard.command"
    ).read_text(encoding="utf-8")
    assert copy_paste.command == ()
    assert "Paste the LLM recovery block here" in (
        tmp_path / "tmp/agentic-kit-copy-paste-standard.command"
    ).read_text(encoding="utf-8")


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
