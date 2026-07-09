from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from agentic_project_kit.cli import app


runner = CliRunner()


def _write_doc(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_registry(root: Path, *, path: str, doc_class: str = "planning") -> None:
    registry = root / "docs" / "DOCUMENTATION_REGISTRY.yaml"
    registry.parent.mkdir(parents=True, exist_ok=True)
    registry.write_text(
        "version: 1\n"
        "documents:\n"
        f"  - path: {path}\n"
        f"    class: {doc_class}\n"
        "    owner: maintainers\n"
        "    status: active\n"
        "    review_policy: required\n"
        "    summary: Registry-backed lifecycle fixture\n",
        encoding="utf-8",
    )


def test_lifecycle_triage_marks_docs_unknown_without_registry(tmp_path: Path) -> None:
    _write_doc(
        tmp_path / "docs" / "planning" / "PROJECT_DIRECTION.md",
        "Status: active\nDecision status: accepted\nReview policy: review after major release\n",
    )

    result = runner.invoke(
        app,
        ["docs", "lifecycle", "triage", "--root", str(tmp_path), "--json"],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    document = payload["documents"][0]
    assert document["path"] == "docs/planning/PROJECT_DIRECTION.md"
    assert document["registry"]["registered"] is None
    assert document["registry"]["scope"] == "unknown"


def test_lifecycle_triage_includes_real_registry_metadata(tmp_path: Path) -> None:
    _write_registry(tmp_path, path="docs/planning/PROJECT_DIRECTION.md", doc_class="planning")
    _write_doc(
        tmp_path / "docs" / "planning" / "PROJECT_DIRECTION.md",
        "Status: active\nDecision status: accepted\nReview policy: required\n",
    )

    result = runner.invoke(
        app,
        ["docs", "lifecycle", "triage", "--root", str(tmp_path), "--json"],
    )

    assert result.exit_code == 0, result.output
    document = json.loads(result.output)["documents"][0]
    assert document["registry"]["registered"] is True
    assert document["registry"]["doc_class"] == "planning"
    assert document["registry"]["owner"] == "maintainers"
    assert document["registry"]["status"] == "active"
    assert document["registry"]["review_policy"] == "required"
    assert document["registry"]["summary"] == "Registry-backed lifecycle fixture"


def test_lifecycle_plan_steps_include_real_registry_metadata(tmp_path: Path) -> None:
    _write_registry(tmp_path, path="docs/planning/PROJECT_DIRECTION.md", doc_class="planning")
    _write_doc(
        tmp_path / "docs" / "planning" / "PROJECT_DIRECTION.md",
        "Status: active\nDecision status: accepted\nReview policy: required\n",
    )

    result = runner.invoke(
        app,
        ["docs", "lifecycle", "plan", "--root", str(tmp_path), "--scope", "docs/planning", "--json"],
    )

    assert result.exit_code == 0, result.output
    step = json.loads(result.output)["steps"][0]
    assert step["path"] == "docs/planning/PROJECT_DIRECTION.md"
    assert step["registry"]["registered"] is True
    assert step["registry"]["doc_class"] == "planning"
    assert step["registry"]["owner"] == "maintainers"
    assert step["registry"]["scope"] == "in-scope"


def test_lifecycle_plan_text_mentions_registry_class_when_available(tmp_path: Path) -> None:
    _write_registry(tmp_path, path="docs/planning/PROJECT_DIRECTION.md", doc_class="planning")
    _write_doc(
        tmp_path / "docs" / "planning" / "PROJECT_DIRECTION.md",
        "Status: active\nDecision status: accepted\nReview policy: required\n",
    )

    result = runner.invoke(
        app,
        ["docs", "lifecycle", "plan", "--root", str(tmp_path), "--scope", "docs/planning"],
    )

    assert result.exit_code == 0, result.output
    assert "class=planning" in result.output
    assert "owner=maintainers" in result.output


def test_lifecycle_triage_does_not_expose_internal_registry_lookup(tmp_path: Path) -> None:
    _write_registry(tmp_path, path="docs/planning/PROJECT_DIRECTION.md", doc_class="planning")
    _write_doc(
        tmp_path / "docs" / "planning" / "PROJECT_DIRECTION.md",
        "Status: active\nDecision status: accepted\nReview policy: required\n",
    )

    result = runner.invoke(
        app,
        ["docs", "lifecycle", "triage", "--root", str(tmp_path), "--json"],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert "entries_by_path" not in (payload.get("registry_summary") or {})
    assert payload["documents"][0]["registry"]["doc_class"] == "planning"
