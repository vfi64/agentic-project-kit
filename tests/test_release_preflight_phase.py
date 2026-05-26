from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.release import CommandResult

runner = CliRunner()


def test_release_preflight_accepts_before_metadata_phase(monkeypatch):
    calls = []

    def fake_run_command(_project_root, args):
        calls.append(args)
        if args[:3] == ["git", "tag", "-l"]:
            return CommandResult(0, "", "")
        if args[:4] == ["git", "ls-remote", "--tags", "origin"]:
            return CommandResult(0, "", "")
        if args[:3] == ["gh", "release", "view"]:
            return CommandResult(1, "", "release not found")
        raise AssertionError(args)

    monkeypatch.setattr("agentic_project_kit.release.run_command", fake_run_command)
    result = runner.invoke(app, ["release-preflight", "--version", "0.3.32"])
    assert result.exit_code == 0
    assert "Release preflight for target v0.3.32" in result.output
    assert "[PASS] semantic version" in result.output
    assert "[PASS] local tag unused" in result.output
    assert "[PASS] remote tag unused" in result.output
    assert "[PASS] GitHub release unused" in result.output
    assert "Overall: PASS" in result.output
    assert ["git", "tag", "-l", "v0.3.32"] in calls


def test_release_preflight_fails_when_target_release_exists(monkeypatch):
    def fake_run_command(_project_root, args):
        if args[:3] == ["git", "tag", "-l"]:
            return CommandResult(0, "", "")
        if args[:4] == ["git", "ls-remote", "--tags", "origin"]:
            return CommandResult(0, "", "")
        if args[:3] == ["gh", "release", "view"]:
            return CommandResult(0, "existing release", "")
        raise AssertionError(args)

    monkeypatch.setattr("agentic_project_kit.release.run_command", fake_run_command)
    result = runner.invoke(app, ["release-preflight", "--version", "0.3.32"])
    assert result.exit_code == 1
    assert "[FAIL] GitHub release unused" in result.output
    assert "Overall: FAIL" in result.output


def test_release_preflight_does_not_require_target_version_in_files(monkeypatch):
    def fake_run_command(_project_root, args):
        if args[:3] == ["git", "tag", "-l"]:
            return CommandResult(0, "", "")
        if args[:4] == ["git", "ls-remote", "--tags", "origin"]:
            return CommandResult(0, "", "")
        if args[:3] == ["gh", "release", "view"]:
            return CommandResult(1, "", "release not found")
        raise AssertionError(args)

    monkeypatch.setattr("agentic_project_kit.release.run_command", fake_run_command)
    result = runner.invoke(app, ["release-preflight", "--version", "0.3.99"])
    assert result.exit_code == 0
    assert "missing text: version =" not in result.output


def test_release_preflight_blocks_when_remote_tag_lookup_warns(monkeypatch):
    def fake_run_command(_project_root, args):
        if args[:3] == ["git", "tag", "-l"]:
            return CommandResult(0, "", "")
        if args[:4] == ["git", "ls-remote", "--tags", "origin"]:
            return CommandResult(2, "", "network unavailable")
        if args[:3] == ["gh", "release", "view"]:
            return CommandResult(1, "", "release not found")
        raise AssertionError(args)

    monkeypatch.setattr("agentic_project_kit.release.run_command", fake_run_command)
    result = runner.invoke(app, ["release-preflight", "--version", "0.3.32"])
    assert result.exit_code == 1
    assert "[WARN] remote tag unused: network unavailable" in result.output
    assert "[BLOCK] release publish readiness" in result.output
    assert "Overall: BLOCK" in result.output
