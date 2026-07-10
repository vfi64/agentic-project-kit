from __future__ import annotations

import json

from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.command_selector import (
    normalize_raw_command,
    select_for_raw,
    select_for_task,
)


def _manifest() -> dict[str, object]:
    return {
        "commands": [
            {
                "qualified_name": "agentic-kit transfer push-current",
                "safety": "BOUNDED",
                "when_to_use": "Push the current branch.",
                "dry_run_available": True,
                "replaces_raw": ["git push"],
                "task_tags": ["transfer", "bounded"],
            },
            {
                "qualified_name": "agentic-kit transfer push-force-safe",
                "safety": "DESTRUCTIVE",
                "when_to_use": "Force-push with checks.",
                "dry_run_available": True,
                "replaces_raw": ["git push --force-with-lease"],
                "task_tags": ["transfer", "destructive"],
            },
            {
                "qualified_name": "agentic-kit audit-command-manifest",
                "safety": "READ_ONLY",
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
