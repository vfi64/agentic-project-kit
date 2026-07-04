from __future__ import annotations

import json
from pathlib import Path

import typer

from agentic_project_kit.path_literal_audit import (
    audit_path_literals,
    render_path_literal_audit,
)


def audit_path_literals_command(
    root: Path = typer.Option(Path("."), "--root", help="Project root."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    """Report hardcoded docs/tmp path literals in source modules."""
    result = audit_path_literals(root.resolve())
    if json_output:
        typer.echo(json.dumps(result.as_dict(), indent=2, sort_keys=True))
    else:
        typer.echo(render_path_literal_audit(result), nl=False)
