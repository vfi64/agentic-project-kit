from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from agentic_project_kit.cli import app


runner = CliRunner()


def _write_doc(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_docs_lifecycle_plan_json_is_dry_run_and_has_scope(tmp_path: Path) -> None:
    _write_doc(
        tmp_path / "docs" / "planning" / "PROJECT_DIRECTION.md",
        "Status: active\n"
        "Decision status: accepted\n"
        "Review policy: review after major release\n",
    )

    result = runner.invoke(
        app,
        ["docs", "lifecycle", "plan", "--root", str(tmp_path), "--scope", "docs/planning", "--json"],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["kind"] == "doc_lifecycle_plan"
    assert payload["mode"] == "dry-run"
    assert payload["scope"] == "docs/planning"
    assert payload["result_status"] == "PASS"
    assert payload["summary"]["steps"] == 1
    assert payload["steps"][0]["operation"] == "confirm-current"
    assert payload["steps"][0]["execute"] is False
    assert payload["steps"][0]["safety_class"] == "no-op-confirmation"


def test_docs_lifecycle_plan_scope_filters_actions(tmp_path: Path) -> None:
    _write_doc(
        tmp_path / "docs" / "planning" / "PLAN.md",
        "Status: active\nDecision status: accepted\nReview policy: review after major release\n",
    )
    _write_doc(
        tmp_path / "docs" / "architecture" / "ARCH.md",
        "Status: active\nDecision status: accepted\nReview policy: review after major release\n",
    )

    result = runner.invoke(
        app,
        ["docs", "lifecycle", "plan", "--root", str(tmp_path), "--scope", "docs/planning", "--json"],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert [step["path"] for step in payload["steps"]] == ["docs/planning/PLAN.md"]


def test_docs_lifecycle_plan_blocks_when_triage_blocks(tmp_path: Path) -> None:
    _write_doc(
        tmp_path / "docs" / "planning" / "BROKEN.md",
        "Status: definitely-current\nDecision status: accepted\nReview policy: keep\n",
    )

    result = runner.invoke(
        app,
        ["docs", "lifecycle", "plan", "--root", str(tmp_path), "--scope", "docs/planning", "--json"],
    )

    assert result.exit_code == 2, result.output
    payload = json.loads(result.output)
    assert payload["result_status"] == "BLOCK"
    assert payload["summary"]["failures"] == 1
    assert payload["steps"][0]["operation"] == "manual-review"
    assert payload["steps"][0]["safety_class"] == "human-decision-required"


def test_docs_lifecycle_plan_text_mentions_no_execute(tmp_path: Path) -> None:
    _write_doc(
        tmp_path / "docs" / "planning" / "PROJECT_DIRECTION.md",
        "Status: active\nDecision status: accepted\nReview policy: review after major release\n",
    )

    result = runner.invoke(
        app,
        ["docs", "lifecycle", "plan", "--root", str(tmp_path), "--scope", "docs/planning"],
    )

    assert result.exit_code == 0, result.output
    assert "DOC_LIFECYCLE_PLAN" in result.output
    assert "MODE: dry-run" in result.output
    assert "EXECUTION: disabled" in result.output
    assert "confirm-current" in result.output
