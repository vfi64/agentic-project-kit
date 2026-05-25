from __future__ import annotations

import typer

from agentic_project_kit.chat_bootloader import check_boot_sources
from agentic_project_kit.chat_bootloader import render_boot_report
from agentic_project_kit.chat_bootloader import render_bootloader
from agentic_project_kit.chat_bootloader import write_boot_report
from agentic_project_kit.chat_bootloader import write_next_chat_bootstrap

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


@boot_app.command("write")
def write(
    path: str = "docs/handoff/NEXT_CHAT_BOOTSTRAP.md",
    root: str = ".",
    include_state: bool = False,
) -> None:
    output_path = write_next_chat_bootstrap(path, root, include_state=include_state)
    typer.echo(f"WROTE {output_path}")


@boot_app.command("report")
def report(root: str = ".", path: str = "") -> None:
    if path:
        output_path = write_boot_report(path, root)
        typer.echo(f"WROTE {output_path}")
    else:
        typer.echo(render_boot_report(root))
