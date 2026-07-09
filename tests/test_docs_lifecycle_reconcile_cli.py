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


def _write_scope(root: Path) -> None:
    scope = root / "docs" / "DOC_REGISTRY_SCOPE.yaml"
    scope.parent.mkdir(parents=True, exist_ok=True)
    scope.write_text(
        "version: 1\n"
        "required_paths:\n"
        "  - docs/planning\n"
        "exempt_paths: []\n",
        encoding="utf-8",
    )


def test_lifecycle_triage_includes_reconcile_findings(tmp_path: Path) -> None:
    _write_registry(tmp_path, path="docs/planning/PROJECT_DIRECTION.md")
    _write_scope(tmp_path)
    _write_doc(
        tmp_path / "docs" / "planning" / "PROJECT_DIRECTION.md",
        "Status: active\nDecision status: accepted\nReview policy: required\n",
    )
    _write_doc(
        tmp_path / "docs" / "governance" / "DOC_REGISTRY_SCOPE_DECISION.md",
        "# stale scope decision table\n",
    )

    result = runner.invoke(
        app,
        ["docs", "lifecycle", "triage", "--root", str(tmp_path), "--json"],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["reconcile"]["kind"] == "doc_registry_reconcile_report"
    assert payload["reconcile"]["mode"] == "dry-run"
    assert payload["summary"]["reconcile_findings"] == len(payload["reconcile"]["findings"])
    assert any(
        action.get("source") == "doc-registry-reconcile"
        for action in payload["proposed_actions"]
    )


def test_lifecycle_plan_includes_reconcile_advisory_steps(tmp_path: Path) -> None:
    _write_registry(tmp_path, path="docs/planning/PROJECT_DIRECTION.md")
    _write_scope(tmp_path)
    _write_doc(
        tmp_path / "docs" / "planning" / "PROJECT_DIRECTION.md",
        "Status: active\nDecision status: accepted\nReview policy: required\n",
    )
    _write_doc(
        tmp_path / "docs" / "governance" / "DOC_REGISTRY_SCOPE_DECISION.md",
        "# stale scope decision table\n",
    )

    result = runner.invoke(
        app,
        ["docs", "lifecycle", "plan", "--root", str(tmp_path), "--scope", "docs/governance", "--json"],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    reconcile_steps = [step for step in payload["steps"] if step["source"] == "doc-registry-reconcile"]
    assert reconcile_steps
    assert reconcile_steps[0]["operation"] == "defer"
    assert reconcile_steps[0]["safety_class"] == "advisory"
    assert reconcile_steps[0]["execute"] is False


def test_lifecycle_plan_text_mentions_reconcile_source(tmp_path: Path) -> None:
    _write_registry(tmp_path, path="docs/planning/PROJECT_DIRECTION.md")
    _write_scope(tmp_path)
    _write_doc(
        tmp_path / "docs" / "planning" / "PROJECT_DIRECTION.md",
        "Status: active\nDecision status: accepted\nReview policy: required\n",
    )
    _write_doc(
        tmp_path / "docs" / "governance" / "DOC_REGISTRY_SCOPE_DECISION.md",
        "# stale scope decision table\n",
    )

    result = runner.invoke(
        app,
        ["docs", "lifecycle", "plan", "--root", str(tmp_path), "--scope", "docs/governance"],
    )

    assert result.exit_code == 0, result.output
    assert "doc-registry-reconcile" in result.output
    assert "EXECUTION: disabled" in result.output
