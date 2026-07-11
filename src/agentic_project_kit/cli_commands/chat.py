from __future__ import annotations

import typer

from agentic_project_kit.chat_entrypoint_contract import (
    render_chat_refresher,
    render_chat_session_start,
)

chat_app = typer.Typer(help="Render command-manifest-aware chat entrypoints.")


@chat_app.command("refresher")
def chat_refresher_command(
    mode: str = typer.Option("copy-paste", "--mode", help="copy-paste, remote, or file-transfer."),
) -> None:
    """Render the compact six-line command manifest refresher."""
    try:
        typer.echo(render_chat_refresher(mode), nl=False)
    except ValueError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(2) from exc


@chat_app.command("session-start")
def chat_session_start_command(
    mode: str = typer.Option("copy-paste", "--mode", help="copy-paste, remote, or file-transfer."),
) -> None:
    """Render the session-start refresher and full inline command list."""
    try:
        typer.echo(render_chat_session_start(mode), nl=False)
    except ValueError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(2) from exc
