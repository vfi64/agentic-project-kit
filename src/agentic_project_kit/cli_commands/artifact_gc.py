from __future__ import annotations

from pathlib import Path

import typer

from agentic_project_kit.communication_artifact_gc import (
    collect_candidates,
    execute_gc,
    execute_report_retention_gc,
    execute_tmp_log_gc,
    execute_transfer_run_report_gc,
    render_plan,
)


def _emit(outcome: str, message: str) -> None:
    typer.echo(outcome)
    if message:
        typer.echo(message)


def _ok(outcome: str) -> bool:
    return outcome.startswith("PASS") or outcome.startswith("PENDING")


def artifact_gc_command(
    tmp_logs: bool = typer.Option(False, "--tmp-logs", help="Collect expired local tmp logs."),
    local_tmp: bool = typer.Option(False, "--local-tmp", help="Use repository-local tmp/ instead of /tmp for --tmp-logs."),
    transfer_runs: bool = typer.Option(False, "--transfer-runs", help="Collect expired docs/reports/transfer_runs files."),
    report_retention: bool = typer.Option(False, "--report-retention", help="Collect expired report-like files under docs/terminal and selected docs/reports directories."),
    execute: bool = typer.Option(False, "--execute", help="Actually delete candidates. Default is dry-run."),
) -> None:
    """Dry-run by default garbage collector for transient communication artifacts."""
    selected_modes = sum(1 for enabled in (tmp_logs, transfer_runs, report_retention) if enabled)
    if selected_modes > 1:
        typer.echo("FAIL_MUTUALLY_EXCLUSIVE_MODES")
        raise typer.Exit(code=1)

    if tmp_logs:
        tmp_root = Path("tmp") if local_tmp else Path("/tmp")
        outcome, message = execute_tmp_log_gc(tmp_root, execute=execute)
        _emit(outcome, message)
        if not _ok(outcome):
            raise typer.Exit(code=1)
        return

    if transfer_runs:
        outcome, message = execute_transfer_run_report_gc(Path("."), execute=execute)
        _emit(outcome, message)
        if not _ok(outcome):
            raise typer.Exit(code=1)
        return

    if report_retention:
        outcome, message = execute_report_retention_gc(Path("."), execute=execute)
        _emit(outcome, message)
        if not _ok(outcome):
            raise typer.Exit(code=1)
        return

    if execute:
        outcome, message = execute_gc(Path("."))
        _emit(outcome, message)
        if not outcome.startswith("PASS"):
            raise typer.Exit(code=1)
        return

    typer.echo(render_plan(collect_candidates(Path("."))))
