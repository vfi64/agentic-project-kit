from __future__ import annotations

from pathlib import Path

from agentic_project_kit.rule_snapshot import build_derived_rule_snapshot
from tests.test_rule_source_validator import write_minimal_sources


def test_derived_rule_snapshot_is_valid_for_repository() -> None:
    snapshot = build_derived_rule_snapshot()

    data = snapshot.as_json_data()

    assert data["schema_version"] == 1
    assert isinstance(data["snapshot_id"], str)
    assert len(data["snapshot_id"]) == 64
    assert data["is_valid"] is True
    assert data["fail_closed"] is False
    assert data["sources_total"] == snapshot.validation.sources_total
    assert len(data["source_digests"]) == snapshot.validation.sources_total


def test_derived_rule_snapshot_is_deterministic_for_unchanged_sources(tmp_path: Path) -> None:
    write_minimal_sources(tmp_path)

    first = build_derived_rule_snapshot(tmp_path)
    second = build_derived_rule_snapshot(tmp_path)

    assert first.snapshot_id == second.snapshot_id
    assert first.as_json_data() == second.as_json_data()


def test_derived_rule_snapshot_changes_when_source_content_changes(tmp_path: Path) -> None:
    write_minimal_sources(tmp_path)

    first = build_derived_rule_snapshot(tmp_path)
    target = tmp_path / "docs/STATUS.md"
    target.write_text(target.read_text(encoding="utf-8") + "\nchanged\n", encoding="utf-8")
    second = build_derived_rule_snapshot(tmp_path)

    assert first.snapshot_id != second.snapshot_id


def test_derived_rule_snapshot_fails_closed_when_required_source_missing(tmp_path: Path) -> None:
    write_minimal_sources(tmp_path)
    (tmp_path / ".agentic/compiled_agent_context.yaml").unlink()

    snapshot = build_derived_rule_snapshot(tmp_path)
    data = snapshot.as_json_data()

    assert data["is_valid"] is False
    assert data["fail_closed"] is True
    assert len(data["snapshot_id"]) == 64
    assert ".agentic/compiled_agent_context.yaml" in data["validation"]["missing_required_paths"]
    assert len(data["source_digests"]) == snapshot.validation.sources_total - 1
