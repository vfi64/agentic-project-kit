import re
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
        "Dokumentationsregistry",
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


def test_documentation_system_audit_checks_status_handoff_closeout_sync() -> None:
    report = build_documentation_system_audit(ROOT)
    rendered = render_documentation_system_audit(report)
    assert "CURRENT_HANDOFF.md missing current closeout marker" not in rendered
    assert "STATUS.md missing current closeout marker" not in rendered
    assert ".agentic/compiled_agent_context.yaml" in Path("docs/handoff/CURRENT_HANDOFF.md").read_text(encoding="utf-8")
    assert "FINAL_SUMMARY_CONTRACT.md" in Path("docs/handoff/CURRENT_HANDOFF.md").read_text(encoding="utf-8")


def test_documentation_system_audit_pr_closeout_regex_matches_real_pr_numbers() -> None:
    source = Path("src/agentic_project_kit/documentation_system_audit.py").read_text(encoding="utf-8")
    assert 'r"PR #\\d+ merged"' in source
    assert 'r"PR #\\\\d+ merged"' not in source
    assert re.search(r"PR #\d+ merged", "PR #649 merged") is not None


def test_documentation_system_audit_enforces_status_headroom() -> None:
    source = Path("src/agentic_project_kit/documentation_system_audit.py").read_text(encoding="utf-8")
    assert "STATUS_HEADROOM_WORD_LIMIT = 4140" in source
    status_words = len(Path("docs/STATUS.md").read_text(encoding="utf-8").split())
    assert status_words <= 4140
    report = build_documentation_system_audit(ROOT)
    rendered = render_documentation_system_audit(report)
    assert "docs/STATUS.md exceeds headroom limit" not in rendered

