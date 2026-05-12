from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.prompt import Confirm

from agentic_project_kit.github import create_github_repo

console = Console()


def register_github_commands(app: typer.Typer) -> None:
    app.command("github-create")(github_create_command)


def github_create_command(
    project_root: Path = typer.Option(Path("."), "--root"),
    owner: str | None = typer.Option(None, "--owner"),
    visibility: str = typer.Option("private", "--visibility"),
) -> None:
    if visibility not in {"private", "public"}:
        raise typer.BadParameter("visibility must be private or public")
    if visibility == "public":
        console.print("[bold yellow]Public repository selected. Check for secrets before continuing.[/bold yellow]")
        if not Confirm.ask("Continue?", default=False):
            raise typer.Exit(code=1)

    create_github_repo(project_root.resolve(), owner=owner, visibility=visibility, push=True)
    console.print("[green]GitHub repository created and pushed.[/green]")
