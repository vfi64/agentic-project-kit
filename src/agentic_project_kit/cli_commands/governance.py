from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from agentic_project_kit.governance import governance_check, render_governance_check

governance_app = typer.Typer(help="Run deterministic project governance checks.")

@governance_app.command("check")
def check_command(
    project_root: Annotated[Path, typer.Option("--root", help="Repository root.")] = Path("."),
) -> None:
    errors = governance_check(project_root.resolve())
    typer.echo(render_governance_check(errors))
    if errors:
        raise typer.Exit(code=1)
