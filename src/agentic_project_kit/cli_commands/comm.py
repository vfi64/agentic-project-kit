from __future__ import annotations

from pathlib import Path

import typer

from agentic_project_kit.comm_signal import inspect_comm_signal
from agentic_project_kit.comm_signal import render_comm_signal_inspection

comm_app = typer.Typer(help="Inspect short chat communication signals against the communication contract.")


@comm_app.command("inspect")
def inspect(signal: str, evidence: Path | None = typer.Option(None, "--evidence")) -> None:
    result = inspect_comm_signal(signal, evidence_path=evidence)
    typer.echo(render_comm_signal_inspection(result))
    if not result.success:
        raise typer.Exit(code=1)
