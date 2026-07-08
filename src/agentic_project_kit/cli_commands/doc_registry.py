from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from agentic_project_kit.documentation_registry import (
    build_doc_registry_reconcile_report,
    render_doc_registry_reconcile_report,
    build_unregistered_document_candidates_report,
    register_documentation_registry_entry,
)

doc_registry_app = typer.Typer(help="Register reviewed documentation registry entries.")


@doc_registry_app.command("register")
def doc_registry_register(
    document_path: Annotated[str, typer.Option("--path", help="Repository-relative document path.")],
    document_class: Annotated[str, typer.Option("--class", help="Allowed documentation registry class.")],
    owner: Annotated[str, typer.Option("--owner", help="Document owner recorded in the registry.")] = "maintainers",
    project_root: Annotated[Path, typer.Option("--root", help="Project root.")] = Path("."),
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Add one reviewed document entry to the documentation registry."""
    result = register_documentation_registry_entry(
        project_root.resolve(),
        document_path=document_path,
        document_class=document_class,
        owner=owner,
    )
    if json_output:
        typer.echo(json.dumps(result, indent=2, sort_keys=True))
    else:
        typer.echo("DOC_REGISTRY_REGISTER")
        typer.echo(f"STATUS={result['result_status']}")
        typer.echo(f"CODE={result['code']}")
        typer.echo(f"PATH={result['path']}")
        typer.echo(f"CLASS={result['class']}")
        typer.echo(f"WRITTEN={result['written']}")
    if result.get("result_status") != "PASS":
        raise typer.Exit(code=1)



@doc_registry_app.command("reconcile")
def doc_registry_reconcile(
    project_root: Annotated[Path, typer.Option("--root", help="Project root.")] = Path("."),
    execute: Annotated[
        bool,
        typer.Option(
            "--execute",
            help="Reserved for a later slice; current implementation is dry-run only.",
        ),
    ] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """Reconcile documentation registry, declared scope, and decision projection."""
    if execute:
        payload = {
            "schema_version": 1,
            "kind": "doc_registry_reconcile_report",
            "result_status": "BLOCK",
            "mode": "execute",
            "message": "--execute is reserved for a later K2c slice; dry-run only.",
        }
        if json_output:
            typer.echo(json.dumps(payload, indent=2, sort_keys=True))
        else:
            typer.echo("DOC_REGISTRY_RECONCILE")
            typer.echo("STATE: BLOCK")
            typer.echo("MODE: execute")
            typer.echo("MESSAGE: --execute is reserved for a later K2c slice; dry-run only.")
        raise typer.Exit(2)

    report = build_doc_registry_reconcile_report(project_root.resolve())
    if json_output:
        typer.echo(json.dumps(report, indent=2, sort_keys=True))
    else:
        typer.echo(render_doc_registry_reconcile_report(report))

    if report["result_status"] == "BLOCK":
        raise typer.Exit(2)

@doc_registry_app.command("check-unregistered")
def doc_registry_check_unregistered(
    project_root: Annotated[Path, typer.Option("--root", help="Project root.")] = Path("."),
    strict_scope: Annotated[
        bool,
        typer.Option(
            "--strict-scope",
            help="Fail when unregistered Markdown files violate declared required scope paths.",
        ),
    ] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON.")] = False,
) -> None:
    """List unregistered docs candidates with optional strict declared-scope failure."""
    report = build_unregistered_document_candidates_report(
        project_root.resolve(),
        strict_scope=strict_scope,
    )
    if json_output:
        typer.echo(json.dumps(report, indent=2, sort_keys=True))
    else:
        typer.echo("DOC_REGISTRY_UNREGISTERED")
        typer.echo(f"STATUS={report['result_status']}")
        typer.echo(f"CANDIDATES={report['candidate_count']}")
        for candidate in report["candidates"]:
            typer.echo(f"- {candidate}")
        if report["scope_present"] and (
            report["scope_required_path_count"]
            or report["scope_exempt_path_count"]
            or report["scope_violation_count"]
            or report["scope_errors"]
        ):
            typer.echo(f"STRICT_SCOPE={report['strict_scope']}")
            typer.echo(f"EXEMPTED={report['exempted_count']}")
            typer.echo(f"SCOPE_VIOLATIONS={report['scope_violation_count']}")
            for violation in report["scope_violations"]:
                typer.echo(f"SCOPE-VIOLATION {violation}")
            for error in report["scope_errors"]:
                typer.echo(f"SCOPE-ERROR {error}")
    if report.get("result_status") == "FAIL":
        raise typer.Exit(code=1)
