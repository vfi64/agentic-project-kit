from pathlib import Path

from agentic_project_kit.gui_dry_run import render_result
from agentic_project_kit.gui_dry_run import run_gui_dry_run
from agentic_project_kit.gui_dry_run import main


def test_gui_dry_run_can_render_allowed_read_only_execution_result() -> None:
    output = render_result(run_gui_dry_run(Path.cwd(), action_name="cockpit-readiness"))
    assert "execution_result_begin" in output
    assert "action=cockpit-readiness" in output
    assert "safety_class=read-only" in output
    assert "allowed=true" in output
    assert "executed=false" in output
    assert "no executor" in output
    assert "real_window_opened=false" in output


def test_gui_dry_run_blocks_remote_mutation_action_result() -> None:
    output = render_result(run_gui_dry_run(Path.cwd(), action_name="agent-run"))
    assert "execution_result_begin" in output
    assert "action=agent-run" in output
    assert "safety_class=remote-mutation" in output
    assert "allowed=false" in output
    assert "executed=false" in output
    assert "limited to read-only actions" in output


def test_gui_dry_run_missing_action_is_reported_without_execution() -> None:
    output = render_result(run_gui_dry_run(Path.cwd(), action_name="missing-action"))
    assert "action=missing-action" in output
    assert "safety_class=unknown" in output
    assert "allowed=false" in output
    assert "Action not found." in output


def test_gui_main_accepts_action_argument(capsys) -> None:
    assert main(["--action", "cockpit-readiness"]) == 0
    output = capsys.readouterr().out
    assert "GUI ACTION EXECUTION RESULT" in output
    assert "action=cockpit-readiness" in output


def test_gui_main_rejects_unknown_arguments(capsys) -> None:
    assert main(["--bad"]) == 2
    output = capsys.readouterr().out
    assert "usage: ./ns gui [--dry-run] [--action ACTION_NAME]" in output
    assert "### RESULT: FAIL ###" in output
