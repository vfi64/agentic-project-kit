from __future__ import annotations

import json
from pathlib import Path

import typer

from agentic_project_kit.command_taxonomy import (
    build_command_taxonomy_report,
    render_command_taxonomy_report,
)


def command_taxonomy_check_command(
    root: Path = typer.Option(Path("."), "--root"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Check that public commands have stable GUI-usable taxonomy."""
    report = build_command_taxonomy_report(root.resolve())
    if json_output:
        typer.echo(json.dumps(report.as_dict(), indent=2, sort_keys=True))
    else:
        typer.echo(render_command_taxonomy_report(report), nl=False)
    if not report.ok:
        raise typer.Exit(code=1)
