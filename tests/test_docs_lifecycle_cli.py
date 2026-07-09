from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from agentic_project_kit.cli import app


runner = CliRunner()


def _write_doc(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_docs_lifecycle_triage_json_is_dry_run_and_warn_only_for_missing_metadata(tmp_path: Path) -> None:
    _write_doc(
        tmp_path / "docs" / "planning" / "OLD_PLAN.md",
        "# Old plan\n\nThis document has no lifecycle headers yet.\n",
    )

    result = runner.invoke(
        app,
        ["docs", "lifecycle", "triage", "--root", str(tmp_path), "--json"],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["kind"] == "doc_lifecycle_triage_report"
    assert payload["mode"] == "dry-run"
    assert payload["result_status"] == "PASS"
    assert payload["summary"]["failures"] == 0
    assert payload["summary"]["warnings"] >= 1
    assert payload["findings"][0]["severity"] == "WARN"
    assert payload["proposed_actions"][0]["operation"] == "defer"


def test_docs_lifecycle_triage_blocks_invalid_status_as_event_conflict(tmp_path: Path) -> None:
    _write_doc(
        tmp_path / "docs" / "planning" / "BROKEN_PLAN.md",
        "Status: definitely-current\n"
        "Decision status: accepted\n"
        "Review policy: keep reviewed by maintainers\n",
    )

    result = runner.invoke(
        app,
        ["docs", "lifecycle", "triage", "--root", str(tmp_path), "--json"],
    )

    assert result.exit_code == 2, result.output
    payload = json.loads(result.output)
    assert payload["result_status"] == "BLOCK"
    assert payload["summary"]["failures"] == 1
    assert payload["findings"][0]["severity"] == "FAIL"
    assert payload["proposed_actions"][0]["operation"] == "manual-review"


def test_docs_lifecycle_triage_text_mentions_no_auto_apply(tmp_path: Path) -> None:
    _write_doc(
        tmp_path / "docs" / "planning" / "ACTIVE_PLAN.md",
        "Status: active\n"
        "Decision status: accepted\n"
        "Review policy: review after major release\n",
    )

    result = runner.invoke(
        app,
        ["docs", "lifecycle", "triage", "--root", str(tmp_path)],
    )

    assert result.exit_code == 0, result.output
    assert "DOC_LIFECYCLE_TRIAGE" in result.output
    assert "MODE: dry-run" in result.output
    assert "AUTO_APPLY: disabled" in result.output
    assert "confirm-current" in result.output
