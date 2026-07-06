from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from agentic_project_kit.workspace_adopt import (
    analyze_workspace_adoption,
    render_workspace_adopt_report,
)

workspace_app = typer.Typer(help="Inspect and manage operating-layer workspaces.")


@workspace_app.command("adopt")
def workspace_adopt_command(
    root: Annotated[Path, typer.Option("--root", help="Target repository root.")] = Path("."),
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Analyze an existing repository without writing workspace files."""

    report = analyze_workspace_adoption(root.resolve())
    if json_output:
        typer.echo(json.dumps(report.as_json_data(), indent=2, sort_keys=True))
    else:
        typer.echo(render_workspace_adopt_report(report), nl=False)
