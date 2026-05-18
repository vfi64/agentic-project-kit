from __future__ import annotations

import typer

from agentic_project_kit.handoff_prompt import render_handoff_prompt
from agentic_project_kit.handoff_state import load_handoff_state, summarize_handoff_state, validate_handoff_state

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
