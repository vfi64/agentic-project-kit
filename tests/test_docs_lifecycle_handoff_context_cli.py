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


def test_lifecycle_report_includes_handoff_context_when_available(tmp_path: Path) -> None:
    _write_registry(tmp_path, path="docs/planning/PROJECT_DIRECTION.md")
    _write_doc(
        tmp_path / "docs" / "planning" / "PROJECT_DIRECTION.md",
        "Status: active\nDecision status: accepted\nReview policy: required\n",
    )
    handoff_dir = tmp_path / "docs" / "reports" / "handoff-packages" / "latest"
    handoff_dir.mkdir(parents=True, exist_ok=True)
    (handoff_dir / "validation_report.json").write_text(
        json.dumps(
            {
                "result_status": "PASS",
                "head_status": "refresh_only_descendant",
                "generated_head": "abc123",
                "current_head": "def456",
            }
        ),
        encoding="utf-8",
    )

    output = tmp_path / "tmp" / "lifecycle-report.json"
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
    written = json.loads(output.read_text(encoding="utf-8"))
    handoff = written["handoff_context"]
    assert handoff["available"] is True
    assert handoff["result_status"] == "PASS"
    assert handoff["head_status"] == "refresh_only_descendant"
    assert handoff["severity"] == "advisory"
    assert handoff["safe_to_continue"] is True


def test_lifecycle_report_handoff_context_missing_is_advisory(tmp_path: Path) -> None:
    _write_registry(tmp_path, path="docs/planning/PROJECT_DIRECTION.md")
    _write_doc(
        tmp_path / "docs" / "planning" / "PROJECT_DIRECTION.md",
        "Status: active\nDecision status: accepted\nReview policy: required\n",
    )

    output = tmp_path / "tmp" / "lifecycle-report.json"
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
    written = json.loads(output.read_text(encoding="utf-8"))
    assert written["handoff_context"]["available"] is False
    assert written["handoff_context"]["severity"] == "advisory"


def test_lifecycle_report_result_mentions_handoff_context(tmp_path: Path) -> None:
    _write_registry(tmp_path, path="docs/planning/PROJECT_DIRECTION.md")
    _write_doc(
        tmp_path / "docs" / "planning" / "PROJECT_DIRECTION.md",
        "Status: active\nDecision status: accepted\nReview policy: required\n",
    )

    output = tmp_path / "tmp" / "lifecycle-report.json"
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
    assert "HANDOFF_CONTEXT:" in result.output
    assert "ARCHIVE: disabled" in result.output


def test_lifecycle_report_unknown_handoff_head_status_remains_advisory(tmp_path: Path) -> None:
    _write_registry(tmp_path, path="docs/planning/PROJECT_DIRECTION.md")
    _write_doc(
        tmp_path / "docs" / "planning" / "PROJECT_DIRECTION.md",
        "Status: active\nDecision status: accepted\nReview policy: required\n",
    )
    handoff_dir = tmp_path / "docs" / "reports" / "handoff-packages" / "latest"
    handoff_dir.mkdir(parents=True, exist_ok=True)
    (handoff_dir / "validation_report.json").write_text(
        json.dumps(
            {
                "result_status": "PASS",
                "generated_head": "abc123",
            }
        ),
        encoding="utf-8",
    )

    output = tmp_path / "tmp" / "lifecycle-report.json"
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
    written = json.loads(output.read_text(encoding="utf-8"))
    handoff = written["handoff_context"]
    assert handoff["available"] is True
    assert handoff["severity"] == "advisory"
    assert handoff["head_status"] is None
    assert handoff["safe_to_continue"] is True
