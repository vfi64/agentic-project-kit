from __future__ import annotations

import json
from pathlib import Path

import typer

from agentic_project_kit.status_current_state_audit import (
    audit_status_current_state,
    render_status_current_state_audit,
)


def audit_status_current_state_command(
    root: Path = typer.Option(Path("."), "--root"),
    max_origin_lag: int = typer.Option(
        3,
        "--max-origin-lag",
        help="Maximum commits the validated substantive safe-state may trail origin/main.",
    ),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Audit STATUS.md current-state claims against handoff, release, and origin/main state."""
    result = audit_status_current_state(root.resolve(), max_origin_lag=max_origin_lag)
    if json_output:
        typer.echo(json.dumps(result.as_dict(), indent=2, sort_keys=True))
    else:
        typer.echo(render_status_current_state_audit(result), nl=False)
    if not result.ok:
        raise typer.Exit(code=result.returncode)
