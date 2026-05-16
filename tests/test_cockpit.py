from pathlib import Path

from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.cockpit import BOUNDED, READ_ONLY, action_by_id, cockpit_actions


runner = CliRunner()


def test_cockpit_action_registry_contains_core_read_only_actions() -> None:
    action_ids = {action.action_id for action in cockpit_actions()}
    assert "git.status" in action_ids
    assert "workflow.state" in action_ids
    assert "gate.doctor" in action_ids
    assert "gate.check-docs" in action_ids
    assert "release.plan" in action_ids
    assert "audit.doc-lifecycle" in action_ids


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
    assert "does not execute git, release, or workflow actions yet" in result.output


def test_cockpit_actions_command_lists_structured_actions() -> None:
    result = runner.invoke(app, ["cockpit", "actions"])

    assert result.exit_code == 0, result.output
    assert "Local cockpit actions" in result.output
    assert "workflow.state [workflow/read_only]" in result.output
    assert "workflow.go [workflow/bounded]" in result.output
    assert "release.plan [release/read_only]" in result.output
