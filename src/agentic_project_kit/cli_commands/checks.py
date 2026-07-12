from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from agentic_project_kit.checks import check_all, check_docs, check_todo
from agentic_project_kit.doc_mesh import (
    apply_doc_mesh_repair_plan,
    build_doc_mesh_repair_plan,
    build_doc_mesh_report,
    render_doc_mesh_repair_plan,
    render_doc_mesh_repair_result,
    render_doc_mesh_report,
    write_doc_mesh_json_report,
    write_doc_mesh_repair_plan,
    write_doc_mesh_repair_result,
)
from agentic_project_kit.doc_lifecycle import (
    build_doc_lifecycle_report,
    build_doc_lifecycle_strict_findings,
    render_doc_lifecycle_report,
    render_doc_lifecycle_strict_findings,
    write_doc_lifecycle_json_report,
)
from agentic_project_kit.doc_lifecycle_signals import (
    build_doc_orphan_report,
    build_review_after_suggestions,
    render_doc_orphan_report,
    render_review_after_suggestions,
    review_after_suggestions_to_dict,
    write_doc_orphan_json_report,
)
from agentic_project_kit.documentation_registry import (
    build_documentation_registry_summary,
    render_documentation_registry_summary,
    write_documentation_registry_summary_json,
)
from agentic_project_kit.documentation_system_audit import (
    build_documentation_system_audit,
    render_documentation_system_audit,
    write_documentation_system_audit_json,
)
from agentic_project_kit.doctor import build_doctor_report, render_doctor_report

console = Console()


def register_check_commands(app: typer.Typer) -> None:
    app.command("check")(check_command)
    app.command("check-docs")(check_docs_command)
    app.command("check-todo")(check_todo_command)
    app.command("docs-audit")(docs_audit_command)
    app.command("docs-registry")(docs_registry_command)
    app.command("doc-mesh-audit")(doc_mesh_audit_command)
    app.command("doc-lifecycle-audit")(doc_lifecycle_audit_command)
    app.command("audit-doc-orphans")(audit_doc_orphans_command)
    app.command("doc-mesh-repair")(doc_mesh_repair_command)
    app.command("doctor")(doctor_command)


def check_command(project_root: Path = typer.Option(Path("."), "--root")) -> None:
    errors = check_all(project_root.resolve())
    _print_result(errors)


def check_docs_command(project_root: Path = typer.Option(Path("."), "--root")) -> None:
    errors = check_docs(project_root.resolve())
    _print_result(errors)


def check_todo_command(project_root: Path = typer.Option(Path("."), "--root")) -> None:
    errors = check_todo(project_root.resolve())
    _print_result(errors)


def docs_audit_command(
    project_root: Annotated[Path, typer.Option("--root")] = Path("."),
    report_path: Annotated[Path | None, typer.Option("--report")] = None,
) -> None:
    """Run the umbrella documentation-system audit."""
    report = build_documentation_system_audit(project_root.resolve())
    if report_path is not None:
        write_documentation_system_audit_json(report, report_path)
    console.print(render_documentation_system_audit(report), markup=False)
    if not report.ok:
        raise typer.Exit(code=1)


def docs_registry_command(
    project_root: Annotated[Path, typer.Option("--root")] = Path("."),
    report_path: Annotated[Path | None, typer.Option("--report")] = None,
) -> None:
    """Show a read-only summary of the documentation registry."""
    summary = build_documentation_registry_summary(project_root.resolve())
    if report_path is not None:
        write_documentation_registry_summary_json(summary, report_path)
    console.print(render_documentation_registry_summary(summary), markup=False)


