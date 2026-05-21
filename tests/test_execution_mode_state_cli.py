from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.execution_mode_state import ModeCheckResult

runner = CliRunner()


def test_state_mode_check_cli_passes(monkeypatch):
    def fake_eval(repo_root, target, expected_branch=None, require_clean=True):
        return ModeCheckResult(True, "REMOTE_READY", target, "main", False, True, {"git": "ok", "gh": "ok"}, ())

    monkeypatch.setattr("agentic_project_kit.cli_commands.state.evaluate_mode_switch", fake_eval)
    result = runner.invoke(app, ["state", "mode-check", "remote", "--expected-branch", "main"])
    assert result.exit_code == 0
    assert "state=REMOTE_READY" in result.output


def test_state_mode_check_cli_fails(monkeypatch):
    def fake_eval(repo_root, target, expected_branch=None, require_clean=True):
        return ModeCheckResult(False, "DIRTY_LOCAL_BLOCKED", target, "feature/x", True, True, {"git": "ok", "gh": "ok"}, ("dirty_worktree",))

    monkeypatch.setattr("agentic_project_kit.cli_commands.state.evaluate_mode_switch", fake_eval)
    result = runner.invoke(app, ["state", "mode-check", "local", "--expected-branch", "feature/x"])
    assert result.exit_code == 1
    assert "state=DIRTY_LOCAL_BLOCKED" in result.output
    assert "dirty_worktree" in result.output


def test_state_mode_write_cli_prints_state_file(monkeypatch, tmp_path):
    def fake_eval(repo_root, target, expected_branch=None, require_clean=True):
        return ModeCheckResult(True, "LOCAL_READY", target, "feature/x", False, True, {"git": "ok", "gh": "ok", "ruff": "ok"}, ())

    def fake_write(repo_root, result, reason):
        return tmp_path / ".agentic" / "execution_mode_state.yaml"

    monkeypatch.setattr("agentic_project_kit.cli_commands.state.evaluate_mode_switch", fake_eval)
    monkeypatch.setattr("agentic_project_kit.cli_commands.state.write_mode_state", fake_write)
    result = runner.invoke(app, ["state", "mode-write", "local", "--expected-branch", "feature/x", "--reason", "test"])
    assert result.exit_code == 0
    assert "state_file=" in result.output
