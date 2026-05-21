from __future__ import annotations

from agentic_project_kit import gui_dry_run


def test_gui_help_returns_success_without_running_dry_run(capsys):
    assert gui_dry_run.main(["--help"]) == 0
    output = capsys.readouterr().out
    assert "usage: ./ns gui [--dry-run] [--action ACTION_NAME]" in output
    assert "Safety: help only" in output
    assert "GUI DRY RUN" not in output
    assert "execution_result_begin" not in output
    assert "### RESULT: PASS ###" in output


def test_gui_short_help_returns_success(capsys):
    assert gui_dry_run.main(["-h"]) == 0
    output = capsys.readouterr().out
    assert "### RESULT: PASS ###" in output


def test_gui_help_like_argument_still_fails(capsys):
    assert gui_dry_run.main(["--help-like"]) == 2
    output = capsys.readouterr().out
    assert "### RESULT: FAIL ###" in output


def test_gui_action_route_still_works(capsys):
    assert gui_dry_run.main(["--action", "cockpit-readiness"]) == 0
    output = capsys.readouterr().out
    assert "execution_result_begin" in output
    assert "action=cockpit-readiness" in output
    assert "allowed=true" in output
