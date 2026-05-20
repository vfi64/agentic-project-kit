from pathlib import Path

from agentic_project_kit.cockpit import (
    CockpitAction,
    RESULT_FAIL,
    RESULT_HARD_FAIL,
    RESULT_PASS,
    RESULT_PENDING,
    action_result_as_json_data,
    run_cockpit_action,
)

class CompletedOk:
    returncode = 0
    stdout = "ok\\n"
    stderr = ""

class CompletedFail:
    returncode = 7
    stdout = ""
    stderr = "boom"

def test_read_only_action_result_contract_pass(tmp_path: Path) -> None:
    result = run_cockpit_action("git.status", tmp_path, executor=lambda command, root: CompletedOk())
    data = action_result_as_json_data(result)
    assert data["schema_version"] == 1
    assert data["result_status"] == RESULT_PASS
    assert data["allowed"] is True
    assert data["executed"] is True
    assert data["returncode"] == 0
    assert data["safety"] == "read_only"
    assert data["dirty_state"] == "unknown"
    assert data["terminal_log"] is None
    assert data["command_report"] is None
    assert data["next_allowed_actions"] == ["cockpit.actions"]

def test_read_only_action_result_contract_fail(tmp_path: Path) -> None:
    result = run_cockpit_action("git.status", tmp_path, executor=lambda command, root: CompletedFail())
    assert result.result_status == RESULT_FAIL
    assert result.returncode == 7
    assert result.stderr == "boom"

def test_bounded_action_without_allow_is_pending_contract(tmp_path: Path) -> None:
    result = run_cockpit_action("workflow.go", tmp_path)
    assert result.allowed is False
    assert result.executed is False
    assert result.result_status == RESULT_PENDING
    assert result.safety == "bounded"

def test_destructive_action_is_hard_fail_contract(tmp_path: Path) -> None:
    actions = [CockpitAction("git.push", "Git push", "git", ("git", "push"), "destructive", "Push changes.")]
    result = run_cockpit_action("git.push", tmp_path, actions=actions)
    assert result.allowed is False
    assert result.executed is False
    assert result.result_status == RESULT_HARD_FAIL
