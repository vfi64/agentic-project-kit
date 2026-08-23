from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from agentic_project_kit.onboarding_measurement import (
    build_onboarding_measurement,
    onboarding_measurement_json,
    render_onboarding_measurement,
)

onboarding_app = typer.Typer(help="Measure first-chat onboarding guidance.")


@onboarding_app.command("measure")
def onboarding_measure_command(
    project_root: Annotated[Path, typer.Option("--root", help="Repository root.")] = Path("."),
    json_output: Annotated[bool, typer.Option("--json", help="Print machine-readable JSON.")] = False,
) -> None:
    """Measure onboarding guidance against the command manifest and workspace detection."""
    measurement = build_onboarding_measurement(project_root.resolve())
    if json_output:
        typer.echo(onboarding_measurement_json(measurement), nl=False)
    else:
        typer.echo(render_onboarding_measurement(measurement), nl=False)
    if not measurement.ok:
        raise typer.Exit(code=measurement.returncode)
