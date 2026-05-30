from __future__ import annotations

import subprocess

from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.transfer_repo_actions import branch_create, branch_delete, branch_switch, commit_paths, fetch_origin, pull_current, repo_diff, repo_log, repo_status


def _init_repo(path):
    subprocess.run(["git", "init"], cwd=path, check=True, stdout=subprocess.PIPE)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=path, check=True)
    (path / "README.md").write_text("base\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=path, check=True)
    subprocess.run(["git", "commit", "-m", "Initial"], cwd=path, check=True, stdout=subprocess.PIPE)
    subprocess.run(["git", "branch", "-M", "main"], cwd=path, check=True, stdout=subprocess.PIPE)


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


def test_repo_status_log_and_diff(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    (tmp_path / "changed.txt").write_text("change\n", encoding="utf-8")

    status = repo_status()
    log = repo_log(limit=1)
    diff = repo_diff(name_only=True)

    assert status.result_status == "PASS"
    assert "changed.txt" in status.stdout
    assert log.result_status == "PASS"
    assert "Initial" in log.stdout
    assert diff.result_status == "PASS"


def test_fetch_and_pull_current_without_origin_fail_deterministically(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    fetch = fetch_origin("main")
    pull = pull_current()

    assert fetch.result_status == "FAIL"
    assert "origin" in fetch.stderr
    assert pull.result_status == "FAIL"
    assert "origin" in pull.stderr


def test_branch_delete(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    created = branch_create("feature/delete-me", start_point="main")
    switched = branch_switch("main")
    deleted = branch_delete("feature/delete-me")

    assert created.result_status == "PASS"
    assert switched.result_status == "PASS"
    assert deleted.result_status == "PASS"


def test_transfer_repo_status_cli(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(app, ["transfer", "repo-status"])

    assert result.exit_code == 0
    assert '"action": "repo-status"' in result.stdout


def test_transfer_repo_log_cli(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(app, ["transfer", "repo-log", "--limit", "1"])

    assert result.exit_code == 0
    assert '"action": "repo-log"' in result.stdout


def test_transfer_branch_delete_cli(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    branch_create("feature/cli-delete", start_point="main")
    branch_switch("main")

    result = CliRunner().invoke(app, ["transfer", "branch-delete", "feature/cli-delete"])

    assert result.exit_code == 0
    assert '"action": "branch-delete"' in result.stdout
