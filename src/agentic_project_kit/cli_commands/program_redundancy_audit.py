from __future__ import annotations

import json
from pathlib import Path

import typer

from agentic_project_kit.program_redundancy_audit import (
    audit_program_redundancy,
    render_program_redundancy_audit,
)


def audit_program_redundancy_command(
    root: Path = typer.Option(Path("."), "--root"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Audit source for risky bug/redundancy patterns."""
    result = audit_program_redundancy(root.resolve())
    if json_output:
        typer.echo(json.dumps(result.as_dict(), indent=2, sort_keys=True))
    else:
        typer.echo(render_program_redundancy_audit(result), nl=False)
    if not result.ok:
        raise typer.Exit(code=result.returncode)
