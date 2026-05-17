import json
from pathlib import Path

from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.cockpit import BOUNDED, DESTRUCTIVE, READ_ONLY, CockpitAction, action_by_id, action_inventory_as_json_data, cockpit_actions, render_action_selection, run_cockpit_action


runner = CliRunner()


def test_cockpit_action_registry_contains_core_read_only_actions() -> None:
    action_ids = {action.action_id for action in cockpit_actions()}
    assert "git.status" in action_ids
    assert "workflow.state" in action_ids
    assert "gate.doctor" in action_ids
    assert "gate.check-docs" in action_ids
    assert "release.plan" in action_ids
    assert "audit.doc-lifecycle" in action_ids
    assert "audit.pr-hygiene" in action_ids


def test_cockpit_action_registry_classifies_bounded_workflow_go() -> None:
    action = action_by_id("workflow.go")
    assert action is not None
    assert action.safety == BOUNDED
    assert action.command == ("agentic-kit", "workflow", "go")


def test_cockpit_foundation_does_not_mark_git_or_release_actions_destructive() -> None:
    for action in cockpit_actions():
        if action.category in {"git", "release", "gate", "audit"}:
            assert action.safety == READ_ONLY


def test_cockpit_status_command_is_read_only(tmp_path: Path) -> None:
    agentic_dir = tmp_path / ".agentic"
    agentic_dir.mkdir()
    (agentic_dir / "workflow_state").write_text("IDLE\n", encoding="utf-8")
    (agentic_dir / "current_work.yaml").write_text("name: demo\nstate: READY\nsteps: []\n", encoding="utf-8")

    result = runner.invoke(app, ["cockpit", "status", "--root", str(tmp_path)])

    assert result.exit_code == 0, result.output
    assert "Local cockpit status" in result.output
    assert "workflow_state=IDLE" in result.output
    assert "current_work=present" in result.output
    assert "current_work_state=READY" in result.output
    assert "This command is read-only." in result.output
    assert "Cockpit action execution allows read-only actions only by default." in result.output


def test_cockpit_actions_command_lists_structured_actions() -> None:
    result = runner.invoke(app, ["cockpit", "actions"])

    assert result.exit_code == 0, result.output
    assert "Local cockpit actions" in result.output
    assert "workflow.state [workflow/read_only]" in result.output
    assert "workflow.go [workflow/bounded]" in result.output
    assert "release.plan [release/read_only]" in result.output
    assert "audit.pr-hygiene [audit/read_only]" in result.output


def test_cockpit_select_renderer_lists_numbered_actions_without_execution_contract() -> None:
    action = CockpitAction("demo.action", "Demo", "demo", ("demo", "run"), READ_ONLY, "Demo action.")

    output = render_action_selection([action])

    assert "Local cockpit action selection" in output
    assert "Safety: selection is inspect-only; no action is executed." in output
    assert " 1) demo.action [demo/read_only]" in output
    assert "label: Demo" in output
    assert "command: demo run" in output
    assert "agentic-kit cockpit run <action-id>" in output


def test_cockpit_select_cli_is_inspect_only_and_does_not_execute_actions() -> None:
    result = runner.invoke(app, ["cockpit", "select"])

    assert result.exit_code == 0, result.output
    assert "Local cockpit action selection" in result.output
    assert "git.status [git/read_only]" in result.output
    assert "workflow.go [workflow/bounded]" in result.output
    assert "allowed=true" not in result.output
    assert "executed=true" not in result.output
    assert "Cockpit action executed." not in result.output


def test_cockpit_run_allows_read_only_action_with_argument_vector(tmp_path: Path) -> None:
    calls = []

    class Completed:
        returncode = 0
        stdout = "ok\n"
        stderr = ""

    def executor(command: tuple[str, ...], root: Path):
        calls.append((command, root))
        return Completed()

    result = run_cockpit_action("git.status", tmp_path, executor=executor)

    assert result.allowed is True
    assert result.executed is True
    assert result.returncode == 0
    assert result.stdout == "ok"
    assert calls == [(("git", "status", "--short"), tmp_path.resolve())]


def test_cockpit_run_blocks_unknown_action(tmp_path: Path) -> None:
    result = run_cockpit_action("missing.action", tmp_path)

    assert result.allowed is False
    assert result.executed is False
    assert result.returncode is None
    assert "Unknown cockpit action" in result.message


