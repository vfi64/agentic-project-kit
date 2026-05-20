import json

from typer.testing import CliRunner

from agentic_project_kit.cli import app

runner = CliRunner()


def test_cockpit_run_json_outputs_machine_readable_action_result() -> None:
    result = runner.invoke(app, ["cockpit", "run", "git.status", "--json"])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["schema_version"] == 1
    assert data["action_id"] == "git.status"
    assert data["result_status"] in {"PASS", "FAIL"}
    assert data["allowed"] is True
    assert data["executed"] is True
    assert data["safety"] == "read_only"
    assert data["dirty_state"] == "unknown"
    assert "terminal_log" in data
    assert "command_report" in data
    assert "next_allowed_actions" in data


def test_cockpit_run_json_preserves_blocked_bounded_contract_and_exit_code() -> None:
    result = runner.invoke(app, ["cockpit", "run", "workflow.go", "--json"])
    assert result.exit_code == 2
    data = json.loads(result.output)
    assert data["result_status"] == "PENDING"
    assert data["allowed"] is False
    assert data["executed"] is False
    assert data["safety"] == "bounded"
