from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from agentic_project_kit.cockpit import build_cockpit_status, cockpit_actions, render_action_inventory, render_cockpit_status


cockpit_app = typer.Typer(help="Inspect local cockpit status and structured project actions.")
console = Console()


@cockpit_app.command("status")
def cockpit_status_command(project_root: Annotated[Path, typer.Option("--root")] = Path(".")) -> None:
    status = build_cockpit_status(project_root.resolve())
    console.print(render_cockpit_status(status), markup=False)


@cockpit_app.command("actions")
def cockpit_actions_command() -> None:
    console.print(render_action_inventory(cockpit_actions()), markup=False)
