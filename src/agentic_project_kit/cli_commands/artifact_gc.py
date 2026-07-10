from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path

import typer

from agentic_project_kit.communication_artifact_gc import (
    DEFAULT_TMP_LOG_TTL_SECONDS,
    collect_candidates,
    execute_gc,
    execute_report_retention_gc,
    execute_tmp_log_gc,
    execute_transfer_run_report_gc,
    render_plan,
)
from agentic_project_kit.local_garbage_collector import run_local_garbage_collector
from agentic_project_kit.workspace import load_workspace


def _message_lines(message: str) -> list[str]:
    return [line for line in message.splitlines() if line.strip()]


def _emit_json(
    *,
    mode: str,
    outcome: str,
    message: str,
    execute: bool,
    ttl_seconds: int | None = None,
    older_than: str = "",
) -> None:
    lines = _message_lines(message)
    typer.echo(
        json.dumps(
            {
                "schema_version": 1,
                "kind": "artifact_gc_result",
                "mode": mode,
                "result_status": "PASS" if _ok(outcome) else "FAIL",
                "outcome": outcome,
                "execute": execute,
                "dry_run": not execute,
                "ttl_seconds": ttl_seconds,
                "older_than": older_than or None,
                "candidate_count": len(lines),
                "candidates": lines,
                "remote_execution_policy": {
                    "status": "not_automatic",
                    "allowed_path": "dry-run report -> explicit confirm -> normal commit/PR lifecycle",
                    "forbidden_path": "ad-hoc remote deletion or a new transfer gc-logs command",
                },
            },
            indent=2,
            sort_keys=True,
        )
    )


def _emit(outcome: str, message: str) -> None:
    typer.echo(outcome)
    if message:
        typer.echo(message)


def _ok(outcome: str) -> bool:
    return outcome.startswith("PASS") or outcome.startswith("PENDING")


def _ttl_from_older_than(older_than: str, *, default_ttl_seconds: int) -> int:
    text = older_than.strip()
    if not text:
        return default_ttl_seconds
    try:
        if len(text) == 10:
            cutoff = datetime.fromisoformat(text).replace(tzinfo=timezone.utc)
        else:
            cutoff = datetime.fromisoformat(text.replace("Z", "+00:00"))
            if cutoff.tzinfo is None:
                cutoff = cutoff.replace(tzinfo=timezone.utc)
    except ValueError as exc:
        raise typer.BadParameter("--older-than must be an ISO date or datetime") from exc
    now = datetime.now(timezone.utc)
    return max(0, int((now - cutoff.astimezone(timezone.utc)).total_seconds()))


