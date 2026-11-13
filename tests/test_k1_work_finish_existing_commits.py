"""K1 (V8, V9): work finish without --path publishes the branch's existing commits."""
from __future__ import annotations

import json
import subprocess

from typer.testing import CliRunner

from agentic_project_kit.cli import app

HW = "agentic_project_kit.cli_commands.human_workflows.subprocess.run"
ARGS = ["work", "finish", "--branch", "fix/demo", "--title", "Demo", "--message", "Demo", "--json"]


def _fake(calls, *, porcelain="", ahead="1\n"):
    def run(argv, *args, **kwargs):
        command = list(argv)
        calls.append(command)
        if command[:2] == ["git", "status"]:
            return subprocess.CompletedProcess(command, 0, porcelain, "")
        if command[:2] == ["git", "rev-list"]:
            return subprocess.CompletedProcess(command, 0, ahead, "")
        if command[1:3] == ["transfer", "pr-create-complete"]:
            out = '{"result_status":"PASS","pr_number":7,"post_merge_complete_verified_by_inner_pr_complete":true}\n'
            return subprocess.CompletedProcess(command, 0, out, "")
        return subprocess.CompletedProcess(command, 0, '{"result_status": "PASS"}\n', "")
    return run


def test_dry_run_without_path_plans_publishing_existing_commits(monkeypatch):
    calls: list[list[str]] = []
    monkeypatch.setattr(HW, _fake(calls))
    result = CliRunner().invoke(app, ARGS)
    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["result_status"] == "PLANNED"
    assert "publish-existing-commits" in [step["name"] for step in payload["steps"]]


def test_execute_without_path_skips_the_work_commit_and_publishes(monkeypatch):
    calls: list[list[str]] = []
    monkeypatch.setattr(HW, _fake(calls))
    result = CliRunner().invoke(app, [*ARGS, "--execute"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    commit = next(step for step in payload["steps"] if step["name"] == "commit")
    assert commit["argv"] == [] and "K1" in commit["stdout"]
    work_commits = [c for c in calls if c[1:3] == ["transfer", "commit"]
                    and c[c.index("--message") + 1] == "Demo"]
    assert work_commits == []
    assert any(c[1:3] == ["transfer", "push-current"] for c in calls)
    assert any(c[1:3] == ["transfer", "pr-create-complete"] for c in calls)


def test_uncommitted_changes_without_path_block_with_command_field(monkeypatch):
    calls: list[list[str]] = []
    monkeypatch.setattr(HW, _fake(calls, porcelain=" M src/x.py\n"))
    result = CliRunner().invoke(app, ARGS)
    assert result.exit_code == 2
    payload = json.loads(result.stdout)
    assert payload["blockers"] == ["path-selection"]
    assert payload["check_id"] == "KIT-CHK-WORK-FINISH-PATHS"
    assert "--path" in payload["next_command"] and payload["next_command_autonomous"] is False


def test_nothing_to_publish_blocks(monkeypatch):
    calls: list[list[str]] = []
    monkeypatch.setattr(HW, _fake(calls, ahead="0\n"))
    result = CliRunner().invoke(app, ARGS)
    assert result.exit_code == 2
    assert json.loads(result.stdout)["blockers"] == ["path-selection"]
