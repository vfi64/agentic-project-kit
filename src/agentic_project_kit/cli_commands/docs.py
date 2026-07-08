from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from agentic_project_kit.removed_source_audit import (
    DEFAULT_CENTRAL_TARGET,
    build_removed_source_audit,
    render_removed_source_audit,
)

docs_app = typer.Typer(help="Documentation maintenance and migration guards.")


@docs_app.command("removed-source-audit")
def removed_source_audit_command(
    root: Annotated[Path, typer.Option("--root", help="Repository root.")] = Path("."),
    path: Annotated[
        list[str] | None,
        typer.Option(
            "--path",
            help=(
                "Repository-relative removed source path to audit. "
                "May be supplied multiple times. Defaults to removed_source paths in PROJECT_DIRECTION.yaml."
            ),
        ),
    ] = None,
    central_target: Annotated[
        str,
        typer.Option("--central-target", help="Repository-relative central document that may retain removed_source metadata."),
    ] = DEFAULT_CENTRAL_TARGET,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Fail if removed documentation sources still have live refs or registry refs."""
    result = build_removed_source_audit(
        root.resolve(),
        paths=path,
        central_target=central_target,
    )
    if json_output:
        typer.echo(json.dumps(result.as_dict(), indent=2, sort_keys=True))
    else:
        typer.echo(render_removed_source_audit(result), nl=False)
    if not result.ok:
        raise typer.Exit(code=result.returncode)
