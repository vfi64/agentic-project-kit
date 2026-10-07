from __future__ import annotations

import json
from pathlib import Path

import typer

from agentic_project_kit.cli_commands.transfer_shared import transfer_app
from agentic_project_kit.pr_superseded_close import close_superseded_pr
from agentic_project_kit.repo_identity import bind_github_cli_env_for_origin


@transfer_app.command("pr-close-superseded")
def pr_close_superseded_command(
    pr_number: int = typer.Argument(...),
    replacement_pr: int = typer.Option(..., "--replacement-pr"),
    expected_head_sha: str = typer.Option(..., "--expected-head-sha"),
    execute: bool = typer.Option(False, "--execute"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Close an unchanged superseded PR after a replacement merged into the same base."""
    root = Path(".").resolve()
    bind_github_cli_env_for_origin(root)
    result = close_superseded_pr(root, pr_number=pr_number, replacement_pr=replacement_pr, expected_head_sha=expected_head_sha, execute=execute)
    typer.echo(json.dumps(result, indent=2) if json_output else f"PR_CLOSE_SUPERSEDED: {result['result_status']}")
    if result["result_status"] == "BLOCKED":
        raise typer.Exit(2)
