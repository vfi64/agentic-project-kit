from __future__ import annotations

import json
from pathlib import Path

import typer

from agentic_project_kit.remote_branch_hygiene import (
    analyze_remote_branch_hygiene,
    collect_remote_branch_hygiene_inputs,
    render_remote_branch_hygiene_report,
    report_as_json_data,
)


def register_remote_branch_hygiene_command(app: typer.Typer) -> None:
    app.command("remote-branch-hygiene")(remote_branch_hygiene_command)


def remote_branch_hygiene_command(
    project_root: Path = typer.Option(Path("."), "--root"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Dry-run remote branch hygiene classification for K3."""
    remote_branches, open_pr_heads = collect_remote_branch_hygiene_inputs(project_root.resolve())
    report = analyze_remote_branch_hygiene(remote_branches, open_pr_heads)
    if json_output:
        typer.echo(json.dumps(report_as_json_data(report), indent=2, sort_keys=True))
    else:
        typer.echo(render_remote_branch_hygiene_report(report), nl=False)
