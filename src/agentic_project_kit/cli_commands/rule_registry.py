from __future__ import annotations

import typer

from agentic_project_kit.rule_registry_validator import (
    render_rule_registry_findings,
    validate_rule_registry,
)

rule_registry_app = typer.Typer(help="Validate governed rule registry artifacts.")


@rule_registry_app.command("check")
def rule_registry_check() -> None:
    findings = validate_rule_registry()
    typer.echo(render_rule_registry_findings(findings))
    if findings:
        raise typer.Exit(1)
