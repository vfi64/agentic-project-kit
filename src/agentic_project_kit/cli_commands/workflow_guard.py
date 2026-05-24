from __future__ import annotations

from typing import Optional

import typer

from agentic_project_kit.workflow_guard import render_findings, run_workflow_guard

workflow_guard_app = typer.Typer(help="Diagnose recurring workflow failure patterns before mutation.")


@workflow_guard_app.command("check")
def workflow_guard_check(paths: Optional[list[str]] = typer.Argument(None)) -> None:
    findings = run_workflow_guard(paths or [])
    typer.echo(render_findings(findings))
    if findings:
        raise typer.Exit(1)


@workflow_guard_app.command("diagnose")
def workflow_guard_diagnose(paths: Optional[list[str]] = typer.Argument(None)) -> None:
    findings = run_workflow_guard(paths or [])
    typer.echo(render_findings(findings))
    if findings:
        typer.echo("Repair mode: produce a repair plan first; only narrow safe repairs may be automated.")
        raise typer.Exit(1)
