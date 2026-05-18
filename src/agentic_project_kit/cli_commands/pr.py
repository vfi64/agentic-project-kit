from __future__ import annotations

import json
from pathlib import Path

import typer

from agentic_project_kit.pr_closeout import BLOCKED, evaluate_pr_closeout, render_pr_closeout

pr_app = typer.Typer(help="Evaluate deterministic PR closeout state.")

@pr_app.command("closeout-check")
def closeout_check(json_file: Path) -> None:
    data = json.loads(json_file.read_text(encoding="utf-8"))
    result = evaluate_pr_closeout(data)
    typer.echo(render_pr_closeout(result))
    if result.outcome == BLOCKED:
        raise typer.Exit(code=1)
