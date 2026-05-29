#!/usr/bin/env python3
"""Apply the first post-merge handoff refresh automation slice locally."""

from __future__ import annotations

from pathlib import Path

MODULE = Path("src/agentic_project_kit/post_merge_handoff_refresh.py")
CLI = Path("src/agentic_project_kit/cli_commands/handoff.py")
TEST = Path("tests/test_post_merge_handoff_refresh.py")
LOG = Path("docs/reports/terminal/post-merge-handoff-refresh-automation-helper.log")

MODULE.write_text(r'''"""Deterministic post-merge handoff refresh status helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from agentic_project_kit.handoff_freshness import HandoffFreshnessReport, assess_handoff_prompt_freshness
from agentic_project_kit.handoff_prompt import render_handoff_prompt
from agentic_project_kit.handoff_state import load_handoff_state


@dataclass(frozen=True)
class PostMergeHandoffRefreshStatus:
    """Machine-readable status for post-merge handoff refresh needs."""

    current_head: str
    freshness_warning_present: bool
    refresh_required: bool
    latest_successor_prompt: str | None
    result: str
    next_safe_action: str


def evaluate_post_merge_handoff_refresh(
    project_root: Path = Path("."),
    *,
    state_path: str = ".agentic/handoff_state.yaml",
) -> PostMergeHandoffRefreshStatus:
    """Return whether a post-merge handoff refresh is required.

    This first slice is read-only. It standardizes the decision that was previously
    inferred manually after merges: a freshness warning means the next safe action is
    an administrative handoff/status refresh, not product work.
    """

    state_file = project_root / state_path
    data = load_handoff_state(str(state_file))
    rendered_prompt = render_handoff_prompt(data)
    report: HandoffFreshnessReport = assess_handoff_prompt_freshness(
        data,
        str(state_file),
        successor_prompt_text=rendered_prompt,
    )
    warning = report.warning_needed
    return PostMergeHandoffRefreshStatus(
        current_head=report.current_head,
        freshness_warning_present=warning,
        refresh_required=warning,
        latest_successor_prompt=report.latest_successor_prompt,
        result="REFRESH_REQUIRED" if warning else "NOOP",
        next_safe_action=(
            "create_administrative_handoff_refresh"
            if warning
            else "continue_without_post_merge_handoff_refresh"
        ),
    )


def render_post_merge_handoff_refresh_status(status: PostMergeHandoffRefreshStatus) -> str:
    """Render a stable, grep-friendly status block."""

    return "\n".join(
        [
            "POST_MERGE_HANDOFF_REFRESH",
            f"current_head={status.current_head}",
            f"freshness_warning_present={str(status.freshness_warning_present)}",
            f"refresh_required={str(status.refresh_required)}",
            f"latest_successor_prompt={status.latest_successor_prompt or ''}",
            f"result={status.result}",
            f"next_safe_action={status.next_safe_action}",
        ]
    ) + "\n"
''', encoding="utf-8")

cli_text = CLI.read_text(encoding="utf-8")
if "post_merge_handoff_refresh" not in cli_text:
    cli_text = cli_text.replace(
        "from agentic_project_kit.handoff_state import (\n",
        "from agentic_project_kit.handoff_state import (\n",
    )
    cli_text = cli_text.replace(
        ")\n\nhandoff_app = typer.Typer",
        ")\nfrom agentic_project_kit.post_merge_handoff_refresh import (\n    evaluate_post_merge_handoff_refresh,\n    render_post_merge_handoff_refresh_status,\n)\n\nhandoff_app = typer.Typer",
        1,
    )
    cli_text += '''\n\n@handoff_app.command("post-merge-refresh-status")\ndef post_merge_refresh_status() -> None:\n    """Report whether the current checkout needs a post-merge handoff refresh."""\n\n    status = evaluate_post_merge_handoff_refresh(Path("."))\n    typer.echo(render_post_merge_handoff_refresh_status(status), nl=False)\n    if status.refresh_required:\n        raise typer.Exit(1)\n'''
    CLI.write_text(cli_text, encoding="utf-8")

TEST.write_text(r'''from agentic_project_kit.post_merge_handoff_refresh import (
    PostMergeHandoffRefreshStatus,
    render_post_merge_handoff_refresh_status,
)


def test_render_post_merge_handoff_refresh_status_noop():
    rendered = render_post_merge_handoff_refresh_status(
        PostMergeHandoffRefreshStatus(
            current_head="abc123",
            freshness_warning_present=False,
            refresh_required=False,
            latest_successor_prompt="docs/reports/terminal/prompt.md",
            result="NOOP",
            next_safe_action="continue_without_post_merge_handoff_refresh",
        )
    )

    assert rendered.startswith("POST_MERGE_HANDOFF_REFRESH\n")
    assert "current_head=abc123" in rendered
    assert "freshness_warning_present=False" in rendered
    assert "refresh_required=False" in rendered
    assert "result=NOOP" in rendered


def test_render_post_merge_handoff_refresh_status_required():
    rendered = render_post_merge_handoff_refresh_status(
        PostMergeHandoffRefreshStatus(
            current_head="def456",
            freshness_warning_present=True,
            refresh_required=True,
            latest_successor_prompt=None,
            result="REFRESH_REQUIRED",
            next_safe_action="create_administrative_handoff_refresh",
        )
    )

    assert "current_head=def456" in rendered
    assert "freshness_warning_present=True" in rendered
    assert "refresh_required=True" in rendered
    assert "latest_successor_prompt=" in rendered
    assert "result=REFRESH_REQUIRED" in rendered
    assert "next_safe_action=create_administrative_handoff_refresh" in rendered
''', encoding="utf-8")

LOG.write_text("POST_MERGE_HANDOFF_REFRESH_AUTOMATION_HELPER\nresult=PASS\n", encoding="utf-8")
print(LOG)
print("result=PASS")
