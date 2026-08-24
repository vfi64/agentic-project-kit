from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.command_selector import (
    normalize_raw_command,
    render_command_selection,
    select_for_raw,
    select_for_task,
)


def _manifest() -> dict[str, object]:
    return {
        "commands": [
            {
                "qualified_name": "agentic-kit transfer push-current",
                "safety": "BOUNDED",
                "surface": "orchestrator",
                "when_to_use": "Push the current branch.",
                "dry_run_available": True,
                "replaces_raw": ["git push"],
                "task_tags": ["transfer", "bounded"],
            },
            {
                "qualified_name": "agentic-kit transfer push-force-safe",
                "safety": "DESTRUCTIVE",
                "surface": "primitive",
                "when_to_use": "Force-push with checks.",
                "dry_run_available": True,
                "replaces_raw": ["git push --force-with-lease"],
                "task_tags": ["transfer", "destructive"],
            },
            {
                "qualified_name": "agentic-kit audit-command-manifest",
                "safety": "READ_ONLY",
                "surface": "diagnostic",
                "when_to_use": "Audit command metadata.",
                "dry_run_available": False,
                "replaces_raw": [],
                "task_tags": ["audit", "read-only"],
            },
        ]
    }


def test_normalize_raw_command_strips_prompt_and_collapses_whitespace() -> None:
    assert normalize_raw_command("  $   git   push   origin   HEAD  ") == "git push origin HEAD"
    assert normalize_raw_command("> gh   pr   create") == "gh pr create"


def test_select_for_raw_uses_longest_replaces_raw_prefix() -> None:
    selection = select_for_raw(_manifest(), "git push --force-with-lease origin main")

    assert selection.status == "match"
    assert selection.payload["matched_prefix"] == "git push --force-with-lease"
    assert selection.payload["commands"][0]["qualified_name"] == "agentic-kit transfer push-force-safe"


def test_select_for_raw_reports_no_mapping_with_exit_zero_payload() -> None:
    selection = select_for_raw(_manifest(), "git status")

    assert selection.status == "no_match"
    assert selection.payload["message"] == (
        "no mapping; if this mutates the repo, check the manifest before running raw"
    )


def test_select_for_task_sorts_by_safety_then_name() -> None:
    selection = select_for_task(_manifest(), "transfer")

    assert selection.status == "match"
    assert [command["safety"] for command in selection.payload["commands"]] == [
        "BOUNDED",
        "DESTRUCTIVE",
    ]


def test_select_for_task_prefers_orchestrator_for_equivalent_candidates() -> None:
    manifest = {
        "commands": [
            {
                "qualified_name": "agentic-kit transfer commit",
                "safety": "BOUNDED",
                "surface": "primitive",
                "when_to_use": "Commit selected paths.",
                "task_tags": ["work"],
            },
            {
                "qualified_name": "agentic-kit workflow go",
                "safety": "BOUNDED",
                "surface": "orchestrator",
                "when_to_use": "Run the next governed workflow step.",
                "task_tags": ["work"],
            },
        ]
    }

    selection = select_for_task(manifest, "work")

    assert selection.status == "match"
    assert selection.payload["commands"][0]["qualified_name"] == "agentic-kit workflow go"


def test_select_for_task_keeps_more_specific_primitive_match() -> None:
    manifest = {
        "commands": [
            {
                "qualified_name": "agentic-kit workflow go",
                "safety": "BOUNDED",
                "surface": "orchestrator",
                "when_to_use": "Run the next governed workflow step.",
                "task_tags": ["work"],
            },
            {
                "qualified_name": "agentic-kit transfer commit",
                "safety": "BOUNDED",
                "surface": "primitive",
                "when_to_use": "Commit selected paths.",
                "task_tags": ["work-commit"],
            },
        ]
    }

    selection = select_for_task(manifest, "work-commit")

    assert selection.status == "match"
    assert [command["qualified_name"] for command in selection.payload["commands"]] == [
        "agentic-kit transfer commit"
    ]


def test_select_for_task_diagnostic_intent_prefers_diagnostic() -> None:
    manifest = {
        "commands": [
            {
                "qualified_name": "agentic-kit workflow go",
                "safety": "READ_ONLY",
                "surface": "orchestrator",
                "when_to_use": "Explain and run the next governed workflow step.",
                "task_tags": ["diagnose"],
            },
            {
                "qualified_name": "agentic-kit doctor",
                "safety": "READ_ONLY",
                "surface": "diagnostic",
                "when_to_use": "Run project health diagnostics.",
                "task_tags": ["diagnose"],
            },
        ]
    }

    selection = select_for_task(manifest, "diagnose")

    assert selection.status == "match"
    assert selection.payload["commands"][0]["qualified_name"] == "agentic-kit doctor"


def test_select_for_task_safety_still_wins_before_surface() -> None:
    manifest = {
        "commands": [
            {
                "qualified_name": "agentic-kit workflow go",
                "safety": "BOUNDED",
                "surface": "orchestrator",
                "when_to_use": "Run the next governed workflow step.",
                "task_tags": ["operate"],
            },
            {
                "qualified_name": "agentic-kit transfer repo-status",
                "safety": "READ_ONLY",
                "surface": "primitive",
                "when_to_use": "Inspect repository status.",
                "task_tags": ["operate"],
            },
        ]
    }

    selection = select_for_task(manifest, "operate")

    assert selection.status == "match"
    assert selection.payload["commands"][0]["qualified_name"] == "agentic-kit transfer repo-status"


def test_select_for_task_reports_invalid_surface() -> None:
    selection = select_for_task(
        {
            "commands": [
                {
                    "qualified_name": "agentic-kit mystery",
                    "safety": "READ_ONLY",
                    "surface": "internal",
                    "when_to_use": "Mystery command.",
                    "task_tags": ["mystery"],
                }
            ]
        },
        "mystery",
    )

    assert selection.status == "invalid_manifest"
    assert selection.payload["invalid_surfaces"] == [
        {"qualified_name": "agentic-kit mystery", "surface": "internal"}
    ]


def test_render_command_selection_includes_surface_deterministically() -> None:
    selection = select_for_task(_manifest(), "audit")

    rendered = render_command_selection(selection)

    assert rendered == render_command_selection(selection)
    assert "surface=diagnostic" in rendered


def test_select_for_task_unknown_tag_lists_available_tags() -> None:
    selection = select_for_task(_manifest(), "missing")

    assert selection.status == "unknown_tag"
    assert selection.payload["available_tags"] == [
        "audit",
        "bounded",
        "destructive",
        "read-only",
        "transfer",
    ]


def test_command_for_cli_json_shape() -> None:
    result = CliRunner().invoke(app, ["command-for", "--raw", "git push origin main", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["mode"] == "raw"
    assert payload["status"] == "match"
    assert payload["matched_prefix"] == "git push"
    assert payload["commands"][0]["qualified_name"] == "agentic-kit transfer push-current"
    assert payload["commands"][0]["surface"] == "primitive"


def test_command_for_cli_uses_packaged_manifest_in_external_workspace(tmp_path: Path) -> None:
    result = CliRunner().invoke(
        app,
        [
            "command-for",
            "--root",
            str(tmp_path),
            "--raw",
            "git push origin main",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["status"] == "match"
    assert payload["matched_prefix"] == "git push"
    assert payload["commands"][0]["qualified_name"] == "agentic-kit transfer push-current"
