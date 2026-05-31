from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from agentic_project_kit.cli import app
from tests.test_rule_source_validator import write_minimal_sources


def test_rules_snapshot_cli_text_passes_for_repository() -> None:
    result = CliRunner().invoke(app, ["rules", "snapshot"])

    assert result.exit_code == 0, result.output
    assert "RULE_SNAPSHOT" in result.output
    assert "schema_version=1" in result.output
    assert "is_valid=True" in result.output
    assert "fail_closed=False" in result.output
    assert "snapshot_id=" in result.output
    assert "source_digests_total=" in result.output


def test_rules_snapshot_cli_json_passes_for_repository() -> None:
    result = CliRunner().invoke(app, ["rules", "snapshot", "--json"])

    assert result.exit_code == 0, result.output
    data = json.loads(result.output)

    assert data["schema_version"] == 1
    assert isinstance(data["snapshot_id"], str)
    assert len(data["snapshot_id"]) == 64
    assert data["is_valid"] is True
    assert data["fail_closed"] is False
    assert isinstance(data["source_digests"], list)
    assert data["sources_total"] == data["validation"]["sources_total"]


def test_rules_snapshot_cli_fails_closed_for_missing_source(tmp_path: Path) -> None:
    write_minimal_sources(tmp_path)
    (tmp_path / ".agentic/compiled_agent_context.yaml").unlink()

    result = CliRunner().invoke(app, ["rules", "snapshot", "--root", str(tmp_path)])

    assert result.exit_code == 1
    assert "RULE_SNAPSHOT" in result.output
    assert "is_valid=False" in result.output
    assert "fail_closed=True" in result.output
    assert (
        "blocking_reason=missing required rule source: .agentic/compiled_agent_context.yaml"
        in result.output
    )


def test_rules_snapshot_cli_json_fails_closed_for_missing_source(tmp_path: Path) -> None:
    write_minimal_sources(tmp_path)
    (tmp_path / ".agentic/compiled_agent_context.yaml").unlink()

    result = CliRunner().invoke(app, ["rules", "snapshot", "--root", str(tmp_path), "--json"])

    assert result.exit_code == 1
    data = json.loads(result.output)

    assert data["is_valid"] is False
    assert data["fail_closed"] is True
    assert ".agentic/compiled_agent_context.yaml" in data["validation"]["missing_required_paths"]
