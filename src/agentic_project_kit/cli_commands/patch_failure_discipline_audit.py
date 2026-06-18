from __future__ import annotations

import json
from pathlib import Path

import typer

from agentic_project_kit.patch_failure_discipline_audit import (
    audit_patch_failure_discipline,
    render_patch_failure_discipline,
)


def audit_patch_failure_discipline_command(
    root: Path = typer.Option(Path("."), "--root"),
    include_tmp: bool = typer.Option(False, "--include-tmp"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Audit whether repeated patch failures were followed by diagnosis evidence."""
    result = audit_patch_failure_discipline(root.resolve(), include_tmp=include_tmp)
    if json_output:
        typer.echo(json.dumps(result.as_dict(), indent=2, sort_keys=True))
    else:
        typer.echo(render_patch_failure_discipline(result), nl=False)
    if not result.ok:
        raise typer.Exit(code=result.returncode)
