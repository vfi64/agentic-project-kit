from __future__ import annotations

from pathlib import Path
import subprocess

import typer
from rich.console import Console
from rich.prompt import Confirm, Prompt

from agentic_project_kit.contract import (
    PROFILE_DEFINITIONS,
    POLICY_PACK_DEFINITIONS,
    default_profiles,
    recommended_policy_packs,
    validate_ids,
)
from agentic_project_kit.github import create_github_repo
from agentic_project_kit.models import ProjectOptions
from agentic_project_kit.templates import create_project

console = Console()


def register_init_command(app: typer.Typer) -> None:
    app.command("init")(init_command)


def init_command(
    name: str | None = typer.Argument(None, help="Project directory/name."),
    project_type: str = typer.Option("python-cli", "--type", help="python-cli, python-lib, generic, governance-wrapper"),
    description: str | None = typer.Option(None, "--description"),
    license_name: str = typer.Option("MIT", "--license"),
    github_actions: bool = typer.Option(True, "--github-actions/--no-github-actions"),
    pre_commit: bool = typer.Option(True, "--pre-commit/--no-pre-commit"),
    agent_docs: bool = typer.Option(True, "--agent-docs/--no-agent-docs"),
    logging_evidence: bool = typer.Option(True, "--logging-evidence/--no-logging-evidence"),
    profiles: str | None = typer.Option(
        None,
        "--profiles",
        help="Comma-separated profile ids. Defaults are recommended from project type.",
    ),
    policy_packs: str | None = typer.Option(
        None,
        "--policy-packs",
        help="Comma-separated policy pack ids. Defaults are recommended from project type.",
    ),
    github: bool = typer.Option(False, "--github/--no-github"),
    github_owner: str | None = typer.Option(None, "--owner"),
    visibility: str = typer.Option("private", "--visibility", help="private or public"),
    kit_source: str = typer.Option(
        "pypi",
        "--kit-source",
        help="agentic-kit install source for generated CI: pypi, testpypi, or none",
    ),
) -> None:
    if name is None:
        name = Prompt.ask("Project name")
    if description is None:
        description = Prompt.ask("Project description", default=f"{name} project")
    if project_type not in {"python-cli", "python-lib", "generic", "governance-wrapper"}:
        raise typer.BadParameter("project type must be python-cli, python-lib, generic, or governance-wrapper")
    if visibility not in {"private", "public"}:
        raise typer.BadParameter("visibility must be private or public")
    if kit_source not in {"pypi", "testpypi", "none"}:
        raise typer.BadParameter("kit source must be pypi, testpypi, or none")

    selected_profiles = _parse_csv(profiles) or default_profiles(
        project_type,
        github_actions=github_actions,
    )
    selected_policy_packs = _parse_csv(policy_packs) or recommended_policy_packs(
        project_type,
        github_actions=github_actions,
        logging_evidence=logging_evidence,
    )
    errors = validate_ids("profile", selected_profiles, PROFILE_DEFINITIONS)
    errors.extend(validate_ids("policy pack", selected_policy_packs, POLICY_PACK_DEFINITIONS))
    if errors:
        raise typer.BadParameter("; ".join(errors))

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
        kit_source=kit_source,
        profiles=selected_profiles,
        policy_packs=selected_policy_packs,
    )

    create_project(options)
    console.print(f"[green]Created project:[/green] {target}")
    console.print("Recommended profiles: " + ", ".join(selected_profiles))
    console.print("Recommended policy packs: " + ", ".join(selected_policy_packs))

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
    if project_type in {"python-cli", "python-lib"}:
        console.print("  python -m venv .venv")
        console.print("  source .venv/bin/activate")
        console.print('  pip install -e ".[dev]"', markup=False)
        console.print("  pytest -q")
    else:
        console.print("  agentic-kit check-docs")
    console.print("  agentic-kit check")
    console.print("  agentic-kit doctor")


def _parse_csv(value: str | None) -> tuple[str, ...]:
    if value is None:
        return ()
    return tuple(item.strip() for item in value.split(",") if item.strip())
