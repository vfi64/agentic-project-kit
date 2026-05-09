from pathlib import Path
import subprocess

import typer
from rich.console import Console
from rich.prompt import Confirm, Prompt

from agentic_project_kit.checks import check_all, check_docs, check_todo
from agentic_project_kit.github import create_github_repo
from agentic_project_kit.models import ProjectOptions
from agentic_project_kit.templates import create_project

app = typer.Typer(help="Generate and check agentic GitHub project skeletons.")
console = Console()


@app.command()
def init(
    name: str | None = typer.Argument(None, help="Project directory/name."),
    project_type: str = typer.Option("python-cli", "--type", help="python-cli, python-lib, generic"),
    description: str | None = typer.Option(None, "--description"),
    license_name: str = typer.Option("MIT", "--license"),
    github_actions: bool = typer.Option(True, "--github-actions/--no-github-actions"),
    pre_commit: bool = typer.Option(True, "--pre-commit/--no-pre-commit"),
    agent_docs: bool = typer.Option(True, "--agent-docs/--no-agent-docs"),
    logging_evidence: bool = typer.Option(True, "--logging-evidence/--no-logging-evidence"),
    github: bool = typer.Option(False, "--github/--no-github"),
    github_owner: str | None = typer.Option(None, "--owner"),
    visibility: str = typer.Option("private", "--visibility", help="private or public"),
) -> None:
    if name is None:
        name = Prompt.ask("Project name")
    if description is None:
        description = Prompt.ask("Project description", default=f"{name} project")
    if project_type not in {"python-cli", "python-lib", "generic"}:
        raise typer.BadParameter("project type must be python-cli, python-lib, or generic")
    if visibility not in {"private", "public"}:
        raise typer.BadParameter("visibility must be private or public")

    target = Path(name).resolve()
    options = ProjectOptions(
        name=name,
        description=description,
        project_type=project_type,
        license_name=license_name,
        github_actions=github_actions,
        pre_commit=pre_commit,
        agent_docs=agent_docs,
        logging_evidence=logging_evidence,
        target_dir=target,
    )

    create_project(options)
    console.print(f"[green]Created project:[/green] {target}")

    subprocess.run(["git", "add", "."], cwd=target, check=False)
    subprocess.run(["git", "commit", "-m", "Initialize agentic project"], cwd=target, check=False)

    if github:
        if visibility == "public":
            console.print("[bold yellow]Public repository selected. Check for secrets before continuing.[/bold yellow]")
            if not Confirm.ask("Continue with public GitHub repository creation?", default=False):
                raise typer.Exit(code=1)
        create_github_repo(target, owner=github_owner, visibility=visibility, push=True)
        console.print("[green]GitHub repository created and pushed.[/green]")

    console.print("Next:")
    console.print(f"  cd {target}")
    console.print("  python -m venv .venv")
    console.print("  source .venv/bin/activate")
    console.print('  pip install -e ".[dev]"')
    console.print("  pytest -q")
    console.print("  agentic-kit check")


@app.command("check")
def check_command(project_root: Path = typer.Option(Path("."), "--root")) -> None:
    errors = check_all(project_root.resolve())
    _print_result(errors)


@app.command("check-docs")
def check_docs_command(project_root: Path = typer.Option(Path("."), "--root")) -> None:
    errors = check_docs(project_root.resolve())
    _print_result(errors)


@app.command("check-todo")
def check_todo_command(project_root: Path = typer.Option(Path("."), "--root")) -> None:
    errors = check_todo(project_root.resolve())
    _print_result(errors)


@app.command("github-create")
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


def _print_result(errors: list[str]) -> None:
    if errors:
        console.print("[bold red]Agentic project check failed[/bold red]")
        for error in errors:
            console.print(f"[red]- {error}[/red]")
        raise typer.Exit(code=1)
    console.print("[bold green]Agentic project check passed[/bold green]")


if __name__ == "__main__":
    app()
