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


def test_lifecycle_apply_requires_execute_flag(tmp_path: Path) -> None:
    _write_registry(tmp_path, path="docs/planning/PROJECT_DIRECTION.md")
    _write_doc(
        tmp_path / "docs" / "planning" / "PROJECT_DIRECTION.md",
        "Status: active\nDecision status: accepted\nReview policy: required\n",
    )

    result = runner.invoke(
        app,
        [
            "docs",
            "lifecycle",
            "apply",
            "--root",
            str(tmp_path),
            "--scope",
            "docs/planning",
            "--only",
            "docs/planning/PROJECT_DIRECTION.md:confirm-current",
            "--json",
        ],
    )

    assert result.exit_code == 2, result.output
    payload = json.loads(result.output)
    assert payload["result_status"] == "BLOCK"
    assert payload["reason"] == "missing_execute_flag"


def test_lifecycle_apply_confirm_current_is_noop_with_execute(tmp_path: Path) -> None:
    _write_registry(tmp_path, path="docs/planning/PROJECT_DIRECTION.md")
    target = tmp_path / "docs" / "planning" / "PROJECT_DIRECTION.md"
    _write_doc(
        target,
        "Status: active\nDecision status: accepted\nReview policy: required\n",
    )
    before = target.read_text(encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "docs",
            "lifecycle",
            "apply",
            "--root",
            str(tmp_path),
            "--scope",
            "docs/planning",
            "--only",
            "docs/planning/PROJECT_DIRECTION.md:confirm-current",
            "--execute",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["kind"] == "doc_lifecycle_apply_result"
    assert payload["result_status"] == "PASS"
    assert payload["applied"]["operation"] == "confirm-current"
    assert payload["applied"]["effect"] == "no-op"
    assert target.read_text(encoding="utf-8") == before


def test_lifecycle_apply_defer_is_noop_with_execute(tmp_path: Path) -> None:
    _write_registry(tmp_path, path="docs/planning/PROJECT_DIRECTION.md")
    _write_doc(
        tmp_path / "docs" / "planning" / "PROJECT_DIRECTION.md",
        "Status: active\nDecision status: accepted\nReview policy: required\n",
    )
    _write_doc(
        tmp_path / "docs" / "governance" / "DOC_REGISTRY_SCOPE_DECISION.md",
        "# stale scope decision table\n",
    )
    scope = tmp_path / "docs" / "DOC_REGISTRY_SCOPE.yaml"
    scope.write_text(
        "schema_version: 1\nrequired_paths:\n  - docs/planning\nexempt_paths: []\n",
        encoding="utf-8",
    )

    plan_result = runner.invoke(
        app,
        ["docs", "lifecycle", "plan", "--root", str(tmp_path), "--scope", "docs/governance", "--json"],
    )
    assert plan_result.exit_code == 0, plan_result.output
    plan_payload = json.loads(plan_result.output)
    step_id = next(
        step["id"]
        for step in plan_payload["steps"]
        if step["operation"] == "defer" and step["source"] == "doc-registry-reconcile"
    )

    result = runner.invoke(
        app,
        [
            "docs",
            "lifecycle",
            "apply",
            "--root",
            str(tmp_path),
            "--scope",
            "docs/governance",
            "--only",
            step_id,
            "--execute",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["result_status"] == "PASS"
    assert payload["applied"]["operation"] == "defer"
    assert payload["applied"]["effect"] == "no-op"


def test_lifecycle_apply_rejects_manual_review_operations(tmp_path: Path) -> None:
    _write_doc(
        tmp_path / "docs" / "planning" / "BROKEN.md",
        "Status: definitely-current\nDecision status: accepted\nReview policy: required\n",
    )

    result = runner.invoke(
        app,
        [
            "docs",
            "lifecycle",
            "apply",
            "--root",
            str(tmp_path),
            "--scope",
            "docs/planning",
            "--only",
            "docs/planning/BROKEN.md:invalid-status",
            "--execute",
            "--json",
        ],
    )

    assert result.exit_code == 2, result.output
    payload = json.loads(result.output)
    assert payload["result_status"] == "BLOCK"
    assert payload["reason"] == "unsafe_operation"


def test_lifecycle_apply_text_mentions_no_mutation(tmp_path: Path) -> None:
    _write_registry(tmp_path, path="docs/planning/PROJECT_DIRECTION.md")
    _write_doc(
        tmp_path / "docs" / "planning" / "PROJECT_DIRECTION.md",
        "Status: active\nDecision status: accepted\nReview policy: required\n",
    )

    result = runner.invoke(
        app,
        [
            "docs",
            "lifecycle",
            "apply",
            "--root",
            str(tmp_path),
            "--scope",
            "docs/planning",
            "--only",
            "docs/planning/PROJECT_DIRECTION.md:confirm-current",
            "--execute",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "DOC_LIFECYCLE_APPLY" in result.output
    assert "EFFECT: no-op" in result.output
    assert "MUTATION: none" in result.output
