import json
from pathlib import Path

import pytest
import typer
import yaml
from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.cli_commands.checks import doc_lifecycle_audit_command
from agentic_project_kit.doc_lifecycle import build_doc_lifecycle_report, render_doc_lifecycle_report, write_doc_lifecycle_json_report
from agentic_project_kit.documentation_registry import DOCUMENT_CLASSES, REGISTRY_PATH, REQUIRED_CLASS_RULE_FIELDS


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _class_rules() -> dict[str, dict[str, str]]:
    return {name: {field: f"{name} {field}" for field in REQUIRED_CLASS_RULE_FIELDS} for name in DOCUMENT_CLASSES}


def _write_registry(root: Path) -> None:
    registry = {
        "version": 1,
        "status": {"lifecycle": "initial", "broad_migration_allowed": False},
        "class_rules": _class_rules(),
        "documents": [
            {"path": "docs/ideas/EXAMPLE.md", "class": "planning", "owner": "maintainers"},
            {"path": "docs/strategy/NOW.md", "class": "operational/automation", "owner": "maintainers"},
        ],
    }
    _write(root / REGISTRY_PATH, yaml.safe_dump(registry, sort_keys=False))


def _write_valid_docs(root: Path) -> None:
    _write(root / "docs/ideas/EXAMPLE.md", "# Example\n\nStatus: idea-note\nDecision status: open\nReview policy: keep while useful\n")
    _write(root / "docs/strategy/NOW.md", "# Now\n\nStatus: active\nDecision status: current\nReview policy: review before milestones\n")


def test_doc_lifecycle_accepts_classified_documents(tmp_path: Path) -> None:
    _write_valid_docs(tmp_path)
    report = build_doc_lifecycle_report(tmp_path)
    assert report.ok
    assert report.registry_summary is None
    assert [document.path for document in report.documents] == ["docs/ideas/EXAMPLE.md", "docs/strategy/NOW.md"]


def test_doc_lifecycle_reports_missing_and_invalid_status(tmp_path: Path) -> None:
    _write(tmp_path / "docs/ideas/ISSUE.md", "# Issue\n\nStatus: idea note\n")
    _write(tmp_path / "docs/planning/MISSING.md", "# Missing\n\nDecision status: unclear\n")
    report = build_doc_lifecycle_report(tmp_path)
    codes = {finding.code for finding in report.findings}
    assert {"invalid-status", "missing-status", "missing-decision-status"} <= codes


def test_doc_lifecycle_requires_review_policy_for_active_and_idea_documents(tmp_path: Path) -> None:
    _write(tmp_path / "docs/strategy/NOW.md", "# Now\n\nStatus: active\nDecision status: current\n")
    report = build_doc_lifecycle_report(tmp_path)
    assert any(finding.code == "missing-review-policy" for finding in report.findings)


def test_doc_lifecycle_requires_lifecycle_note_for_closed_documents(tmp_path: Path) -> None:
    _write(tmp_path / "docs/roadmap/DONE.md", "# Done\n\nStatus: implemented\nDecision status: done\n")
    report = build_doc_lifecycle_report(tmp_path)
    assert any(finding.code == "missing-lifecycle-note" for finding in report.findings)


def test_doc_lifecycle_includes_registry_summary_when_available(tmp_path: Path) -> None:
    _write_valid_docs(tmp_path)
    _write_registry(tmp_path)
    report = build_doc_lifecycle_report(tmp_path)
    rendered = render_doc_lifecycle_report(report)
    assert report.ok
    assert report.registry_summary is not None
    assert report.registry_summary["registry_path"] == "docs/DOCUMENTATION_REGISTRY.yaml"
    assert report.registry_summary["document_count"] == 2
    assert report.registry_summary["broad_migration_allowed"] is False
    assert "Documentation registry:" in rendered
    assert "class:operational/automation: 1" in rendered


def test_doc_lifecycle_json_report_has_stable_shape(tmp_path: Path) -> None:
    _write(tmp_path / "docs/ideas/EXAMPLE.md", "# Example\n\nStatus: idea-note\nDecision status: open\nReview policy: keep while useful\n")
    report = build_doc_lifecycle_report(tmp_path)
    output_path = tmp_path / "reports" / "doc-lifecycle-report.json"
    write_doc_lifecycle_json_report(report, output_path)
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["ok"] is True
    assert payload["findings"] == []
    assert payload["registry_summary"] is None
    assert payload["documents"][0]["path"] == "docs/ideas/EXAMPLE.md"


def test_doc_lifecycle_json_report_includes_registry_summary(tmp_path: Path) -> None:
    _write_valid_docs(tmp_path)
    _write_registry(tmp_path)
    output_path = tmp_path / "reports" / "doc-lifecycle-report.json"
    write_doc_lifecycle_json_report(build_doc_lifecycle_report(tmp_path), output_path)
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["registry_summary"]["class_counts"]["planning"] == 1


def test_doc_lifecycle_audit_command_exits_nonzero_on_findings(tmp_path: Path) -> None:
    _write(tmp_path / "docs/ideas/ISSUE.md", "# Issue\n\nStatus: idea note\n")
    with pytest.raises(typer.Exit) as exc_info:
        doc_lifecycle_audit_command(tmp_path)
    assert exc_info.value.exit_code == 1


def test_doc_lifecycle_cli_command_reports_pass(tmp_path: Path) -> None:
    _write(tmp_path / "docs/ideas/EXAMPLE.md", "# Example\n\nStatus: idea-note\nDecision status: open\nReview policy: keep while useful\n")
    result = CliRunner().invoke(app, ["doc-lifecycle-audit", "--root", str(tmp_path)])
    assert result.exit_code == 0, result.output
    assert "Documentation lifecycle audit" in result.output
    assert "Overall: PASS" in result.output


def test_doc_lifecycle_cli_command_writes_report(tmp_path: Path) -> None:
    _write(tmp_path / "docs/ideas/ISSUE.md", "# Issue\n\nStatus: idea note\n")
    output_path = tmp_path / "doc-lifecycle-report.json"
    result = CliRunner().invoke(app, ["doc-lifecycle-audit", "--root", str(tmp_path), "--report", str(output_path)])
    assert result.exit_code == 1
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["ok"] is False
    assert payload["findings"][0]["code"] == "invalid-status"
