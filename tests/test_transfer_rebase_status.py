from __future__ import annotations

import json
import subprocess

import pytest
from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.transfer_rebase import rebase_on_upstream


def test_rebase_reports_real_git_conflict_and_preserves_in_progress_state(tmp_path, monkeypatch):
    remote = tmp_path / "origin.git"
    repo = tmp_path / "repo"
    subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True)
    repo.mkdir()

    def git(*args):
        return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)

    git("init", "-b", "main")
    git("config", "user.name", "Fixture")
    git("config", "user.email", "fixture@example.invalid")
    source = repo / "shared.txt"
    source.write_text("base\n")
    git("add", "shared.txt")
    git("commit", "-m", "Base")
    git("remote", "add", "origin", str(remote))
    git("push", "origin", "main")
    git("switch", "-c", "feature/conflict")
    source.write_text("feature\n")
    git("commit", "-am", "Feature")
    git("switch", "main")
    source.write_text("upstream\n")
    git("commit", "-am", "Upstream")
    git("push", "origin", "main")
    git("switch", "feature/conflict")
    monkeypatch.chdir(repo)

    result = CliRunner().invoke(
        app, ["transfer", "rebase-on-upstream", "--upstream", "origin/main", "--json"]
    )

    assert result.exit_code == 2, result.output
    payload = json.loads(result.output)
    assert payload["result_status"] == "BLOCKED"
    assert payload["conflict_present"] is True
    assert "conflict_detected" in payload["blockers"]
    assert payload["conflict_status"]["repo"]["unmerged_files"] == ["shared.txt"]
    assert (repo / ".git/rebase-merge").exists()


@pytest.mark.parametrize(
    ("status_rc", "status_output"),
    [
        (0, "not-json"),
        (0, "{}"),
        (1, '{"repo":{"conflict_present":false}}'),
        (0, '{"repo":{"conflict_present":false},"commands":{"unmerged":{"returncode":128}}}'),
    ],
)
def test_rebase_blocks_when_conflict_observation_is_unavailable(monkeypatch, status_rc, status_output):
    def run(argv, **kwargs):
        command = list(argv)
        if command == ["git", "branch", "--show-current"]:
            return subprocess.CompletedProcess(command, 0, "feature/demo\n", "")
        if "conflict-status" in command:
            return subprocess.CompletedProcess(command, status_rc, status_output, "")
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(subprocess, "run", run)
    result = CliRunner().invoke(app, ["transfer", "rebase-on-upstream", "--json"])

    assert result.exit_code == 2, result.output
    payload = json.loads(result.output)
    assert payload["conflict_present"] is None
    assert "conflict_status_unavailable" in payload["blockers"]


def test_rebase_renders_unknown_observation_without_claiming_no_conflict(monkeypatch):
    def run(argv, **kwargs):
        if list(argv) == ["git", "branch", "--show-current"]:
            return subprocess.CompletedProcess(argv, 0, "feature/demo\n", "")
        return subprocess.CompletedProcess(argv, 0, "", "")

    monkeypatch.setattr(subprocess, "run", run)
    result = CliRunner().invoke(app, ["transfer", "rebase-on-upstream"])
    assert result.exit_code == 2
    assert "CONFLICT:" in result.output and "unknown" in result.output


@pytest.mark.parametrize("branch", ["main", "feature/other"])
def test_rebase_core_preserves_branch_guards_without_fetch_or_rebase(monkeypatch, branch):
    calls = []

    def run(argv, **kwargs):
        command = list(argv)
        calls.append(command)
        output = branch + "\n" if command == ["git", "branch", "--show-current"] else '{"repo":{"conflict_present":false}}'
        return subprocess.CompletedProcess(argv, 0, output, "")

    monkeypatch.setattr(subprocess, "run", run)
    result = rebase_on_upstream(expected_branch="feature/expected")
    assert result["result_status"] == "BLOCKED"
    assert not any(command[:2] in (["git", "fetch"], ["git", "rebase"]) for command in calls)

