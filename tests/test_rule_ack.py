from __future__ import annotations

from pathlib import Path

from agentic_project_kit.rule_ack import (
    RuleAcknowledgement,
    acknowledgement_from_json_data,
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


def test_rule_acknowledgement_rejects_repo_head_mismatch(tmp_path: Path) -> None:
    write_minimal_sources(tmp_path)
    snapshot = build_derived_rule_snapshot(tmp_path)

    decision = validate_rule_acknowledgement(
        snapshot,
        _valid_ack(snapshot, repo_head="old"),
        repo_head="new",
        required_next_allowed_action="run_next_command",
    )

    assert decision.is_confirmed is False
    assert "repo_head_mismatch" in decision.blocking_reasons


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
