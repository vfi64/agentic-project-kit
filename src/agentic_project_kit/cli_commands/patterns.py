from __future__ import annotations

from pathlib import Path

import typer

from agentic_project_kit.patterns import (
    PatternCatalogError,
    find_pattern,
    load_pattern_catalog,
    load_pattern_detail,
)

patterns_app = typer.Typer(help="Inspect the local read-only pattern catalog.")


@patterns_app.command("list")
def patterns_list() -> None:
    """List known local patterns and anti-patterns."""
    try:
        catalog = load_pattern_catalog(Path("."))
    except PatternCatalogError as exc:
        raise typer.BadParameter(str(exc)) from exc

    for entry in catalog.patterns:
        typer.echo(f"{entry.id}\t{entry.kind}\t{entry.title}")
        typer.echo(f"  {entry.summary}")


@patterns_app.command("show")
def patterns_show(pattern_id: str) -> None:
    """Show one local pattern catalog entry by stable ID."""
    try:
        catalog = load_pattern_catalog(Path("."))
        entry = find_pattern(catalog, pattern_id)
        detail = load_pattern_detail(Path("."), entry)
    except PatternCatalogError as exc:
        raise typer.BadParameter(str(exc)) from exc

    typer.echo(detail.markdown)
