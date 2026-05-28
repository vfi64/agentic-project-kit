from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from agentic_project_kit import slice_gate

slice_app = typer.Typer(help="Run temporary slice-specific governance gates.")


@slice_app.command("gate")
def gate_command(
    kind: Annotated[str, typer.Option("--kind", help="Slice gate kind to run.")] = "planning-doc",
    project_root: Annotated[Path, typer.Option("--root", help="Repository root.")] = Path("."),
) -> None:
    report = slice_gate.run_slice_gate(kind, project_root=project_root)
    typer.echo(slice_gate.render_slice_gate_report(report), nl=False)
    if report.exit_code:
        raise typer.Exit(code=report.exit_code)
