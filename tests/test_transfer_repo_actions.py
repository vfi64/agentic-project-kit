from __future__ import annotations

import subprocess

from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.transfer_repo_actions import branch_create, branch_switch, commit_paths


def _init_repo(path):
    subprocess.run(["git", "init"], cwd=path, check=True, stdout=subprocess.PIPE)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=path, check=True)
    (path / "README.md").write_text("base\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=path, check=True)
    subprocess.run(["git", "commit", "-m", "Initial"], cwd=path, check=True, stdout=subprocess.PIPE)


def test_branch_create_and_switch(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    created = branch_create("feature/example", start_point="main")
    assert created.result_status == "PASS"

    switched = branch_switch("main")
    assert switched.result_status == "PASS"


def test_commit_paths(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    (tmp_path / "file.txt").write_text("content\n", encoding="utf-8")

    result = commit_paths("Add file", ["file.txt"])

    assert result.result_status == "PASS"
    assert result.returncode == 0


def test_transfer_branch_create_cli(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(app, ["transfer", "branch-create", "feature/cli"])

    assert result.exit_code == 0
    assert '"action": "branch-create"' in result.stdout
    assert '"result_status": "PASS"' in result.stdout


def test_transfer_commit_cli_requires_path(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(app, ["transfer", "commit", "--message", "No paths"])

    assert result.exit_code != 0
    assert "No paths supplied" in result.stdout
