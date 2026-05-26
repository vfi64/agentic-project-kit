from pathlib import Path

from agentic_project_kit import release_publish_core
from agentic_project_kit.release_publish_core import CommandResult, expected_confirmation, normalize_version, publish_release


def test_normalize_version_accepts_plain_and_tag():
    assert normalize_version("0.3.37") == ("0.3.37", "v0.3.37")
    assert normalize_version("v0.3.37") == ("0.3.37", "v0.3.37")


def test_expected_confirmation_uses_tag():
    assert expected_confirmation("v0.3.37") == "publish-v0.3.37"


def test_publish_release_blocks_when_remote_tag_lookup_fails(monkeypatch, tmp_path: Path, capsys):
    calls: list[list[str]] = []

    def fake_run_command(_repo_root: Path, args: list[str]) -> CommandResult:
        calls.append(args)
        if args == ["git", "branch", "--show-current"]:
            return CommandResult(0, "main")
        if args in (["git", "status", "--short"], ["git", "status", "--porcelain"]):
            return CommandResult(0, "")
        if args == ["git", "pull", "--ff-only", "origin", "main"]:
            return CommandResult(0, "updated")
        if args == ["./ns", "release-gate", "0.4.4"]:
            return CommandResult(0, "gate passed")
        if args == ["git", "rev-parse", "v0.4.4"]:
            return CommandResult(1, "fatal: ambiguous argument")
        if args == ["git", "ls-remote", "--tags", "origin", "v0.4.4"]:
            return CommandResult(2, "network unavailable")
        if args == ["gh", "release", "view", "v0.4.4"]:
            return CommandResult(1, "release not found")
        if args[:3] == ["gh", "run", "list"]:
            return CommandResult(0, "workflow list")
        if args == ["git", "log", "--oneline", "-8"]:
            return CommandResult(0, "log")
        raise AssertionError(args)

    monkeypatch.setattr(release_publish_core, "run_command", fake_run_command)

    assert publish_release("0.4.4", "publish-v0.4.4", tmp_path, sleep_seconds=0) == 1

    output = capsys.readouterr().out
    assert "ERROR: remote tag lookup failed: network unavailable" in output
    assert ["git", "tag", "v0.4.4"] not in calls
    assert ["git", "push", "origin", "v0.4.4"] not in calls


def test_publish_release_blocks_when_github_release_lookup_is_inconclusive(monkeypatch, tmp_path: Path, capsys):
    calls: list[list[str]] = []

    def fake_run_command(_repo_root: Path, args: list[str]) -> CommandResult:
        calls.append(args)
        if args == ["git", "branch", "--show-current"]:
            return CommandResult(0, "main")
        if args in (["git", "status", "--short"], ["git", "status", "--porcelain"]):
            return CommandResult(0, "")
        if args == ["git", "pull", "--ff-only", "origin", "main"]:
            return CommandResult(0, "updated")
        if args == ["./ns", "release-gate", "0.4.4"]:
            return CommandResult(0, "gate passed")
        if args == ["git", "rev-parse", "v0.4.4"]:
            return CommandResult(1, "fatal: ambiguous argument")
        if args == ["git", "ls-remote", "--tags", "origin", "v0.4.4"]:
            return CommandResult(0, "")
        if args == ["gh", "release", "view", "v0.4.4"]:
            return CommandResult(2, "network unavailable")
        if args[:3] == ["gh", "run", "list"]:
            return CommandResult(0, "workflow list")
        if args == ["git", "log", "--oneline", "-8"]:
            return CommandResult(0, "log")
        raise AssertionError(args)

    monkeypatch.setattr(release_publish_core, "run_command", fake_run_command)

    assert publish_release("0.4.4", "publish-v0.4.4", tmp_path, sleep_seconds=0) == 1

    output = capsys.readouterr().out
    assert "ERROR: GitHub release lookup failed: network unavailable" in output
    assert ["git", "tag", "v0.4.4"] not in calls
    assert ["git", "push", "origin", "v0.4.4"] not in calls
