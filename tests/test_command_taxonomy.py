from __future__ import annotations

import json
from pathlib import Path

from agentic_project_kit.command_taxonomy import (
    ALLOWED_COMMAND_CATEGORIES,
    build_command_taxonomy_report,
    classify_command,
    render_command_taxonomy_report,
)


def test_classify_root_audit_commands_as_audit() -> None:
    entry = classify_command(
        {
            "qualified_name": "agentic-kit audit-doc-currency",
            "group": "root",
            "path": ["audit-doc-currency"],
            "help": "Audit docs",
        }
    )

    assert entry.category == "audit"
    assert entry.role


def test_classify_release_publish_as_release() -> None:
    entry = classify_command(
        {
            "qualified_name": "agentic-kit release-publish",
            "group": "root",
            "path": ["release-publish"],
            "help": "Publish release",
        }
    )

    assert entry.category == "release"


def test_command_taxonomy_report_requires_valid_categories(tmp_path: Path) -> None:
    ref = tmp_path / "docs" / "reference"
    ref.mkdir(parents=True)
    (ref / "agentic-kit-commands.json").write_text(
        json.dumps(
            {
                "commands": [
                    {
                        "qualified_name": "agentic-kit audit-doc-currency",
                        "group": "root",
                        "path": ["audit-doc-currency"],
                        "help": "Audit docs",
                    },
                    {
                        "qualified_name": "agentic-kit transfer repo-status",
                        "group": "transfer",
                        "path": ["transfer", "repo-status"],
                        "help": "Status",
                    },
                ]
            }
        ),
        encoding="utf-8",
    )

    report = build_command_taxonomy_report(tmp_path)

    assert report.ok
    assert {entry.category for entry in report.entries} <= set(ALLOWED_COMMAND_CATEGORIES)


def test_render_command_taxonomy_report() -> None:
    report = build_command_taxonomy_report(Path("."))

    rendered = render_command_taxonomy_report(report)

    assert "COMMAND_TAXONOMY_CHECK" in rendered
    assert "COMMAND_COUNT=" in rendered
    assert "CATEGORY=" in rendered

def test_classify_patch_scope_preflight_as_diagnostic() -> None:
    entry = classify_command(
        {
            "qualified_name": "agentic-kit patch-scope-preflight",
            "group": "root",
            "path": ["patch-scope-preflight"],
            "help": "Diagnose patch scope",
        }
    )

    assert entry.category == "diagnostic"

def test_classify_project_direction_as_docs() -> None:
    entry = classify_command(
        {
            "qualified_name": "agentic-kit project-direction",
            "group": "root",
            "path": ["project-direction"],
            "help": "Render project direction",
        }
    )

    assert entry.category == "docs"


def test_classify_direction_group_as_docs() -> None:
    entry = classify_command(
        {
            "qualified_name": "agentic-kit direction validate",
            "group": "direction",
            "path": ["direction", "validate"],
            "help": "Validate direction",
        }
    )

    assert entry.category == "docs"



def test_classify_pr_closeout_complete_as_preferred_composite() -> None:
    entry = classify_command(
        {
            "qualified_name": "agentic-kit transfer pr-closeout-complete",
            "group": "transfer",
            "path": ["transfer", "pr-closeout-complete"],
            "help": "Complete PR closeout",
        }
    )

    assert entry.category == "transfer"
    assert entry.composition_level == "composite"
    assert entry.recommendation_weight == 100
    assert "Preferred high-level wrapper" in entry.role


def test_render_command_taxonomy_report_includes_preferred_composites() -> None:
    report = build_command_taxonomy_report(Path("."))

    rendered = render_command_taxonomy_report(report)

    assert "COMPOSITION_LEVEL=" in rendered
    assert "PREFERRED=agentic-kit transfer pr-closeout-complete" in rendered
