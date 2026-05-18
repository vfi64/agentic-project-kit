from __future__ import annotations

import typer

from agentic_project_kit.governance import governance_check, render_governance_check

governance_app = typer.Typer(help="Run deterministic project governance checks.")

@governance_app.command("check")
def check_command() -> None:
    errors = governance_check()
    typer.echo(render_governance_check(errors))
    if errors:
        raise typer.Exit(code=1)
