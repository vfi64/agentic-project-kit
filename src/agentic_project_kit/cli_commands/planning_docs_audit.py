from __future__ import annotations

import json
from pathlib import Path

import typer

from agentic_project_kit.planning_docs_consolidation_audit import (
    audit_planning_docs_consolidation,
    render_planning_docs_consolidation_audit,
)


def audit_planning_docs_consolidation_command(
    root: Path = typer.Option(Path("."), "--root"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Audit planning and handoff docs for consolidation candidates."""
    result = audit_planning_docs_consolidation(root.resolve())
    if json_output:
        typer.echo(json.dumps(result.as_dict(), indent=2, sort_keys=True))
    else:
        typer.echo(render_planning_docs_consolidation_audit(result), nl=False)
    if not result.ok:
        raise typer.Exit(code=result.returncode)