def test_cockpit_run_blocks_bounded_without_explicit_allow_flag(tmp_path: Path) -> None:
    result = run_cockpit_action("workflow.go", tmp_path)

    assert result.allowed is False
    assert result.executed is False
    assert "Blocked bounded cockpit action" in result.message


def test_cockpit_run_blocks_destructive_actions(tmp_path: Path) -> None:
    actions = [CockpitAction("git.push", "Git push", "git", ("git", "push"), DESTRUCTIVE, "Push changes.")]

    result = run_cockpit_action("git.push", tmp_path, actions=actions)

    assert result.allowed is False
    assert result.executed is False
    assert "Blocked destructive cockpit action" in result.message


def test_cockpit_run_does_not_use_shell_string_assembly(tmp_path: Path) -> None:
    observed = []

    class Completed:
        returncode = 0
        stdout = ""
        stderr = ""

    def executor(command: tuple[str, ...], root: Path):
        observed.append(command)
        return Completed()

    result = run_cockpit_action("git.status", tmp_path, executor=executor)

    assert result.allowed is True
    assert isinstance(observed[0], tuple)
    assert observed[0] == ("git", "status", "--short")
    assert "git status --short" != observed[0]


def test_cockpit_run_read_only_does_not_mutate_hidden_state(tmp_path: Path) -> None:
    agentic_dir = tmp_path / ".agentic"
    agentic_dir.mkdir()
    state_file = agentic_dir / "workflow_state"
    work_file = agentic_dir / "current_work.yaml"
    state_file.write_text("IDLE\n", encoding="utf-8")
    work_file.write_text("name: demo\nstate: READY\nsteps: []\n", encoding="utf-8")
    before = {path.name: path.read_text(encoding="utf-8") for path in agentic_dir.iterdir()}

    class Completed:
        returncode = 0
        stdout = ""
        stderr = ""

    result = run_cockpit_action("git.status", tmp_path, executor=lambda command, root: Completed())
    after = {path.name: path.read_text(encoding="utf-8") for path in agentic_dir.iterdir()}

    assert result.allowed is True
    assert after == before


def test_cockpit_run_cli_executes_read_only_action() -> None:
    result = runner.invoke(app, ["cockpit", "run", "git.status"])

    assert result.exit_code == 0, result.output
    assert "action_id=git.status" in result.output
    assert "allowed=true" in result.output
    assert "executed=true" in result.output


def test_cockpit_run_cli_blocks_bounded_action_without_allow_flag() -> None:
    result = runner.invoke(app, ["cockpit", "run", "workflow.go"])

    assert result.exit_code == 2
    assert "allowed=false" in result.output
    assert "executed=false" in result.output
    assert "Blocked bounded cockpit action" in result.output


def test_cockpit_action_inventory_json_data_has_stable_schema() -> None:
    action = CockpitAction("demo.action", "Demo", "demo", ("demo", "run"), READ_ONLY, "Demo action.")
    data = action_inventory_as_json_data([action])

    assert data == {
        "schema_version": 1,
        "actions": [
            {
                "action_id": "demo.action",
                "label": "Demo",
                "category": "demo",
                "safety": READ_ONLY,
                "command": ["demo", "run"],
                "description": "Demo action.",
            }
        ],
    }


def test_cockpit_actions_json_cli_outputs_machine_readable_inventory() -> None:
    result = runner.invoke(app, ["cockpit", "actions", "--json"])

    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["schema_version"] == 1
    assert "actions" in data
    git_status = next(action for action in data["actions"] if action["action_id"] == "git.status")
    assert git_status["category"] == "git"
    assert git_status["safety"] == READ_ONLY
    assert git_status["command"] == ["git", "status", "--short"]
    workflow_go = next(action for action in data["actions"] if action["action_id"] == "workflow.go")
    assert workflow_go["safety"] == BOUNDED


def test_cockpit_actions_json_cli_does_not_execute_actions() -> None:
    result = runner.invoke(app, ["cockpit", "actions", "--json"])

    assert result.exit_code == 0, result.output
    assert "allowed=true" not in result.output
    assert "executed=true" not in result.output
