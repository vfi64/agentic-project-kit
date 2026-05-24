from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.documentation_registry import (
    build_artifact_policy_summary,
    build_documentation_registry_summary,
)

ROOT = Path(__file__).resolve().parents[1]


def test_artifact_policy_summary_consumes_machine_readable_rules() -> None:
    summary = build_artifact_policy_summary(ROOT)

    assert summary["policy_path"] == ".agentic/communication_artifacts.yaml"
    assert summary["present"] is True
    assert summary["schema_version"] == 1
    assert summary["rule_count"] >= 6
    assert "repo-terminal-logs" in summary["protected_rule_ids"]
    assert "terminal-latest-pointer" in summary["protected_rule_ids"]
    assert "command-run-reports" in summary["protected_rule_ids"]


def test_documentation_registry_summary_embeds_artifact_policy() -> None:
    summary = build_documentation_registry_summary(ROOT)

    artifact_policy = summary["artifact_policy"]
    assert artifact_policy["policy_path"] == ".agentic/communication_artifacts.yaml"
    assert artifact_policy["rule_count"] >= 6
    assert "terminal-latest-pointer" in artifact_policy["protected_rule_ids"]


def test_docs_registry_cli_renders_artifact_policy() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["docs-registry"])

    assert result.exit_code == 0
    assert "artifact policy:" in result.output
    assert "repo-terminal-logs" in result.output


def test_docs_registry_json_report_contains_artifact_policy(tmp_path: Path) -> None:
    report_path = tmp_path / "registry-summary.json"
    runner = CliRunner()
    result = runner.invoke(app, ["docs-registry", "--report", str(report_path)])

    assert result.exit_code == 0
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["artifact_policy"]["policy_path"] == ".agentic/communication_artifacts.yaml"
    assert payload["artifact_policy"]["rule_count"] >= 6
    assert "terminal-latest-pointer" in payload["artifact_policy"]["protected_rule_ids"]