def artifact_gc_command(
    tmp_logs: bool = typer.Option(False, "--tmp-logs", help="Collect expired local tmp logs."),
    local_tmp: bool = typer.Option(False, "--local-tmp", help="Use repository-local tmp/ instead of /tmp for --tmp-logs."),
    local_tmp_contents: bool = typer.Option(
        False,
        "--local-tmp-contents",
        help="Collect expired untracked files and empty directories under repository-local tmp/.",
    ),
    transfer_runs: bool = typer.Option(False, "--transfer-runs", help="Collect expired docs/reports/transfer_runs files."),
    report_retention: bool = typer.Option(
        False,
        "--report-retention",
        help="Collect expired report-like files and generated successor-handoff Markdown under selected docs/report surfaces.",
    ),
    execute: bool = typer.Option(False, "--execute", help="Actually delete candidates. Default is dry-run."),
    ttl_seconds: int = typer.Option(
        DEFAULT_TMP_LOG_TTL_SECONDS,
        "--ttl-seconds",
        min=0,
        help="Retention age in seconds for age-gated modes.",
    ),
    older_than: str = typer.Option(
        "",
        "--older-than",
        help="ISO date/datetime cutoff. Overrides --ttl-seconds for age-gated modes.",
    ),
    json_output: bool = typer.Option(False, "--json", help="Print machine-readable JSON."),
) -> None:
    """Dry-run by default garbage collector for transient communication artifacts."""
    selected_modes = sum(1 for enabled in (tmp_logs, local_tmp_contents, transfer_runs, report_retention) if enabled)
    if selected_modes > 1:
        if json_output:
            _emit_json(
                mode="invalid",
                outcome="FAIL_MUTUALLY_EXCLUSIVE_MODES",
                message="Choose only one GC mode.",
                execute=execute,
                ttl_seconds=ttl_seconds,
                older_than=older_than,
            )
        else:
            typer.echo("FAIL_MUTUALLY_EXCLUSIVE_MODES")
        raise typer.Exit(code=1)

    effective_ttl_seconds = _ttl_from_older_than(older_than, default_ttl_seconds=ttl_seconds)

    if local_tmp_contents:
        result = run_local_garbage_collector(
            Path("."),
            dry_run=not execute,
            retention_seconds=effective_ttl_seconds,
            write_report=True,
            skip_if_run_id_seen=False,
        )
        result = {
            **result,
            "mode": "local-tmp-contents",
            "older_than": older_than or None,
            "remote_execution_policy": {
                "status": "forbidden",
                "allowed_path": "local repo tmp/ cleanup only",
                "forbidden_path": "remote tmp cleanup, report retention, or git push from this mode",
            },
        }
        if json_output:
            typer.echo(json.dumps(result, indent=2, sort_keys=True))
        else:
            typer.echo("PASS_LOCAL_TMP_CONTENTS" if result["result_status"] == "PASS" else "FAIL_LOCAL_TMP_CONTENTS")
            for path in [*result.get("deleted", []), *result.get("deleted_directories", [])]:
                typer.echo(path)
        if result["result_status"] != "PASS":
            raise typer.Exit(code=1)
        return

    if tmp_logs:
        tmp_root = load_workspace(Path(".")).tmp() if local_tmp else Path("/tmp")
        outcome, message = execute_tmp_log_gc(tmp_root, execute=execute, ttl_seconds=effective_ttl_seconds)
        if json_output:
            _emit_json(
                mode="tmp-logs-local" if local_tmp else "tmp-logs",
                outcome=outcome,
                message=message,
                execute=execute,
                ttl_seconds=effective_ttl_seconds,
                older_than=older_than,
            )
        else:
            _emit(outcome, message)
        if not _ok(outcome):
            raise typer.Exit(code=1)
        return

    if transfer_runs:
        outcome, message = execute_transfer_run_report_gc(Path("."), execute=execute, ttl_seconds=effective_ttl_seconds)
        if json_output:
            _emit_json(
                mode="transfer-runs",
                outcome=outcome,
                message=message,
                execute=execute,
                ttl_seconds=effective_ttl_seconds,
                older_than=older_than,
            )
        else:
            _emit(outcome, message)
        if not _ok(outcome):
            raise typer.Exit(code=1)
        return

    if report_retention:
        outcome, message = execute_report_retention_gc(Path("."), execute=execute, ttl_seconds=effective_ttl_seconds)
        if json_output:
            _emit_json(
                mode="report-retention",
                outcome=outcome,
                message=message,
                execute=execute,
                ttl_seconds=effective_ttl_seconds,
                older_than=older_than,
            )
        else:
            _emit(outcome, message)
        if not _ok(outcome):
            raise typer.Exit(code=1)
        return

    if execute:
        outcome, message = execute_gc(Path("."))
        if json_output:
            _emit_json(
                mode="communication-artifacts",
                outcome=outcome,
                message=message,
                execute=execute,
            )
        else:
            _emit(outcome, message)
        if not outcome.startswith("PASS"):
            raise typer.Exit(code=1)
        return

    message = render_plan(collect_candidates(Path(".")))
    if json_output:
        outcome, *rest = message.splitlines()
        _emit_json(
            mode="communication-artifacts",
            outcome=outcome,
            message="\n".join(rest),
            execute=False,
        )
    else:
        typer.echo(message)
