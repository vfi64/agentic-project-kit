"""G3: every BLOCKED result of the work orchestrator and of transfer commit carries the command
field (resolving Kit command, autonomous yes/no) so Cockpit and LLM need not interpret."""
from agentic_project_kit.cli_commands.human_workflows import _failed_local_step, _noop_step, _payload
from agentic_project_kit.transfer_repo_actions import RepoActionResult, result_terminal


def test_blocked_work_payload_always_has_the_command_fields():
    payload = _payload("work-finish", [_noop_step("a", ""), _failed_local_step("b", "x")])
    assert payload["result_status"] == "BLOCKED"
    assert {"next_command", "next_command_autonomous", "check_id"} <= set(payload)


def test_the_first_blocked_step_supplies_the_command():
    step = _failed_local_step("b", "x")
    step.update(next_command="agentic-kit transfer commit --message m --path a", next_command_autonomous=True,
                check_id="KIT-CHK-INDEX-LOCK")
    payload = _payload("work-finish", [step, _failed_local_step("c", "y")])
    assert payload["next_command"].startswith("agentic-kit transfer commit")
    assert payload["next_command_autonomous"] is True and payload["check_id"] == "KIT-CHK-INDEX-LOCK"


def test_passing_payload_is_unchanged():
    assert "next_command" not in _payload("work-finish", [_noop_step("a", "")])


def test_repo_action_result_carries_and_prints_the_command():
    result = RepoActionResult("commit", "BLOCKED", 128, ["git", "add"], "", "lock", "wait",
                              next_command="agentic-kit transfer commit --message m", next_command_autonomous=True)
    data = result.as_json_data()
    assert data["next_command"] and data["next_command_autonomous"] is True
    assert "NEXT_COMMAND" in result_terminal(result)
