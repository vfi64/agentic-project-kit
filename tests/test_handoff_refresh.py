from pathlib import Path

import yaml
from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.handoff_state import is_administrative_refresh_subject, refresh_handoff_safe_state, save_handoff_state

def test_refresh_handoff_safe_state_updates_commit_without_mutating_input():
    data = {
        "updated": {"date": "old"},
        "safe_state": {"branch": "main", "commit": "old", "commit_subject": "old subject"},
    }
    refreshed = refresh_handoff_safe_state(data, "abc1234", "New subject", updated_date="2026-05-26")
    assert data["safe_state"]["commit"] == "old"
    assert refreshed["safe_state"]["commit"] == "abc1234"
    assert refreshed["safe_state"]["commit_subject"] == "New subject"
    assert refreshed["updated"]["date"] == "2026-05-26"
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

def test_refresh_preserves_substantive_commit_for_administrative_refresh_head():
    data = {
        "updated": {"reason": "old"},
        "safe_state": {
            "branch": "main",
            "commit": "sub1234",
            "commit_subject": "Add parameterized action specs MVP (#348)",
            "semantics": "last_substantive_work_state",
            "administrative_refresh_prs": [349],
        },
        "release": {"current_version": "0.3.24"},
        "repo": {"name": "agentic-project-kit", "local_path": ".", "remote": "remote"},
        "next_allowed_tasks": [{"id": "next", "title": "Next", "priority": 1}],
        "recent_failure_patterns": [{"id": "x", "prevention": "y"}],
        "rules": [],
        "first_instruction": "Continue substantive work.",
    }
    refreshed = refresh_handoff_safe_state(
        data,
        "adm9999",
        "Refresh handoff state after parameterized action specs (#349)",
        updated_date="2026-05-26",
    )
    assert refreshed["safe_state"]["commit"] == "sub1234"
    assert refreshed["safe_state"]["semantics"] == "last_substantive_work_state"
    assert refreshed["updated"]["date"] == "2026-05-26"
    assert "administrative handoff refresh" in refreshed["updated"]["reason"]


def test_save_handoff_state_preserves_required_comment_anchors(tmp_path: Path):
    target = tmp_path / "handoff_state.yaml"

    save_handoff_state({"schema_version": 1}, target)

    text = target.read_text(encoding="utf-8")
    assert "# preservation-anchor: use d for log-backed PASS and f for log-backed FAIL" in text
    assert "# preservation-anchor: nested shell/Python quote layers" in text
    assert yaml.safe_load(text)["schema_version"] == 1


def test_refresh_handoff_after_pr_subject_is_administrative() -> None:
    assert is_administrative_refresh_subject("Refresh handoff after PR980 (#981)")
