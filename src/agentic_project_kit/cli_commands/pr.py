from __future__ import annotations

import json
from pathlib import Path

import typer

from agentic_project_kit.ci_readiness import (
    WAITING,
    gh_pr_snapshot_provider,
    render_pr_readiness,
    wait_for_pr_readiness,
)
from agentic_project_kit.pr_closeout import BLOCKED, evaluate_pr_closeout, render_pr_closeout

pr_app = typer.Typer(help="Evaluate deterministic PR closeout and readiness state.")


@pr_app.command("closeout-check")
def closeout_check(json_file: Path) -> None:
    data = json.loads(json_file.read_text(encoding="utf-8"))
    result = evaluate_pr_closeout(data)
    typer.echo(render_pr_closeout(result))
    if result.outcome == BLOCKED:
        raise typer.Exit(code=1)


@pr_app.command("wait-ci")
def wait_ci(
    pr_number: int = typer.Argument(..., help="Pull request number to inspect."),
    expected_head_sha: str | None = typer.Option(
        None,
        "--expected-head-sha",
        help="Expected PR head SHA for --expected-head-sha. The command fails closed if the head moves.",
    ),
    timeout_seconds: int = typer.Option(2700, min=1, help="Maximum wait time."),
    interval_seconds: int = typer.Option(20, min=1, help="Polling interval."),
    expected_check: list[str] = typer.Option(
        [],
        "--expected-check",
        help="Check name that must be present before readiness can pass. Repeatable.",
    ),
) -> None:
    result = wait_for_pr_readiness(
        gh_pr_snapshot_provider(pr_number),
        expected_head_sha=expected_head_sha,
        timeout_seconds=timeout_seconds,
        interval_seconds=interval_seconds,
        expected_checks=tuple(expected_check),
    )
    typer.echo(render_pr_readiness(result))
    if not result.success:
        raise typer.Exit(code=2 if result.outcome == WAITING else 1)


def register_pr_closeout_alias(app: typer.Typer) -> None:
    @app.command("pr-closeout")
    def pr_closeout_alias(json_file: Path) -> None:
        data = json.loads(json_file.read_text(encoding="utf-8"))
        result = evaluate_pr_closeout(data)
        typer.echo(render_pr_closeout(result))
        if result.outcome == BLOCKED:
            raise typer.Exit(code=1)
