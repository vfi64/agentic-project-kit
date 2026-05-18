from __future__ import annotations

import typer

from agentic_project_kit.action_specs import built_in_action_specs, get_action_spec, render_action_spec

actions_app = typer.Typer(help="Inspect parameterized action specifications.")

@actions_app.command("list")
def list_actions() -> None:
    for spec in built_in_action_specs().values():
        typer.echo(f"{spec.action_id}\t{spec.safety_class.value}\t{spec.title}")

@actions_app.command("show")
def show_action(action_id: str) -> None:
    try:
        spec = get_action_spec(action_id)
    except KeyError as exc:
        typer.echo(str(exc))
        raise typer.Exit(code=1) from exc
    typer.echo(render_action_spec(spec))
