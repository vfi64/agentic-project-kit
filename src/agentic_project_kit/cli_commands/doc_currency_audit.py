from __future__ import annotations

import json
from pathlib import Path

import typer

from agentic_project_kit.doc_currency_audit import (
    audit_doc_currency,
    render_doc_currency_audit,
)


def audit_doc_currency_command(
    root: Path = typer.Option(Path("."), "--root"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Audit current release/documentation currency across handoff and release docs."""
    result = audit_doc_currency(root.resolve())
    if json_output:
        typer.echo(json.dumps(result.as_dict(), indent=2, sort_keys=True))
    else:
        typer.echo(render_doc_currency_audit(result), nl=False)
    if not result.ok:
        raise typer.Exit(code=result.returncode)
