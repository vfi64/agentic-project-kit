#!/usr/bin/env python3
"""Apply the first post-merge handoff refresh automation slice locally."""

from __future__ import annotations

from pathlib import Path

MODULE = Path("src/agentic_project_kit/post_merge_handoff_refresh.py")
CLI = Path("src/agentic_project_kit/cli_commands/handoff.py")
TEST = Path("tests/test_post_merge_handoff_refresh.py")
LOG = Path("docs/reports/terminal/post-merge-handoff-refresh-automation-helper.log")

MODULE.write_text('''"""Deterministic post-merge handoff refresh status helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from agentic_project_kit.handoff_freshness import HandoffFreshnessReport, evaluate_handoff_freshness


@dataclass(frozen=True)
class PostMergeHandoffRefreshStatus:
    """Machine-readable status for post-merge handoff refresh needs."""

    current_head: str
    freshness_warning_present: bool
    refresh_required: bool
    latest_successor_prompt: str | None
    result: str
    next_safe_action: str


def evaluate_post_merge_handoff_refresh(project_root: Path = Path(".")) -> PostMergeHandoffRefreshStatus:
    """Return whether a post-merge handoff refresh is required.

    This first slice is read-only. It standardizes the decision that was previously
    inferred manually after merges: a freshness warning means the next safe action is
    an administrative handoff/status refresh, not product work.
    """

    report: HandoffFreshnessReport = evaluate_handoff_freshness(project_root)
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
        "from agentic_project_kit.handoff_state import HandoffStateError, load_handoff_state\n",
        "from agentic_project_kit.handoff_state import HandoffStateError, load_handoff_state\nfrom agentic_project_kit.post_merge_handoff_refresh import evaluate_post_merge_handoff_refresh, render_post_merge_handoff_refresh_status\n",
    )
    cli_text += '''\n\n@app.command("post-merge-refresh-status")\ndef post_merge_refresh_status() -> None:\n    """Report whether the current checkout needs a post-merge handoff refresh."""\n\n    status = evaluate_post_merge_handoff_refresh(Path("."))\n    typer.echo(render_post_merge_handoff_refresh_status(status), nl=False)\n    if status.refresh_required:\n        raise typer.Exit(1)\n'''
    CLI.write_text(cli_text, encoding="utf-8")

TEST.write_text('''from agentic_project_kit.post_merge_handoff_refresh import (\n    PostMergeHandoffRefreshStatus,\n    render_post_merge_handoff_refresh_status,\n)\n\n\ndef test_render_post_merge_handoff_refresh_status_noop():\n    rendered = render_post_merge_handoff_refresh_status(\n        PostMergeHandoffRefreshStatus(\n            current_head="abc123",\n            freshness_warning_present=False,\n            refresh_required=False,\n            latest_successor_prompt="docs/reports/terminal/prompt.md",\n            result="NOOP",\n            next_safe_action="continue_without_post_merge_handoff_refresh",\n        )\n    )\n\n    assert rendered.startswith("POST_MERGE_HANDOFF_REFRESH\\n")\n    assert "current_head=abc123" in rendered\n    assert "freshness_warning_present=False" in rendered\n    assert "refresh_required=False" in rendered\n    assert "result=NOOP" in rendered\n\n\ndef test_render_post_merge_handoff_refresh_status_required():\n    rendered = render_post_merge_handoff_refresh_status(\n        PostMergeHandoffRefreshStatus(\n            current_head="def456",\n            freshness_warning_present=True,\n            refresh_required=True,\n            latest_successor_prompt=None,\n            result="REFRESH_REQUIRED",\n            next_safe_action="create_administrative_handoff_refresh",\n        )\n    )\n\n    assert "current_head=def456" in rendered\n    assert "freshness_warning_present=True" in rendered\n    assert "refresh_required=True" in rendered\n    assert "latest_successor_prompt=" in rendered\n    assert "result=REFRESH_REQUIRED" in rendered\n    assert "next_safe_action=create_administrative_handoff_refresh" in rendered\n''', encoding="utf-8")

LOG.write_text("POST_MERGE_HANDOFF_REFRESH_AUTOMATION_HELPER\nresult=PASS\n", encoding="utf-8")
print(LOG)
print("result=PASS")
