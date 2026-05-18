from __future__ import annotations

import typer

from agentic_project_kit.state_freshness import find_stale_state_fragments, format_findings

state_app = typer.Typer(help="Check repository state freshness.")


@state_app.command("freshness-check")
def freshness_check() -> None:
    findings = find_stale_state_fragments()
    typer.echo(format_findings(findings))
    if findings:
        raise typer.Exit(1)
