from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from agentic_project_kit.cli import app


runner = CliRunner()


def _write_doc(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_registry(root: Path, *, path: str) -> None:
    registry = root / "docs" / "DOCUMENTATION_REGISTRY.yaml"
    registry.parent.mkdir(parents=True, exist_ok=True)
    registry.write_text(
        "version: 1\n"
        "documents:\n"
        f"  - path: {path}\n"
        "    class: planning\n"
        "    owner: maintainers\n"
        "    status: active\n"
        "    review_policy: required\n",
        encoding="utf-8",
    )


def test_lifecycle_report_dry_run_does_not_write(tmp_path: Path) -> None:
    _write_registry(tmp_path, path="docs/planning/PROJECT_DIRECTION.md")
    _write_doc(
        tmp_path / "docs" / "planning" / "PROJECT_DIRECTION.md",
        "Status: active\nDecision status: accepted\nReview policy: required\n",
    )
    output = tmp_path / "docs" / "architecture" / "evidence" / "lifecycle.json"

    result = runner.invoke(
        app,
        [
            "docs",
            "lifecycle",
            "report",
            "--root",
            str(tmp_path),
            "--scope",
            "docs/planning",
            "--output",
            str(output),
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["kind"] == "doc_lifecycle_evidence_report_result"
    assert payload["mode"] == "dry-run"
    assert payload["mutation"] == "none"
    assert payload["would_write"] is True
    assert not output.exists()


def test_lifecycle_report_execute_writes_evidence_json(tmp_path: Path) -> None:
    _write_registry(tmp_path, path="docs/planning/PROJECT_DIRECTION.md")
    _write_doc(
        tmp_path / "docs" / "planning" / "PROJECT_DIRECTION.md",
        "Status: active\nDecision status: accepted\nReview policy: required\n",
    )
    output = tmp_path / "docs" / "architecture" / "evidence" / "lifecycle.json"

    result = runner.invoke(
        app,
        [
            "docs",
            "lifecycle",
            "report",
            "--root",
            str(tmp_path),
            "--scope",
            "docs/planning",
            "--output",
            str(output),
            "--execute",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["result_status"] == "PASS"
    assert payload["mutation"] == "write-report"
    assert payload["output_path"].endswith("docs/architecture/evidence/lifecycle.json")
    written = json.loads(output.read_text(encoding="utf-8"))
    assert written["kind"] == "doc_lifecycle_evidence_report"
    assert written["scope"] == "docs/planning"
    assert written["plan"]["result_status"] == "PASS"
    assert written["triage"]["result_status"] == "PASS"


def test_lifecycle_report_rejects_output_outside_evidence_roots(tmp_path: Path) -> None:
    _write_registry(tmp_path, path="docs/planning/PROJECT_DIRECTION.md")
    _write_doc(
        tmp_path / "docs" / "planning" / "PROJECT_DIRECTION.md",
        "Status: active\nDecision status: accepted\nReview policy: required\n",
    )
    output = tmp_path / "docs" / "planning" / "lifecycle.json"

    result = runner.invoke(
        app,
        [
            "docs",
            "lifecycle",
            "report",
            "--root",
            str(tmp_path),
            "--scope",
            "docs/planning",
            "--output",
            str(output),
            "--execute",
            "--json",
        ],
    )

    assert result.exit_code == 2, result.output
    payload = json.loads(result.output)
    assert payload["result_status"] == "BLOCK"
    assert payload["reason"] == "output_path_not_allowed"


def test_lifecycle_report_text_mentions_evidence_and_no_archive(tmp_path: Path) -> None:
    _write_registry(tmp_path, path="docs/planning/PROJECT_DIRECTION.md")
    _write_doc(
        tmp_path / "docs" / "planning" / "PROJECT_DIRECTION.md",
        "Status: active\nDecision status: accepted\nReview policy: required\n",
    )
    output = tmp_path / "docs" / "architecture" / "evidence" / "lifecycle.json"

    result = runner.invoke(
        app,
        [
            "docs",
            "lifecycle",
            "report",
            "--root",
            str(tmp_path),
            "--scope",
            "docs/planning",
            "--output",
            str(output),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "DOC_LIFECYCLE_EVIDENCE_REPORT" in result.output
    assert "MUTATION: none" in result.output
    assert "ARCHIVE: disabled" in result.output
