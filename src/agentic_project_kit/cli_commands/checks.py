from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from agentic_project_kit.checks import check_all, check_docs, check_todo
from agentic_project_kit.doc_mesh import build_doc_mesh_report, render_doc_mesh_report, write_doc_mesh_json_report
from agentic_project_kit.doctor import build_doctor_report, render_doctor_report

console = Console()


def register_check_commands(app: typer.Typer) -> None:
    app.command("check")(check_command)
    app.command("check-docs")(check_docs_command)
    app.command("check-todo")(check_todo_command)
    app.command("doc-mesh-audit")(doc_mesh_audit_command)
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


def doc_mesh_audit_command(
    project_root: Annotated[Path, typer.Option("--root")] = Path("."),
    report_path: Annotated[Path | None, typer.Option("--report")] = None,
) -> None:
    """Audit cross-document state, governance, architecture, and historical-plan drift."""
    report = build_doc_mesh_report(project_root.resolve())
    if report_path is not None:
        write_doc_mesh_json_report(report, report_path)
    console.print(render_doc_mesh_report(report), markup=False)
    if not report.ok:
        raise typer.Exit(code=1)


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
    console.print("[bold green]Agentic project check passed[/bold green]
