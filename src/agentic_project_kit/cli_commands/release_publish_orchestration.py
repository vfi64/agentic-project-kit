from __future__ import annotations

import json
from pathlib import Path

import typer

from agentic_project_kit import __version__ as PACKAGE_VERSION
from agentic_project_kit.release_publish_orchestration import (
    evaluate_release_publish_plan,
    render_release_publish_plan,
)


def release_publish_command(
    version: str = typer.Option(PACKAGE_VERSION, "--version"),
    dry_run: bool = typer.Option(True, "--dry-run/--no-dry-run"),
    execute: bool = typer.Option(False, "--execute"),
    root: Path = typer.Option(Path("."), "--root"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Plan release publishing without live tag/release side effects."""
    plan = evaluate_release_publish_plan(
        root.resolve(),
        version=version,
        dry_run=dry_run,
        execute=execute,
    )
    if json_output:
        typer.echo(json.dumps(plan.as_dict(), indent=2, sort_keys=True))
    else:
        typer.echo(render_release_publish_plan(plan), nl=False)
    if not plan.ok:
        raise typer.Exit(code=plan.returncode)
