from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from agentic_project_kit.rule_registry_registration import (
    register_rule_registry_entry,
)
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


@rule_registry_app.command("register")
def rule_registry_register(
    mechanism_id: Annotated[str, typer.Option("--id", help="Unique rule mechanism id.")],
    rule_class: Annotated[
        str,
        typer.Option("--class", help="Rule mechanism class/category."),
    ],
    owner: Annotated[str, typer.Option("--owner", help="Responsible owner.")],
    priority: Annotated[int, typer.Option("--priority", help="Positive enforcement priority.")],
    enforcement_phase: Annotated[
        str,
        typer.Option("--enforcement-phase", help="Allowed enforcement phase."),
    ],
    conflict_domains: Annotated[
        list[str],
        typer.Option("--conflict-domain", help="Conflict domain; repeat for multiple domains."),
    ],
    surfaces: Annotated[
        list[str],
        typer.Option("--surface", help="Covered rule surface; repeat for multiple surfaces."),
    ],
    source_path: Annotated[str, typer.Option("--source", help="Repository-relative source path.")],
    required_terms: Annotated[
        list[str],
        typer.Option("--required-term", help="Required source anchor term; repeat for multiple terms."),
    ],
    test_paths: Annotated[
        list[str],
        typer.Option("--test", help="Direct regression test path; repeat for multiple tests."),
    ],
    protected_rule_intent: Annotated[
        str,
        typer.Option("--protected-rule-intent", help="Protected intent preserved by this rule."),
    ],
    assertion_statement: Annotated[
        str,
        typer.Option("--assertion-statement", help="Direct coverage assertion statement."),
    ],
    assertion_kind: Annotated[
        str,
        typer.Option("--assertion-kind", help="Coverage assertion kind."),
    ] = "guard",
    project_root: Annotated[Path, typer.Option("--root", help="Project root.")] = Path("."),
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Add one reviewed rule mechanism with direct evidence coverage."""
    result = register_rule_registry_entry(
        project_root.resolve(),
        mechanism_id=mechanism_id,
        rule_class=rule_class,
        owner=owner,
        priority=priority,
        enforcement_phase=enforcement_phase,
        conflict_domains=conflict_domains,
        surfaces=surfaces,
        source_path=source_path,
        required_terms=required_terms,
        test_paths=test_paths,
        protected_rule_intent=protected_rule_intent,
        assertion_statement=assertion_statement,
        assertion_kind=assertion_kind,
    )
    if json_output:
        typer.echo(json.dumps(result, indent=2, sort_keys=True))
    else:
        typer.echo("RULE_REGISTRY_REGISTER")
        typer.echo(f"STATUS={result['result_status']}")
        typer.echo(f"CODE={result['code']}")
        typer.echo(f"ID={result['id']}")
        typer.echo(f"CLASS={result['class']}")
        typer.echo(f"WRITTEN={result['written']}")
        typer.echo(f"GATE_RELEVANT={result['gate_relevant']}")
        note = result.get("gate_participation_note")
        if note:
            typer.echo(f"NOTE={note}")
    if result.get("result_status") != "PASS":
        raise typer.Exit(code=1)
