from __future__ import annotations

from pathlib import Path

import typer

from agentic_project_kit.pass_already_done import classify_file
from agentic_project_kit.pass_already_done import render_classification

app = typer.Typer(help="Classify idempotent already-done command outcomes.")


@app.command("classify")
def classify(
    path: Path,
    exit_code: int = typer.Option(..., "--exit-code"),
    target_verified: bool = typer.Option(False, "--target-verified"),
) -> None:
    classification = classify_file(path, exit_code=exit_code, target_verified=target_verified)
    typer.echo(render_classification(classification))
    if not classification.success:
        raise typer.Exit(code=1)
