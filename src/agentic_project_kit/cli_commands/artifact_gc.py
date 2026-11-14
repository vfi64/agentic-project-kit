from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import typer

from agentic_project_kit.cli_commands.routed_output import emit_routed, human_reason

from agentic_project_kit.communication_artifact_gc import (
    DEFAULT_TMP_LOG_TTL_SECONDS,
    collect_candidates,
    default_os_tmp_root,
    execute_gc,
    execute_report_retention_gc,
    execute_tmp_log_gc,
    execute_transfer_run_report_gc,
    render_plan,
)
from agentic_project_kit.local_garbage_collector import run_local_garbage_collector
from agentic_project_kit.workspace import load_workspace


MUTUALLY_EXCLUSIVE_MODES = "FAIL_MUTUALLY_EXCLUSIVE_MODES"
INVALID_OLDER_THAN = "FAIL_INVALID_OLDER_THAN"


def _message_lines(message: str) -> list[str]:
    return [line for line in message.splitlines() if line.strip()]


def _gc_payload(
    *,
    mode: str,
    outcome: str,
    message: str,
    execute: bool,
    ttl_seconds: int | None = None,
    older_than: str = "",
) -> dict[str, object]:
    lines = _message_lines(message)
    payload: dict[str, object] = {
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
    }
    if not _ok(outcome):
        payload.update(human_reason(_gc_fail_reason(outcome, lines)))
    return payload


def _gc_fail_reason(outcome: str, lines: list[str]) -> str:
    """G3: no Kit command resolves a refused collection; a person looks at the refused path."""
    if outcome == MUTUALLY_EXCLUSIVE_MODES:
        return "Choose only one GC mode: --tmp-logs, --local-tmp-contents, --transfer-runs or --report-retention."
    if outcome == INVALID_OLDER_THAN:
        return "Rerun with --older-than as an ISO date (YYYY-MM-DD) or datetime, or omit it to use --ttl-seconds."
    refused = lines[0] if lines else "a candidate"
    return f"{outcome}: the collector refused {refused}; inspect that path by hand, then rerun the dry run."


def _gc_text(outcome: str, message: str) -> str:
    return f"{outcome}\n{message}\n" if message else f"{outcome}\n"


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
        raise ValueError(f"--older-than must be an ISO date or datetime, got {older_than!r}") from exc
    now = datetime.now(timezone.utc)
    return max(0, int((now - cutoff.astimezone(timezone.utc)).total_seconds()))


def artifact_gc_command(
    tmp_logs: bool = typer.Option(False, "--tmp-logs", help="Collect expired local temp logs and protected-diff artifacts."),
    local_tmp: bool = typer.Option(False, "--local-tmp", help="Use repository-local tmp/ instead of the OS temp directory for --tmp-logs."),
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
        payload = _gc_payload(
            mode="invalid",
            outcome=MUTUALLY_EXCLUSIVE_MODES,
            message="Choose only one GC mode.",
            execute=execute,
            ttl_seconds=ttl_seconds,
            older_than=older_than,
        )
        emit_routed(payload, json_output=json_output, text=_gc_text(MUTUALLY_EXCLUSIVE_MODES, ""))
        raise typer.Exit(code=1)

    try:
        effective_ttl_seconds = _ttl_from_older_than(older_than, default_ttl_seconds=ttl_seconds)
    except ValueError as exc:
        # KIT-GF-113: an unreadable cutoff is a routed result, not a Click usage error.
        payload = _gc_payload(
            mode="invalid",
            outcome=INVALID_OLDER_THAN,
            message="",
            execute=execute,
            ttl_seconds=ttl_seconds,
            older_than=older_than,
        )
        payload["error"] = str(exc)
        emit_routed(payload, json_output=json_output, text=_gc_text(INVALID_OLDER_THAN, str(exc)))
        raise typer.Exit(code=2) from exc

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
        passed = result["result_status"] == "PASS"
        if not passed:
            errors = result.get("errors") or []
            first = errors[0] if errors and isinstance(errors[0], dict) else {}
            detail = f" First error: {first.get('path')}: {first.get('error')}" if first else ""
            result.update(human_reason(f"{result.get('next_action') or 'Local tmp/ cleanup failed.'}{detail}"))
        text = "PASS_LOCAL_TMP_CONTENTS\n" if passed else "FAIL_LOCAL_TMP_CONTENTS\n"
        text += "".join(f"{path}\n" for path in [*result.get("deleted", []), *result.get("deleted_directories", [])])
        emit_routed(result, json_output=json_output, text=text)
        if not passed:
            raise typer.Exit(code=1)
        return

    if tmp_logs or transfer_runs or report_retention:
        if tmp_logs:
            tmp_root = load_workspace(Path(".")).tmp() if local_tmp else default_os_tmp_root()
            outcome, message = execute_tmp_log_gc(tmp_root, execute=execute, ttl_seconds=effective_ttl_seconds)
            mode = "tmp-logs-local" if local_tmp else "tmp-logs"
        elif transfer_runs:
            outcome, message = execute_transfer_run_report_gc(Path("."), execute=execute, ttl_seconds=effective_ttl_seconds)
            mode = "transfer-runs"
        else:
            outcome, message = execute_report_retention_gc(Path("."), execute=execute, ttl_seconds=effective_ttl_seconds)
            mode = "report-retention"
        payload = _gc_payload(
            mode=mode,
            outcome=outcome,
            message=message,
            execute=execute,
            ttl_seconds=effective_ttl_seconds,
            older_than=older_than,
        )
        emit_routed(payload, json_output=json_output, text=_gc_text(outcome, message))
        if not _ok(outcome):
            raise typer.Exit(code=1)
        return

    if execute:
        outcome, message = execute_gc(Path("."))
        payload = _gc_payload(mode="communication-artifacts", outcome=outcome, message=message, execute=execute)
        emit_routed(payload, json_output=json_output, text=_gc_text(outcome, message))
        if not outcome.startswith("PASS"):
            raise typer.Exit(code=1)
        return

    plan = render_plan(collect_candidates(Path(".")))
    outcome, *rest = plan.splitlines()
    payload = _gc_payload(mode="communication-artifacts", outcome=outcome, message="\n".join(rest), execute=False)
    emit_routed(payload, json_output=json_output, text=f"{plan}\n")
