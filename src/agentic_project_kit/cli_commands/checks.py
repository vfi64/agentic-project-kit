from __future__ import annotations

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
from agentic_project_kit.doc_lifecycle import build_doc_lifecycle_report, render_doc_lifecycle_report, write_doc_lifecycle_json_report
from agentic_project_kit.doctor import build_doctor_report, render_doctor_report

console = Console()


def register_check_commands(app: typer.Typer) -> None:
    app.command("check")(check_command)
    app.command("check-docs")(check_docs_command)
    app.command("check-todo")(check_todo_command)
    app.command("doc-mesh-audit")(doc_mesh_audit_command)
    app.command("doc-lifecycle-audit")(doc_lifecycle_audit_command)
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


def doc_lifecycle_audit_command(
    project_root: Annotated[Path, typer.Option("--root")] = Path("."),
    report_path: Annotated[Path | None, typer.Option("--report")] = None,
) -> None:
    """Audit lifecycle status headers for planning, roadmap, strategy, and idea documents."""
    report = build_doc_lifecycle_report(project_root.resolve())
    if report_path is not None:
        write_doc_lifecycle_json_report(report, report_path)
    console.print(render_doc_lifecycle_report(report), markup=False)
    if not report.ok:
        raise typer.Exit(code=1)


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
