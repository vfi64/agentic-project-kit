from __future__ import annotations

from agentic_project_kit import terminal_logging


def test_remote_mutation_preflight_passes_on_clean_worktree(monkeypatch):
    monkeypatch.setattr(terminal_logging, "git_dirty_paths", lambda: [])
    outcome, message = terminal_logging.remote_mutation_preflight()
    assert outcome == "PASS_CLEAN_FOR_REMOTE_MUTATION"
    assert "clean" in message.lower()


def test_remote_mutation_preflight_fails_on_any_dirty_file(monkeypatch):
    monkeypatch.setattr(terminal_logging, "git_dirty_paths", lambda: ["docs/reports/terminal/current.log"])
    outcome, message = terminal_logging.remote_mutation_preflight()
    assert outcome == "FAIL_DIRTY_WORKTREE_BEFORE_REMOTE_MUTATION"
    assert "docs/reports/terminal/current.log" in message


def test_terminal_remote_preflight_cli_returns_failure_for_dirty_worktree(monkeypatch, capsys):
    monkeypatch.setattr(terminal_logging, "git_dirty_paths", lambda: ["README.md"])
    code = terminal_logging.main(["terminal-remote-preflight"])
    out = capsys.readouterr().out
    assert code == 1
    assert "FAIL_DIRTY_WORKTREE_BEFORE_REMOTE_MUTATION" in out
    assert "README.md" in out
