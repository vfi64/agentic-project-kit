from __future__ import annotations

import json
from pathlib import Path

import typer

from agentic_project_kit.gui_readiness_gate import (
    evaluate_gui_readiness,
    render_gui_readiness_gate,
)


def gui_readiness_gate_command(
    root: Path = typer.Option(Path("."), "--root"),
    version: str = typer.Option("0.4.9", "--version"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Run the pre-GUI readiness gate."""
    result = evaluate_gui_readiness(root.resolve(), version=version)
    if json_output:
        typer.echo(json.dumps(result.as_dict(), indent=2, sort_keys=True))
    else:
        typer.echo(render_gui_readiness_gate(result), nl=False)
    if not result.ok:
        raise typer.Exit(code=result.returncode)