def doc_lifecycle_audit_command(
    project_root: Annotated[Path, typer.Option("--root")] = Path("."),
    report_path: Annotated[Path | None, typer.Option("--report")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Print JSON instead of text.")] = False,
    strict: Annotated[
        bool,
        typer.Option("--strict", help="Fail on deterministic lifecycle blocker findings."),
    ] = False,
    current_version: Annotated[
        str | None,
        typer.Option("--current-version", help="Override the version used for release review_after checks."),
    ] = None,
    suggest_review_after: Annotated[
        bool,
        typer.Option("--suggest-review-after", help="Print report-only review_after suggestions from version target prose."),
    ] = False,
) -> None:
    """Audit lifecycle status headers for planning, roadmap, strategy, and idea documents."""
    if suggest_review_after:
        suggestions = build_review_after_suggestions(project_root.resolve())
        if json_output:
            typer.echo(json.dumps(review_after_suggestions_to_dict(suggestions), indent=2, sort_keys=True))
        else:
            console.print(render_review_after_suggestions(suggestions), markup=False)
        return

    root = project_root.resolve()
    report = build_doc_lifecycle_report(root, current_version=current_version)
    strict_findings = build_doc_lifecycle_strict_findings(root, report=report) if strict else ()
    if report_path is not None:
        write_doc_lifecycle_json_report(report, report_path)
    if json_output:
        payload = report.to_dict()
        if strict:
            payload["strict"] = {
                "ok": not strict_findings,
                "blocker_count": len(strict_findings),
                "blockers": [finding.to_dict() for finding in strict_findings],
            }
        typer.echo(json.dumps(payload, indent=2, sort_keys=True))
    else:
        console.print(render_doc_lifecycle_report(report), markup=False)
        if strict:
            console.print(render_doc_lifecycle_strict_findings(strict_findings), markup=False)
    if strict and strict_findings:
        raise typer.Exit(code=1)
    if not report.ok:
        raise typer.Exit(code=1)


def audit_doc_orphans_command(
    project_root: Annotated[Path, typer.Option("--root")] = Path("."),
    report_path: Annotated[Path | None, typer.Option("--report")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Print JSON instead of text.")] = False,
) -> None:
    """Report registered documents without incoming repository references."""
    report = build_doc_orphan_report(project_root.resolve())
    if report_path is not None:
        write_doc_orphan_json_report(report, report_path)
    if json_output:
        typer.echo(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        console.print(render_doc_orphan_report(report), markup=False)


def doc_mesh_audit_command(
    project_root: Annotated[Path, typer.Option("--root")] = Path("."),
    report_path: Annotated[Path | None, typer.Option("--report")] = None,
    repair_plan_path: Annotated[Path | None, typer.Option("--repair-plan")] = None,
) -> None:
    """Audit cross-document state, governance, architecture, and historical-plan drift."""
    report = build_doc_mesh_report(project_root.resolve())
    if report_path is not None:
        write_doc_mesh_json_report(report, report_path)
    if repair_plan_path is not None:
        repair_plan = build_doc_mesh_repair_plan(report)
        write_doc_mesh_repair_plan(repair_plan, repair_plan_path)
        console.print(render_doc_mesh_repair_plan(repair_plan), markup=False)
    console.print(render_doc_mesh_report(report), markup=False)
    if not report.ok:
        raise typer.Exit(code=1)


def doc_mesh_repair_command(
    project_root: Annotated[Path, typer.Option("--root")] = Path("."),
    result_path: Annotated[Path | None, typer.Option("--result")] = None,
) -> None:
    """Apply safe automatic documentation mesh repairs."""
    report = build_doc_mesh_report(project_root.resolve())
    repair_plan = build_doc_mesh_repair_plan(report)
    result = apply_doc_mesh_repair_plan(project_root.resolve(), repair_plan)
    if result_path is not None:
        write_doc_mesh_repair_result(result, result_path)
    console.print(render_doc_mesh_repair_result(result), markup=False)


def doctor_command(project_root: Path = typer.Option(Path("."), "--root")) -> None:
    """Run a compact project health check."""
    report = build_doctor_report(project_root.resolve())
    console.print(render_doctor_report(report), markup=False)
    if not report.ok:
        raise typer.Exit(code=1)


def _print_result(errors: list[str]) -> None:
    if errors:
        console.print("[bold red]Agentic project check failed[/bold red]")
        for error in errors:
            console.print(f"[red]- {error}[/red]")
        raise typer.Exit(code=1)
    console.print("[bold green]Agentic project check passed[/bold green]")
