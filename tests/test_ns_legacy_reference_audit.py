from __future__ import annotations

from pathlib import Path

import pytest
import typer

from agentic_project_kit import cli
from agentic_project_kit.ns_legacy_reference_audit import (
    audit_ns_legacy_references,
    classify_legacy_reference,
    render_ns_legacy_reference_audit,
)


def test_classifies_current_instruction_as_blocker() -> None:
    classification, reason = classify_legacy_reference("docs/handoff/START.md", "Run ./ns release-prep 0.4.9")
    assert classification == "current_instruction_blocker"
    assert "current instruction" in reason


def test_classifies_tests_as_fixture() -> None:
    classification, reason = classify_legacy_reference("tests/test_old_ns.py", "assert './ns' in help")
    assert classification == "test_fixture"
    assert "test" in reason


def test_classifies_changelog_with_legacy_marker_as_historical() -> None:
    classification, reason = classify_legacy_reference("CHANGELOG.md", "- Legacy ./ns release-prep was removed.")
    assert classification == "historical"
    assert "historical" in reason


def test_audit_blocks_current_doc_instruction(tmp_path: Path) -> None:
    doc = tmp_path / "docs" / "handoff" / "START.md"
    doc.parent.mkdir(parents=True)
    doc.write_text("Run ./ns release-prep 0.4.9\n", encoding="utf-8")

    result = audit_ns_legacy_references(tmp_path)

    assert result.ok is False
    assert result.status == "BLOCK"
    assert result.blockers
    assert result.blockers[0].path == "docs/handoff/START.md"


def test_audit_passes_historical_and_test_contexts(tmp_path: Path) -> None:
    changelog = tmp_path / "CHANGELOG.md"
    changelog.write_text("Legacy ./ns release-prep was removed.\n", encoding="utf-8")
    test = tmp_path / "tests" / "test_old.py"
    test.parent.mkdir(parents=True)
    test.write_text("assert './ns' in old_text\n", encoding="utf-8")

    result = audit_ns_legacy_references(tmp_path)

    assert result.ok is True
    assert result.status == "PASS"
    assert {reference.classification for reference in result.references} <= {
        "historical",
        "test_fixture",
        "release_history",
    }


def test_render_lists_blockers(tmp_path: Path) -> None:
    doc = tmp_path / "docs" / "handoff" / "START.md"
    doc.parent.mkdir(parents=True)
    doc.write_text("Use ./ns release-publish 0.4.9 publish-v0.4.9\n", encoding="utf-8")

    rendered = render_ns_legacy_reference_audit(audit_ns_legacy_references(tmp_path))

    assert "NS_LEGACY_REFERENCE_AUDIT" in rendered
    assert "STATUS=BLOCK" in rendered
    assert "BLOCKER=docs/handoff/START.md:1" in rendered


def test_cli_command_raises_on_block(tmp_path: Path, capsys) -> None:
    doc = tmp_path / "docs" / "handoff" / "START.md"
    doc.parent.mkdir(parents=True)
    doc.write_text("Run ./ns release-prep 0.4.9\n", encoding="utf-8")

    with pytest.raises(typer.Exit) as excinfo:
        cli.audit_ns_legacy_references_command(root=tmp_path, json_output=False)

    assert excinfo.value.exit_code == 1
    assert "STATUS=BLOCK" in capsys.readouterr().out


def test_cli_command_json_passes(tmp_path: Path, capsys) -> None:
    changelog = tmp_path / "CHANGELOG.md"
    changelog.write_text("Legacy ./ns command was removed.\n", encoding="utf-8")

    cli.audit_ns_legacy_references_command(root=tmp_path, json_output=True)

    out = capsys.readouterr().out
    assert '"status": "PASS"' in out
    assert '"references"' in out

def test_audit_skips_tmp_and_docs_reports_generated_evidence(tmp_path: Path) -> None:
    tmp_log = tmp_path / "tmp" / "old-audit.json"
    tmp_log.parent.mkdir(parents=True)
    tmp_log.write_text("Run ./ns release-prep 0.4.9\n", encoding="utf-8")

    report = tmp_path / "docs" / "reports" / "old.md"
    report.parent.mkdir(parents=True)
    report.write_text("Run ./ns release-prep 0.4.9\n", encoding="utf-8")

    result = audit_ns_legacy_references(tmp_path)

    assert result.ok is True
    assert result.references == ()

def test_classifies_planning_docs_as_legacy_documentation_context() -> None:
    classification, reason = classify_legacy_reference(
        "docs/governance/WORK_ORDER_WORKFLOW_CONTRACT.md",
        "Once ./ns next-turn exists, the assistant can use it.",
    )
    assert classification == "legacy_documentation_context"
    assert "documentation cleanup" in reason


def test_classifies_audit_implementation_tokens_as_compatibility_implementation() -> None:
    classification, reason = classify_legacy_reference(
        "src/agentic_project_kit/ns_legacy_reference_audit.py",
        're.compile(r"\\./ns\\b")',
    )
    assert classification == "compatibility_implementation"
    assert "compatibility patterns" in reason


def test_classifies_doc_currency_audit_legacy_guards_as_compatibility_implementation() -> None:
    classification, reason = classify_legacy_reference(
        "src/agentic_project_kit/doc_currency_audit.py",
        'if current_section and ("./ns" in current_section or "ns release-prep" in current_section):',
    )
    assert classification == "compatibility_implementation"
    assert "compatibility patterns" in reason


def test_classifies_workflow_docs_as_legacy_documentation_context() -> None:
    classification, reason = classify_legacy_reference(
        "docs/workflow/TERMINAL_LOG_HANDOFF_RULE.md",
        "Use ./ns terminal-upload for failure handoff.",
    )
    assert classification == "legacy_documentation_context"
    assert "documentation cleanup" in reason

def test_classifies_workflow_output_cycle_as_legacy_documentation_context() -> None:
    classification, reason = classify_legacy_reference(
        "docs/WORKFLOW_OUTPUT_CYCLE.md",
        "./ns run",
    )
    assert classification == "legacy_documentation_context"
    assert "documentation cleanup" in reason

def test_classifies_planning_docs_audit_patterns_as_compatibility_implementation() -> None:
    classification, reason = classify_legacy_reference(
        "src/agentic_project_kit/planning_docs_consolidation_audit.py",
        '"./ns",',
    )
    assert classification == "compatibility_implementation"
    assert "compatibility patterns" in reason
