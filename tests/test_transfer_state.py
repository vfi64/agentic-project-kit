from __future__ import annotations

import json
import subprocess
from pathlib import Path

from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.rule_ack import RuleAcknowledgement
from agentic_project_kit.rule_snapshot import build_derived_rule_snapshot
from agentic_project_kit.transfer_state import PRIMARY_BLOCKED, PRIMARY_WAIT, build_transfer_state
from tests.test_rule_source_validator import write_minimal_sources


def _init_repo(root: Path) -> None:
    subprocess.run(["git", "init"], cwd=root, check=True, stdout=subprocess.PIPE)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=root, check=True)
    subprocess.run(
        ["git", "remote", "add", "origin", "git@github.com:vfi64/agentic-project-kit.git"],
        cwd=root,
        check=True,
    )


def _write_and_commit_minimal_sources(root: Path) -> None:
    write_minimal_sources(root)
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    subprocess.run(
        ["git", "commit", "-m", "Add minimal rule sources"],
        cwd=root,
        check=True,
        stdout=subprocess.PIPE,
    )


def _write_rule_ack(
    root: Path, *, repo_head: str | None = None, next_action: str = "run_next_command"
) -> None:
    snapshot = build_derived_rule_snapshot(root)
    head = repo_head
    if head is None:
        head = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=root,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
        ).stdout.strip()
    ack = RuleAcknowledgement(
        schema_version=1,
        snapshot_id=snapshot.snapshot_id,
        repo_head=head,
        sources_total=snapshot.sources_total,
        missing_sources_total=len(snapshot.validation.missing_required_paths),
        declared_next_allowed_action=next_action,
    )
    path = root / ".agentic/rule_ack/current.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(ack.as_json_data(), indent=2, sort_keys=True), encoding="utf-8")


def test_transfer_state_waits_without_pending_order(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    _write_and_commit_minimal_sources(tmp_path)
    monkeypatch.chdir(tmp_path)

    snapshot = build_transfer_state(tmp_path)

    assert snapshot.schema_version == 1
    assert snapshot.repo == "vfi64/agentic-project-kit"
    assert snapshot.primary_state == PRIMARY_WAIT
    assert snapshot.capabilities["diagnose"] is True
    assert snapshot.capabilities["run_next_command"] is False
    assert snapshot.capabilities["rules_confirmed"] is False
    assert "missing_rule_acknowledgement" in snapshot.reasons


def test_transfer_state_blocks_dirty_worktree(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    _write_and_commit_minimal_sources(tmp_path)
    (tmp_path / "dirty.txt").write_text("dirty\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    snapshot = build_transfer_state(tmp_path)

    assert snapshot.primary_state == PRIMARY_BLOCKED
    assert "dirty_worktree" in snapshot.reasons
    assert snapshot.capabilities["run_next_command"] is False


def test_transfer_state_ready_with_pending_order(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    _write_and_commit_minimal_sources(tmp_path)
    inbox = tmp_path / ".agentic/transfer/inbox/current.yaml"
    inbox.parent.mkdir(parents=True)
    inbox.write_text("id: example\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "commit", "-m", "Add pending transfer order"],
        cwd=tmp_path,
        check=True,
        stdout=subprocess.PIPE,
    )
    _write_rule_ack(tmp_path)
    monkeypatch.chdir(tmp_path)

    snapshot = build_transfer_state(tmp_path)

    assert snapshot.primary_state == "READY"
    assert snapshot.capabilities["run_next_command"] is True
    assert snapshot.capabilities["rules_confirmed"] is True
    assert snapshot.rule_acknowledgement["decision"]["is_confirmed"] is True


def test_transfer_state_cli_emits_json(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    _write_and_commit_minimal_sources(tmp_path)
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(app, ["transfer", "state"])

    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["schema_version"] == 1
    assert data["primary_state"] == "WAIT"
    assert "capabilities" in data
    assert data["capabilities"]["rules_confirmed"] is False
    assert data["rule_acknowledgement"]["present"] is False


def test_transfer_state_blocks_when_rule_snapshot_fails_closed(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    _write_and_commit_minimal_sources(tmp_path)
    (tmp_path / ".agentic/compiled_agent_context.yaml").unlink()
    monkeypatch.chdir(tmp_path)

    snapshot = build_transfer_state(tmp_path)

    assert snapshot.primary_state == PRIMARY_BLOCKED
    assert "rule_snapshot_fail_closed" in snapshot.reasons
    assert snapshot.capabilities["rules_confirmed"] is False
    assert snapshot.capabilities["run_next_command"] is False
    assert snapshot.rule_snapshot["fail_closed"] is True
    assert (
        ".agentic/compiled_agent_context.yaml"
        in snapshot.rule_snapshot["validation"]["missing_required_paths"]
    )


def test_transfer_state_rejects_stale_rule_acknowledgement(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    _write_and_commit_minimal_sources(tmp_path)
    _write_rule_ack(tmp_path, repo_head="stale")
    monkeypatch.chdir(tmp_path)

    snapshot = build_transfer_state(tmp_path)

    assert snapshot.primary_state == PRIMARY_WAIT
    assert snapshot.capabilities["rules_confirmed"] is False
    assert "repo_head_mismatch" in snapshot.reasons
    assert snapshot.rule_acknowledgement["present"] is True
    assert snapshot.rule_acknowledgement["decision"]["is_confirmed"] is False


def test_transfer_state_confirms_matching_rule_acknowledgement_without_order(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    _write_and_commit_minimal_sources(tmp_path)
    _write_rule_ack(tmp_path)
    monkeypatch.chdir(tmp_path)

    snapshot = build_transfer_state(tmp_path)

    assert snapshot.primary_state == PRIMARY_WAIT
    assert snapshot.capabilities["rules_confirmed"] is True
    assert snapshot.capabilities["run_next_command"] is False
    assert snapshot.rule_acknowledgement["decision"]["is_confirmed"] is True
