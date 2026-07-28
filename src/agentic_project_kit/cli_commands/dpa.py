from __future__ import annotations

import json
from pathlib import Path

import typer

from agentic_project_kit.dpa_readiness import (
    DEFAULT_READINESS_PATH,
    evaluate_dpa_readiness,
    render_dpa_readiness_result,
)

dpa_app = typer.Typer(help="Inspect Document Projection Architecture readiness state.")


@dpa_app.command("readiness")
def dpa_readiness_command(
    root: Path = typer.Option(Path("."), "--root", help="Repository root."),
    record: Path = typer.Option(
        DEFAULT_READINESS_PATH,
        "--record",
        help="DPA Assessment readiness JSON record to inspect.",
    ),
    output_json: bool = typer.Option(False, "--json", help="Print machine-readable JSON."),
    require_dp2_ready: bool = typer.Option(
        False,
        "--require-dp2-ready",
        help="Fail unless the readiness record structurally authorizes DP2.",
    ),
) -> None:
    """Validate the DPA DP1 Assessment readiness record without mutating files."""
    result = evaluate_dpa_readiness(root, readiness_path=record)
    if output_json:
        typer.echo(json.dumps(result.as_dict(), indent=2))
    else:
        typer.echo(render_dpa_readiness_result(result), nl=False)
    if result.findings or (require_dp2_ready and not result.dp2_ready):
        raise typer.Exit(1)
