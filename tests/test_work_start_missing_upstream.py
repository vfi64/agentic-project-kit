"""A generated project explains how to connect its local main branch."""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys


def test_work_start_reports_missing_upstream_and_passes_after_tracking(tmp_path):
    root = Path(__file__).resolve().parents[1]
    env = {**os.environ, "PYTHONPATH": str(root / "src"), "GIT_CONFIG_NOSYSTEM": "1",
           "GIT_CONFIG_GLOBAL": str(tmp_path / "fixture.gitconfig")}
    kit = [sys.executable, "-c", "from agentic_project_kit.cli import app; app()"]

    def run(cwd, *argv, expected=0):
        result = subprocess.run(argv, cwd=cwd, env=env, capture_output=True, text=True, timeout=90)
        assert result.returncode == expected, result.stdout + result.stderr
        return result.stdout

    project = tmp_path / "demo"
    bare = tmp_path / "origin.git"
    run(tmp_path, "git", "config", "--global", "user.name", "Fixture")
    run(tmp_path, "git", "config", "--global", "user.email", "fixture@example.invalid")
    run(tmp_path, *kit, "init", project.name, "--type", "generic", "--no-github", "--json")
    run(tmp_path, "git", "init", "--bare", str(bare))
    run(project, "git", "remote", "add", "origin", str(bare))
    run(project, "git", "push", "origin", "main")
    run(project, "git", "config", "--get", "branch.main.merge", expected=1)

    start = [*kit, "work", "start", "--branch", "feat/demo"]
    result = json.loads(run(project, *start, "--json", expected=2))
    assert result["blockers"] == ["sync-main"]
    assert result["next_command_kind"] == "human"
    assert result["next_command_autonomous"] is False
    assert "missing_upstream" in result["next_command_reason"]
    assert "git branch -u origin/main" in result["next_action"]
    run(project, "git", "config", "--get", "branch.main.merge", expected=1)

    dirty_file = project / "uncommitted.txt"
    dirty_file.write_text("Uncommitted user work.\n", encoding="utf-8")
    result = json.loads(run(project, *start, "--json", expected=2))
    assert "missing_upstream" in result["next_action"]
    assert "dirty_worktree" in result["next_action"]
    assert "git branch -u origin/main" in result["next_action"]
    assert dirty_file.read_text(encoding="utf-8") == "Uncommitted user work.\n"
    dirty_file.unlink()

    run(project, "git", "config", "branch.main.remote", "origin")
    run(project, "git", "config", "branch.main.merge", "refs/heads/unavailable")
    result = json.loads(run(project, *start, "--json", expected=2))
    assert "missing_upstream" not in result["next_action"]
    assert "git branch -u" not in result["next_command_reason"]

    run(project, "git", "branch", "-u", "origin/main")
    result = json.loads(run(project, *start, "--json"))
    assert result["result_status"] == "PASS"
    assert run(project, "git", "branch", "--show-current").strip() == "feat/demo"
