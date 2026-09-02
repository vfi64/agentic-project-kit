from __future__ import annotations

import json
from pathlib import Path
import subprocess

from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.rule_ack import (
    RuleAcknowledgement,
    acknowledgement_from_json_data,
    build_rule_acknowledgement,
    ensure_rule_ack_local_exclude,
    validate_rule_acknowledgement,
)
from agentic_project_kit.rule_snapshot import build_derived_rule_snapshot
from tests.test_rule_source_validator import write_minimal_sources


def _valid_ack(snapshot, repo_head: str = "abc123") -> RuleAcknowledgement:
    return RuleAcknowledgement(
        schema_version=1,
        snapshot_id=snapshot.snapshot_id,
        repo_head=repo_head,
        sources_total=snapshot.sources_total,
        missing_sources_total=len(snapshot.validation.missing_required_paths),
        declared_next_allowed_action="run_next_command",
    )


def test_rule_acknowledgement_confirms_matching_snapshot(tmp_path: Path) -> None:
    write_minimal_sources(tmp_path)
    snapshot = build_derived_rule_snapshot(tmp_path)

    decision = validate_rule_acknowledgement(
        snapshot,
        _valid_ack(snapshot),
        repo_head="abc123",
        required_next_allowed_action="run_next_command",
    )

    assert decision.is_confirmed is True
    assert decision.fail_closed is False
    assert decision.blocking_reasons == ()


def test_rule_acknowledgement_fails_closed_when_missing(tmp_path: Path) -> None:
    write_minimal_sources(tmp_path)
    snapshot = build_derived_rule_snapshot(tmp_path)

    decision = validate_rule_acknowledgement(
        snapshot,
        None,
        repo_head="abc123",
        required_next_allowed_action="run_next_command",
    )

    assert decision.is_confirmed is False
    assert decision.fail_closed is True
    assert "missing_rule_acknowledgement" in decision.blocking_reasons


def test_rule_acknowledgement_rejects_stale_snapshot_id(tmp_path: Path) -> None:
    write_minimal_sources(tmp_path)
    snapshot = build_derived_rule_snapshot(tmp_path)
    ack = RuleAcknowledgement(
        schema_version=1,
        snapshot_id="0" * 64,
        repo_head="abc123",
        sources_total=snapshot.sources_total,
        missing_sources_total=0,
        declared_next_allowed_action="run_next_command",
    )

    decision = validate_rule_acknowledgement(
        snapshot,
        ack,
        repo_head="abc123",
        required_next_allowed_action="run_next_command",
    )

    assert decision.is_confirmed is False
    assert "snapshot_id_mismatch" in decision.blocking_reasons


def test_rule_acknowledgement_warns_on_repo_head_mismatch_without_blocking(tmp_path: Path) -> None:
    write_minimal_sources(tmp_path)
    snapshot = build_derived_rule_snapshot(tmp_path)

    decision = validate_rule_acknowledgement(
        snapshot,
        _valid_ack(snapshot, repo_head="old"),
        repo_head="new",
        required_next_allowed_action="run_next_command",
    )

    assert decision.is_confirmed is True
    assert decision.fail_closed is False
    assert decision.blocking_reasons == ()
    assert decision.warnings == ("repo_head_mismatch",)


def test_rule_acknowledgement_rejects_next_action_mismatch(tmp_path: Path) -> None:
    write_minimal_sources(tmp_path)
    snapshot = build_derived_rule_snapshot(tmp_path)
    ack = RuleAcknowledgement(
        schema_version=1,
        snapshot_id=snapshot.snapshot_id,
        repo_head="abc123",
        sources_total=snapshot.sources_total,
        missing_sources_total=0,
        declared_next_allowed_action="different_action",
    )

    decision = validate_rule_acknowledgement(
        snapshot,
        ack,
        repo_head="abc123",
        required_next_allowed_action="run_next_command",
    )

    assert decision.is_confirmed is False
    assert "declared_next_allowed_action_mismatch" in decision.blocking_reasons


def test_rule_acknowledgement_fails_closed_when_snapshot_fails_closed(tmp_path: Path) -> None:
    write_minimal_sources(tmp_path)
    (tmp_path / ".agentic/compiled_agent_context.yaml").unlink()
    snapshot = build_derived_rule_snapshot(tmp_path)

    decision = validate_rule_acknowledgement(
        snapshot,
        _valid_ack(snapshot),
        repo_head="abc123",
        required_next_allowed_action="run_next_command",
    )

    assert decision.is_confirmed is False
    assert "rule_snapshot_fail_closed" in decision.blocking_reasons


def test_rule_acknowledgement_roundtrip_from_json_data(tmp_path: Path) -> None:
    write_minimal_sources(tmp_path)
    snapshot = build_derived_rule_snapshot(tmp_path)
    ack = acknowledgement_from_json_data(_valid_ack(snapshot).as_json_data())

    assert ack == _valid_ack(snapshot)


def test_build_rule_acknowledgement_uses_snapshot_identity(tmp_path: Path) -> None:
    write_minimal_sources(tmp_path)
    snapshot = build_derived_rule_snapshot(tmp_path)

    ack = build_rule_acknowledgement(
        snapshot,
        repo_head="abc123",
        declared_next_allowed_action="run_next_command",
    )

    assert ack.schema_version == 1
    assert ack.snapshot_id == snapshot.snapshot_id
    assert ack.repo_head == "abc123"
    assert ack.sources_total == snapshot.sources_total
    assert ack.missing_sources_total == len(snapshot.validation.missing_required_paths)
    assert ack.declared_next_allowed_action == "run_next_command"


def test_ensure_rule_ack_local_exclude_is_idempotent(tmp_path: Path) -> None:
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, stdout=subprocess.PIPE)

    first = ensure_rule_ack_local_exclude(tmp_path)
    second = ensure_rule_ack_local_exclude(tmp_path)

    exclude_path = subprocess.check_output(
        ["git", "rev-parse", "--git-path", "info/exclude"],
        cwd=tmp_path,
        text=True,
    ).strip()
    assert first.updated is True
    assert first.patterns == (".agentic/rule_ack/",)
    assert second.updated is False
    assert (tmp_path / exclude_path).read_text(encoding="utf-8").count(".agentic/rule_ack/") == 1


def test_rules_acknowledge_keeps_rule_ack_runtime_state_locally_ignored(tmp_path: Path) -> None:
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, stdout=subprocess.PIPE)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=tmp_path, check=True)
    write_minimal_sources(tmp_path)
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-m", "Add rule sources"], cwd=tmp_path, check=True, stdout=subprocess.PIPE)

    result = CliRunner().invoke(app, ["rules", "acknowledge", "--root", str(tmp_path), "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["local_exclude"]["updated"] is True
    assert payload["local_exclude"]["patterns"] == [".agentic/rule_ack/"]
    status = subprocess.check_output(
        ["git", "status", "--short", "--untracked-files=all", "--", ".agentic/rule_ack/current.json"],
        cwd=tmp_path,
        text=True,
    )
    assert status == ""
