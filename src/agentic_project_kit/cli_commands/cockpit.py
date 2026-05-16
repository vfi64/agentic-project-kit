from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from agentic_project_kit.cockpit import (
    action_inventory_as_json_data,
    build_cockpit_status,
    cockpit_actions,
    render_action_inventory,
    render_cockpit_status,
    run_cockpit_action,
)


cockpit_app = typer.Typer(help="Inspect local cockpit status and structured project actions.")
console = Console()


@cockpit_app.command("status")
def cockpit_status_command(project_root: Annotated[Path, typer.Option("--root")] = Path(".")) -> None:
    status = build_cockpit_status(project_root.resolve())
    console.print(render_cockpit_status(status), markup=False)


@cockpit_app.command("actions")
def cockpit_actions_command(
    json_output: Annotated[
        bool,
        typer.Option("--json", help="Print machine-readable JSON action inventory."),
    ] = False,
) -> None:
    actions = cockpit_actions()
    if json_output:
        typer.echo(json.dumps(action_inventory_as_json_data(actions), indent=2, sort_keys=True))
        return
    console.print(render_action_inventory(actions), markup=False)


@cockpit_app.command("run")
def cockpit_run_command(
    action_id: str,
    project_root: Annotated[Path, typer.Option("--root")] = Path("."),
    allow_bounded: Annotated[bool, typer.Option("--allow-bounded")] = False,
) -> None:
    result = run_cockpit_action(action_id, project_root.resolve(), allow_bounded=allow_bounded)
    console.print(f"action_id={result.action_id}", markup=False)
    console.print(f"allowed={str(result.allowed).lower()}", markup=False)
    console.print(f"executed={str(result.executed).lower()}", markup=False)
    if result.returncode is not None:
        console.print(f"returncode={result.returncode}", markup=False)
    console.print(result.message, markup=False)
    if result.stdout:
        console.print(result.stdout, markup=False)
    if result.stderr:
        console.print(result.stderr, markup=False)
    if not result.allowed:
        raise typer.Exit(code=2)
    if result.returncode not in (None, 0):
        raise typer.Exit(code=result.returncode)
