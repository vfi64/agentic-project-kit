from __future__ import annotations

from typing import Annotated

import typer

from agentic_project_kit.handoff_prompt import render_handoff_prompt
from agentic_project_kit.handoff_state import current_git_safe_state, load_handoff_state, refresh_handoff_safe_state, save_handoff_state, summarize_handoff_state, validate_handoff_state

handoff_app = typer.Typer(help="Read-only persistent handoff state commands.")

@handoff_app.command("show")
def show(path: str = ".agentic/handoff_state.yaml") -> None:
    data = load_handoff_state(path)
    typer.echo(summarize_handoff_state(data))

@handoff_app.command("check")
def check(path: str = ".agentic/handoff_state.yaml") -> None:
    data = load_handoff_state(path)
    errors = validate_handoff_state(data)
    if errors:
        for error in errors:
            typer.echo(f"[FAIL] {error}")
        raise typer.Exit(code=1)
    typer.echo("Persistent handoff state check passed")

@handoff_app.command("prompt")
def prompt(path: str = ".agentic/handoff_state.yaml") -> None:
    data = load_handoff_state(path)
    errors = validate_handoff_state(data)
    if errors:
        for error in errors:
            typer.echo(f"[FAIL] {error}")
        raise typer.Exit(code=1)
    typer.echo(render_handoff_prompt(data))


@handoff_app.command("refresh")
def refresh(
    path: Annotated[str, typer.Argument()] = ".agentic/handoff_state.yaml",
    write: bool = typer.Option(False, "--write", help="Write refreshed safe_state to YAML."),
) -> None:
    data = load_handoff_state(path)
    git_state = current_git_safe_state()
    refreshed = refresh_handoff_safe_state(
        data,
        git_state["commit"],
        git_state["commit_subject"],
    )
    errors = validate_handoff_state(refreshed)
    if errors:
        for error in errors:
            typer.echo(f"[FAIL] {error}")
        raise typer.Exit(code=1)
    current = data.get("safe_state", {})
    updated = refreshed.get("safe_state", {})
    typer.echo(f"Current safe_state: {current.get('commit')} {current.get('commit_subject')}")
    typer.echo(f"Refreshed safe_state: {updated.get('commit')} {updated.get('commit_subject')}")
    if write:
        save_handoff_state(refreshed, path)
        typer.echo(f"Updated {path}")
    else:
        typer.echo("Dry run only. Use --write to update the YAML file.")
