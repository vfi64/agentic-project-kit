from pathlib import Path

import yaml
from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.handoff_state import refresh_handoff_safe_state

def test_refresh_handoff_safe_state_updates_commit_without_mutating_input():
    data = {
        "updated": {"date": "old"},
        "safe_state": {"branch": "main", "commit": "old", "commit_subject": "old subject"},
    }
    refreshed = refresh_handoff_safe_state(data, "abc1234", "New subject")
    assert data["safe_state"]["commit"] == "old"
    assert refreshed["safe_state"]["commit"] == "abc1234"
    assert refreshed["safe_state"]["commit_subject"] == "New subject"
    assert refreshed["updated"]["source"] == "agentic-kit handoff refresh"

def test_handoff_refresh_dry_run_does_not_mutate_file(tmp_path, monkeypatch):
    source = Path(".agentic/handoff_state.yaml")
    target = tmp_path / "handoff_state.yaml"
    target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    before = target.read_text(encoding="utf-8")
    monkeypatch.setattr("agentic_project_kit.cli_commands.handoff.current_git_safe_state", lambda: {"commit": "dryrun1", "commit_subject": "Dry run subject"})
    result = CliRunner().invoke(app, ["handoff", "refresh", str(target)])
    assert result.exit_code == 0
    assert "Dry run only" in result.output
    assert target.read_text(encoding="utf-8") == before

def test_handoff_refresh_write_updates_file(tmp_path, monkeypatch):
    source = Path(".agentic/handoff_state.yaml")
    target = tmp_path / "handoff_state.yaml"
    target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr("agentic_project_kit.cli_commands.handoff.current_git_safe_state", lambda: {"commit": "write01", "commit_subject": "Write subject"})
    result = CliRunner().invoke(app, ["handoff", "refresh", str(target), "--write"])
    assert result.exit_code == 0
    assert "Updated" in result.output
    data = yaml.safe_load(target.read_text(encoding="utf-8"))
    assert data["safe_state"]["commit"] == "write01"
    assert data["safe_state"]["commit_subject"] == "Write subject"
