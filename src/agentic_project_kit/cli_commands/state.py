from __future__ import annotations

from pathlib import Path

import typer

from agentic_project_kit.execution_mode_state import evaluate_mode_switch, render_mode_check, write_mode_state
from agentic_project_kit.state_freshness import find_stale_state_fragments, format_findings

state_app = typer.Typer(help="Check repository state freshness and execution mode safety.")


@state_app.command("freshness-check")
def freshness_check() -> None:
    findings = find_stale_state_fragments()
    typer.echo(format_findings(findings))
    if findings:
        raise typer.Exit(1)


@state_app.command("mode-check")
def mode_check(
    target: str = typer.Argument(..., help="Execution target: local or remote."),
    expected_branch: str | None = typer.Option(None, "--expected-branch"),
    allow_dirty: bool = typer.Option(False, "--allow-dirty", help="Allow a dirty worktree."),
) -> None:
    if target not in {"local", "remote"}:
        typer.echo("ERROR: target must be 'local' or 'remote'.")
        raise typer.Exit(2)
    result = evaluate_mode_switch(Path("."), target, expected_branch=expected_branch, require_clean=not allow_dirty)
    typer.echo(render_mode_check(result))
    if not result.ok:
        raise typer.Exit(1)


@state_app.command("mode-write")
def mode_write(
    target: str = typer.Argument(..., help="Execution target: local or remote."),
    expected_branch: str | None = typer.Option(None, "--expected-branch"),
    reason: str = typer.Option("manual_mode_transition", "--reason"),
    allow_dirty: bool = typer.Option(False, "--allow-dirty", help="Allow a dirty worktree."),
) -> None:
    if target not in {"local", "remote"}:
        typer.echo("ERROR: target must be 'local' or 'remote'.")
        raise typer.Exit(2)
    result = evaluate_mode_switch(Path("."), target, expected_branch=expected_branch, require_clean=not allow_dirty)
    path = write_mode_state(Path("."), result, reason)
    typer.echo(render_mode_check(result))
    typer.echo(f"state_file={path.as_posix()}")
    if not result.ok:
        raise typer.Exit(1)
