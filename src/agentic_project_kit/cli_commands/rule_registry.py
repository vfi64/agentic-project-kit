from __future__ import annotations

import json

import typer

from agentic_project_kit.rule_registry_report import (
    build_rule_registry_report,
    render_rule_registry_report,
)
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


@rule_registry_app.command("report")
def rule_registry_report(
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
    fail_on_followups: bool = typer.Option(
        False,
        "--fail-on-followups",
        help="Exit non-zero when follow-up items remain, even if validation passes.",
    ),
) -> None:
    report = build_rule_registry_report()
    if json_output:
        typer.echo(json.dumps(report, indent=2, sort_keys=True))
    else:
        typer.echo(render_rule_registry_report(report))
    summary = report.get("summary", {}) if isinstance(report.get("summary"), dict) else {}
    if summary.get("validation_finding_count", 0):
        raise typer.Exit(1)
    if fail_on_followups and summary.get("followup_count", 0):
        raise typer.Exit(1)
