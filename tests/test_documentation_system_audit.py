from pathlib import Path

from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.documentation_system_audit import (
    MANDATORY_ORDER,
    build_documentation_system_audit,
    render_documentation_system_audit,
)

ROOT = Path(__file__).resolve().parents[1]


def test_documentation_system_audit_has_required_dimensions() -> None:
    report = build_documentation_system_audit(ROOT)
    names = [dimension.name for dimension in report.dimensions]
    assert names == [
        "Aktualität",
        "Vollständigkeit",
        "Korrektheit",
        "Redundanzfreiheit",
        "Stringenz der Dokumentenordnung",
        "Konsistenz",
    ]


def test_documentation_system_audit_renderer_exposes_boundaries() -> None:
    report = build_documentation_system_audit(ROOT)
    rendered = render_documentation_system_audit(report)
    assert "Documentation system audit" in rendered
    assert "Redundanzfreiheit" in rendered
    assert "review-only boundary" in rendered
    assert "Overall:" in rendered


def test_documentation_system_audit_mandatory_order_is_complete() -> None:
    assert MANDATORY_ORDER == (
        ".agentic/compiled_agent_context.yaml",
        "docs/governance/FINAL_SUMMARY_CONTRACT.md",
        "docs/governance/CHAT_COMMUNICATION_CONTRACT.md",
        "docs/governance/PORTABLE_CHAT_EXECUTION_CONTRACT.md",
        "docs/governance/CHAT_BOOTSTRAP_AND_DRIFT_CONTRACT.md",
        "docs/TEST_GATES.md",
        "docs/STATUS.md",
        "docs/handoff/CURRENT_HANDOFF.md",
    )


def test_docs_audit_cli_is_registered() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["docs-audit"])
    assert "Documentation system audit" in result.output
