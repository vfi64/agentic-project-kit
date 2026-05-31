from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from agentic_project_kit.cli import app
from tests.test_rule_source_validator import write_minimal_sources


def test_rules_validate_sources_cli_passes_for_repository() -> None:
    result = CliRunner().invoke(app, ["rules", "validate-sources"])

    assert result.exit_code == 0, result.output
    assert "RULE_SOURCE_VALIDATION" in result.output
    assert "is_valid=True" in result.output
    assert "fail_closed=False" in result.output


def test_rules_validate_sources_cli_json_passes_for_repository() -> None:
    result = CliRunner().invoke(app, ["rules", "validate-sources", "--json"])

    assert result.exit_code == 0, result.output
    assert '"is_valid": true' in result.output
    assert '"fail_closed": false' in result.output
    assert '"blocking_reasons": []' in result.output


def test_rules_validate_sources_cli_fails_closed_for_missing_source(tmp_path: Path) -> None:
    write_minimal_sources(tmp_path)
    (tmp_path / ".agentic/compiled_agent_context.yaml").unlink()

    result = CliRunner().invoke(app, ["rules", "validate-sources", "--root", str(tmp_path)])

    assert result.exit_code == 1
    assert "RULE_SOURCE_VALIDATION" in result.output
    assert "is_valid=False" in result.output
    assert "fail_closed=True" in result.output
    assert "missing_required_path=.agentic/compiled_agent_context.yaml" in result.output
