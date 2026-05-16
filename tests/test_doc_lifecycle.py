import json
from pathlib import Path

import pytest
import typer
from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.cli_commands.checks import doc_lifecycle_audit_command
from agentic_project_kit.doc_lifecycle import build_doc_lifecycle_report, write_doc_lifecycle_json_report


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_doc_lifecycle_accepts_classified_documents(tmp_path: Path) -> None:
    _write(tmp_path / "docs/ideas/EXAMPLE.md", "# Example\n\nStatus: idea-note\nDecision status: not implemented\nReview policy: keep while useful\n")
    _write(tmp_path / "docs/planning/OLD.md", "# Old\n\nStatus: superseded\nDecision status: replaced by later work\nLifecycle note: retained as historical context\n")
    _write(tmp_path / "docs/roadmap/DONE.md", "# Done\n\nStatus: implemented\nDecision status: implemented by release work\nLifecycle note: retained as historical context\n")
    _write(tmp_path / "docs/strategy/NOW.md", "# Now\n\nStatus: active\nDecision status: current strategy document\nReview policy: review before milestone planning\n")

    report = build_doc_lifecycle_report(tmp_path)

    assert report.ok
    assert [document.path for document in report.documents] == [
        "docs/ideas/EXAMPLE.md",
        "docs/planning/OLD.md",
        "docs/roadmap/DONE.md",
        "docs/strategy/NOW.md",
    ]


def test_doc_lifecycle_reports_missing_and_invalid_status(tmp_path: Path) -> None:
    _write(tmp_path / "docs/ideas/BAD.md", "# Bad\n\nStatus: idea note\n")
    _write(tmp_path / "docs/planning/MISSING.md", "# Missing\n\nDecision status: unclear\n")

    report = build_doc_lifecycle_report(tmp_path)

    assert not report.ok
    codes = {finding.code for finding in report.findings}
    assert "invalid-status" in codes
    assert "missing-status" in codes
    assert "missing-decision-status" in codes


def test_doc_lifecycle_requires_review_policy_for_active_and_idea_documents(tmp_path: Path) -> None:
    _write(tmp_path / "docs/strategy/NOW.md", "# Now\n\nStatus: active\nDecision status: current strategy\n")

    report = build_doc_lifecycle_report(tmp_path)

    assert not report.ok
    assert any(finding.code == "missing-review-policy" for finding in report.findings)


def test_doc_lifecycle_requires_lifecycle_note_for_closed_documents(tmp_path: Path) -> None:
    _write(tmp_path / "docs/roadmap/DONE.md", "# Done\n\nStatus: implemented\nDecision status: implemented\n")

    report = build_doc_lifecycle_report(tmp_path)

    assert not report.ok
    assert any(finding.code == "missing-lifecycle-note" for finding in report.findings)


def test_doc_lifecycle_json_report_has_stable_shape(tmp_path: Path) -> None:
    _write(tmp_path / "docs/ideas/EXAMPLE.md", "# Example\n\nStatus: idea-note\nDecision status: not implemented\nReview policy: keep while useful\n")
    report = build_doc_lifecycle_report(tmp_path)
    output_path = tmp_path / "reports" / "doc-lifecycle-report.json"

    write_doc_lifecycle_json_report(report, output_path)

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload == {
        "documents": [
            {
                "decision_status": "not implemented",
                "path": "docs/ideas/EXAMPLE.md",
                "status": "idea-note",
            }
        ],
        "findings": [],
        "ok": True,
    }


def test_doc_lifecycle_audit_command_exits_nonzero_on_findings(tmp_path: Path) -> None:
    _write(tmp_path / "docs/ideas/BAD.md", "# Bad\n\nStatus: idea note\n")

    with pytest.raises(typer.Exit) as exc_info:
        doc_lifecycle_audit_command(tmp_path)

    assert exc_info.value.exit_code == 1


def test_doc_lifecycle_cli_command_reports_pass(tmp_path: Path) -> None:
    _write(tmp_path / "docs/ideas/EXAMPLE.md", "# Example\n\nStatus: idea-note\nDecision status: not implemented\nReview policy: keep while useful\n")
    runner = CliRunner()

    result = runner.invoke(app, ["doc-lifecycle-audit", "--root", str(tmp_path)])

    assert result.exit_code == 0, result.output
    assert "Documentation lifecycle audit" in result.output
    assert "Overall: PASS" in result.output


def test_doc_lifecycle_cli_command_writes_report(tmp_path: Path) -> None:
    _write(tmp_path / "docs/ideas/BAD.md", "# Bad\n\nStatus: idea note\n")
    output_path = tmp_path / "doc-lifecycle-report.json"
    runner = CliRunner()

    result = runner.invoke(app, ["doc-lifecycle-audit", "--root", str(tmp_path), "--report", str(output_path)])

    assert result.exit_code == 1
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["ok"] is False
    assert payload["findings"][0]["code"] == "invalid-status"
