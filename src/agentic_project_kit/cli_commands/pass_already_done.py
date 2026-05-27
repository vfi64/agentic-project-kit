from __future__ import annotations

from pathlib import Path

import typer

from agentic_project_kit.pass_already_done import classify_file
from agentic_project_kit.pass_already_done import render_classification
from agentic_project_kit.pass_already_done import render_classification_json
from agentic_project_kit.pass_already_done import SUPPORTED_TARGET_STATES
from agentic_project_kit.result_report_classifier import classify_report
from agentic_project_kit.result_report_classifier import render_report_classification

app = typer.Typer(help="Classify idempotent already-done command outcomes.")


@app.command("classify")
def classify(
    path: Path,
    exit_code: int = typer.Option(..., "--exit-code"),
    target_verified: bool = typer.Option(False, "--target-verified"),
    target_state: str | None = typer.Option(
        None,
        "--target-state",
        help="Already-done target class. One of: " + ", ".join(sorted(SUPPORTED_TARGET_STATES)),
    ),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON output."),
) -> None:
    classification = classify_file(
        path,
        exit_code=exit_code,
        target_verified=target_verified,
        target_state=target_state,
    )
    if json_output:
        typer.echo(render_classification_json(classification))
    else:
        typer.echo(render_classification(classification))
    if not classification.success:
        raise typer.Exit(code=1)


@app.command("report")
def report(
    path: Path,
    exit_code: int = typer.Option(..., "--exit-code"),
    target_verified: bool = typer.Option(False, "--target-verified"),
    target_state: str | None = typer.Option(
        None,
        "--target-state",
        help="Already-done target class. One of: " + ", ".join(sorted(SUPPORTED_TARGET_STATES)),
    ),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON output."),
) -> None:
    result = classify_report(
        path,
        raw_exit_code=exit_code,
        target_verified=target_verified,
        target_state=target_state,
    )
    if json_output:
        typer.echo(render_classification_json(result.classification))
    else:
        typer.echo(render_report_classification(result))
    if not result.success:
        raise typer.Exit(code=1)
