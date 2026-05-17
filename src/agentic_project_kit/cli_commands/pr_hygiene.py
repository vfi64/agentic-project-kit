from __future__ import annotations

from pathlib import Path
import json

import typer
from rich.console import Console

from agentic_project_kit.pr_hygiene import analyze_pr_hygiene, collect_pr_hygiene_inputs, render_pr_hygiene_report, report_as_json_data

console = Console()


def register_pr_hygiene_command(app: typer.Typer) -> None:
    app.command("pr-hygiene")(pr_hygiene_command)


def pr_hygiene_command(
    project_root: Path = typer.Option(Path("."), "--root"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    open_prs, local_branches = collect_pr_hygiene_inputs(project_root.resolve())
    report = analyze_pr_hygiene(open_prs, local_branches)
    if json_output:
        console.print(json.dumps(report_as_json_data(report), indent=2), markup=False)
        return
    console.print(render_pr_hygiene_report(report), markup=False)
