from __future__ import annotations

import json
from pathlib import Path

import typer

from agentic_project_kit.absolute_path_portability_audit import (
    audit_absolute_path_portability,
    render_absolute_path_portability_audit,
)


def audit_absolute_path_portability_command(
    root: Path = typer.Option(Path("."), "--root"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Audit absolute local paths that may break portability."""
    result = audit_absolute_path_portability(root.resolve())
    if json_output:
        typer.echo(json.dumps(result.as_dict(), indent=2, sort_keys=True))
    else:
        typer.echo(render_absolute_path_portability_audit(result), nl=False)
    if not result.ok:
        raise typer.Exit(code=result.returncode)
