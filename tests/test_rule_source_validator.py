from pathlib import Path

import yaml

from agentic_project_kit.chat_bootloader import MANDATORY_BOOT_SOURCES
from agentic_project_kit.rule_source_validator import (
    canonical_rule_source_paths,
    render_rule_source_validation,
    validate_rule_sources,
)


def write_minimal_sources(root: Path) -> None:
    for source in canonical_rule_source_paths():
        path = root / source
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.suffix in {".yaml", ".yml"}:
            path.write_text("{}\n", encoding="utf-8")
        else:
            path.write_text(f"content for {source}\n", encoding="utf-8")

    handoff_state = {
        "schema_version": 1,
        "updated": "2026-05-31",
        "repo": {"name": "agentic-project-kit"},
        "safe_state": {"semantics": "current_main_head"},
        "release": {"current_version": "0.4.5"},
        "open_items": {},
        "completed_since_previous_handoff": ["test"],
        "current_capabilities": ["test"],
        "rules": [{"id": "r1", "status": "active", "text": "test rule"}],
        "recent_failure_patterns": ["test"],
        "next_allowed_tasks": ["test"],
        "blocked_until_closeout": [],
        "first_instruction": "test",
        "handoff_maintenance": {"latest_successor_prompt": "post-PR1"},
    }
    (root / ".agentic/handoff_state.yaml").write_text(yaml.safe_dump(handoff_state), encoding="utf-8")


def test_canonical_rule_source_paths_reuse_existing_source_lists() -> None:
    paths = canonical_rule_source_paths()

    for source in MANDATORY_BOOT_SOURCES:
        assert source in paths
    assert ".agentic/compiled_agent_context.yaml" in paths
    assert ".agentic/handoff_state.yaml" in paths
    assert "relevant source files and tests for the requested slice" not in paths
    assert len(paths) == len(set(paths))


def test_validate_rule_sources_passes_for_repository() -> None:
    result = validate_rule_sources(Path("."))

    assert result.is_valid
    assert not result.fail_closed
    assert result.sources_total == len(canonical_rule_source_paths())
    assert result.missing_required_paths == ()
    assert result.yaml_parse_error_paths == ()
    assert result.blocking_reasons == ()


def test_validate_rule_sources_fails_closed_for_missing_required_source(tmp_path: Path) -> None:
    write_minimal_sources(tmp_path)
    (tmp_path / ".agentic/compiled_agent_context.yaml").unlink()

    result = validate_rule_sources(tmp_path)

    assert not result.is_valid
    assert result.fail_closed
    assert ".agentic/compiled_agent_context.yaml" in result.missing_required_paths
    assert "missing required rule source: .agentic/compiled_agent_context.yaml" in result.blocking_reasons


def test_validate_rule_sources_fails_closed_for_yaml_parse_error(tmp_path: Path) -> None:
    write_minimal_sources(tmp_path)
    (tmp_path / ".agentic/rule_migrations.yaml").write_text(":\n", encoding="utf-8")

    result = validate_rule_sources(tmp_path)

    assert not result.is_valid
    assert result.fail_closed
    assert ".agentic/rule_migrations.yaml" in result.yaml_parse_error_paths
    assert any(reason.startswith("yaml parse error in rule source: .agentic/rule_migrations.yaml") for reason in result.blocking_reasons)


def test_validate_rule_sources_fails_closed_for_invalid_handoff_state(tmp_path: Path) -> None:
    write_minimal_sources(tmp_path)
    (tmp_path / ".agentic/handoff_state.yaml").write_text("{}\n", encoding="utf-8")

    result = validate_rule_sources(tmp_path)

    assert not result.is_valid
    assert result.fail_closed
    assert "missing required field: schema_version" in result.handoff_state_errors
    assert "handoff_state invalid: missing required field: schema_version" in result.blocking_reasons


def test_render_rule_source_validation_is_machine_readable() -> None:
    rendered = render_rule_source_validation(validate_rule_sources(Path(".")))

    assert "RULE_SOURCE_VALIDATION" in rendered
    assert "sources_total=" in rendered
    assert "is_valid=True" in rendered
    assert "fail_closed=False" in rendered
