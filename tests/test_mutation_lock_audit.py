from __future__ import annotations

import json

from typer.testing import CliRunner

from agentic_project_kit.cli import app


def test_mutation_lock_audit_command_exists_and_reports_known_gaps() -> None:
    result = CliRunner().invoke(app, ["audit-mutation-lock-coverage", "--json"])

    assert result.exit_code == 1
    payload = json.loads(result.output)

    assert payload["kind"] == "mutation_lock_coverage_audit"
    assert payload["result_status"] == "BLOCK"
    assert "findings" in payload
    assert any(finding["category"] in {"A", "B", "C"} for finding in payload["findings"])
    assert any("branch_create" in finding["symbol"] for finding in payload["findings"])


def test_mutation_lock_audit_has_text_summary() -> None:
    result = CliRunner().invoke(app, ["audit-mutation-lock-coverage"])

    assert result.exit_code == 1
    assert "MUTATION_LOCK_COVERAGE_AUDIT" in result.output
    assert "RESULT: BLOCK" in result.output
    assert "branch_create" in result.output
