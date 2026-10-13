from __future__ import annotations

import json
from pathlib import Path

import typer

from agentic_project_kit.ci_status import read_ci_status, render_ci_status, result_to_dict

ci_app = typer.Typer(help="Read GitHub Actions CI status for branches and commits.")


@ci_app.command("runtime-plan")
def runtime_plan_command(
    base: str = typer.Option(..., "--base"),
    head: str = typer.Option(..., "--head"),
    branch: str = typer.Option("", "--branch"),
    event_name: str = typer.Option("", "--event-name"),
    root: Path = typer.Option(Path("."), "--root"),
    json_output: bool = typer.Option(False, "--json"),
):
    """Classify a custom CI diff; unknown input always requests full tests."""
    from agentic_project_kit.ci_runtime_plan import runtime_plan

    result = runtime_plan(root, base, head, branch=branch, event_name=event_name)
    typer.echo(
        json.dumps(result, indent=2, sort_keys=True)
        if json_output
        else result["mode"] + ": " + result["reason"]
    )


@ci_app.command("status")
def status(
    commit: str = typer.Option("", "--commit", help="Commit SHA to inspect."),
    branch: str = typer.Option("", "--branch", help="Branch name to inspect."),
    limit: int = typer.Option(20, min=1, help="Maximum workflow runs to read."),
    json_output: bool = typer.Option(
        False, "--json", help="Print JSON instead of the text report."
    ),
) -> None:
    """Report the CI verdict for a commit or branch without requiring a pull request."""
    try:
        result = read_ci_status(commit=commit, branch=branch, limit=limit)
    except (RuntimeError, ValueError) as exc:
        payload = {
            "schema_version": 1,
            "kind": "ci_status",
            "result_status": "BLOCKED",
            "decision": "unknown",
            "commit": commit,
            "branch": branch,
            "error": str(exc),
            "next_action": "fix the CI status query and rerun the command",
        }
        if json_output:
            typer.echo(json.dumps(payload, indent=2, sort_keys=True))
        else:
            typer.echo(f"CI_STATUS\nresult_status=BLOCKED\ndecision=unknown\nerror={exc}\n")
        raise typer.Exit(code=2)
    if json_output:
        typer.echo(json.dumps(result_to_dict(result), indent=2, sort_keys=True))
    else:
        typer.echo(render_ci_status(result))
