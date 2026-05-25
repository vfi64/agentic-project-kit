from __future__ import annotations

import typer

from agentic_project_kit.chat_bootloader import check_boot_sources, render_bootloader

boot_app = typer.Typer(help="Render and check successor-chat boot information.")


@boot_app.command("prompt")
def prompt(root: str = ".") -> None:
    typer.echo(render_bootloader(root))


@boot_app.command("check")
def check(root: str = ".") -> None:
    typer.echo(render_bootloader(root))
    missing = [item.source for item in check_boot_sources(root) if not item.exists]
    if missing:
        raise typer.Exit(code=1)
