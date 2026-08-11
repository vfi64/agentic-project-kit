from __future__ import annotations

import typer

from agentic_project_kit import __version__


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"agentic-kit {__version__}")
        raise typer.Exit()


def _main_callback(
    version: bool = typer.Option(
        False,
        "--version",
        help="Show the installed agentic-kit version and exit.",
        callback=_version_callback,
        is_eager=True,
    ),
) -> None:
    """Generate and check agentic GitHub project skeletons."""


def register_version_callback(app: typer.Typer) -> None:
    app.callback()(_main_callback)
