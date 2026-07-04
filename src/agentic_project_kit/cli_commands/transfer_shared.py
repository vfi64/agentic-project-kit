from __future__ import annotations

# ruff: noqa: F401

from datetime import date as date_cls
import json
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

import typer
from agentic_project_kit.transfer_safety_context import render_local_to_llm_log_header, render_local_to_llm_log_upload_hint, build_transfer_safety_header
import yaml

from agentic_project_kit.communication_rule_context import require_current_communication_context
from agentic_project_kit.llm_context_carriers import refresh_llm_context_carriers
from agentic_project_kit.local_garbage_collector import run_local_garbage_collector
from agentic_project_kit.local_command_stack import begin_local_command_stack
from agentic_project_kit.local_command_stack import current_or_begin_local_command_stack_id
from agentic_project_kit.local_command_stack import end_local_command_stack
from agentic_project_kit.patch_cycle_workflow import build_patch_cycle_status, render_patch_cycle_status
from agentic_project_kit.transfer_closeout import closeout_transfer
from agentic_project_kit.transfer_continue import render_transfer_continue_summary
from agentic_project_kit.transfer_continue import run_transfer_continue
from agentic_project_kit.transfer_local_runner import run_local_transfer
from agentic_project_kit.transfer_pr_actions import pr_status_transfer
from agentic_project_kit.transfer_remote_next import run_remote_next_transfer
from agentic_project_kit.transfer_repo_actions import (
    RepoActionResult,
    admin_refresh_pr,
    branch_create,
    branch_delete,
    branch_switch,
    commit_paths,
    fetch_origin,
    head_sha,
    pr_create,
    pr_merge_safe,
    pr_wait_ci,
    post_merge_check,
    pull_current,
    push_current,
    repo_diff,
    repo_log,
    repo_status,
    result_json,
    result_terminal,
)
from agentic_project_kit.transfer_runner import (
    DEFAULT_INBOX,
    apply_transfer_order,
    inspect_transfer_order,
    load_transfer_order,
    transfer_result_as_json_data,
)
from agentic_project_kit.transfer_state import build_transfer_state
from agentic_project_kit.transfer_state import normalize_transfer_file_lifecycle
from agentic_project_kit.work_order_patch import (
    DEFAULT_PATCH_ORDER,
    WorkOrderPatchResult,
    apply_work_order_patch,
    load_work_order_patch,
    render_work_order_patch_result,
    work_order_patch_result_as_json_data,
)
from agentic_project_kit.successor_handoff_package import write_successor_handoff_package
from agentic_project_kit.transfer_uplink import (
    publish_latest_transfer_report,
    read_latest_transfer_report,
    run_and_log_transfer_command,
    run_and_log_transfer_sequence,
    write_transfer_report_from_repo_result,
)
from agentic_project_kit.transfer_workflow_next import run_workflow_next
from agentic_project_kit import wrapper_live_status

transfer_app = typer.Typer(help="Inspect and apply repo-backed text transfer orders.")

def _run_local_garbage_collector_preflight() -> None:
    """Run deterministic local runtime cleanup before local transfer preflight."""
    command_stack_id = current_or_begin_local_command_stack_id(Path("."))
    result = run_local_garbage_collector(Path("."), write_report=True, run_id=command_stack_id)
    if int(result.get("returncode", 0)) != 0:
        raise typer.BadParameter(str(result.get("next_action", "local garbage collector failed")))

def _load_or_exit(path: Path):
    try:
        return load_transfer_order(path)
    except (FileNotFoundError, ValueError) as exc:
        typer.echo(str(exc))
        raise typer.Exit(code=1) from exc

def _emit_result(result, json_output: bool) -> None:
    if json_output:
        typer.echo(json.dumps(transfer_result_as_json_data(result), indent=2, sort_keys=True))
    else:
        typer.echo(f"transfer_id={result.transfer_id}")
        typer.echo(f"result_status={result.result_status}")
        typer.echo(f"returncode={result.returncode}")
        typer.echo(f"report_path={result.report_path}")
        typer.echo(f"message={result.message}")

def _echo_repo_result(result, json_output: bool) -> None:
    typer.echo(result_json(result) if json_output else result_terminal(result))


def _public_transfer_attr(name: str, fallback):
    public_module = sys.modules.get("agentic_project_kit.cli_commands.transfer")
    if public_module is not None and hasattr(public_module, name):
        return getattr(public_module, name)
    return fallback


def _echo_quiet_repo_report(result: RepoActionResult, *, label: str) -> None:
    uplink = write_transfer_report_from_repo_result(result, label=label, cwd=Path("."))
    typer.echo("TRANSFER_UPLOAD=done")
    typer.echo(f"REMOTE_REPORT={uplink.remote_report_path}")
    typer.echo("CHAT_REPLY=g")

def _echo_transfer_payload_summary(
    *,
    title: str,
    result_status: str,
    final_signal: str,
    next_action: str,
    fields: dict[str, object] | None = None,
) -> None:
    typer.echo("*" * 34 + " START SUMMARY " + "*" * 35)
    typer.echo(title)
    typer.echo("")
    typer.echo(_summary_line("STATE", result_status))
    if fields:
        for key, value in fields.items():
            typer.echo(_summary_line(key, value))
    typer.echo("")
    typer.echo(_summary_line("NEXT", next_action))
    typer.echo(_summary_line("CHAT_REPLY", f"{final_signal} | NEXT={next_action}"))
    typer.echo("*" * 35 + " END SUMMARY " + "*" * 36)

def _summary_line(label: str, value: object, *, indent: int = 0, width: int = 24) -> str:
    return f"{' ' * indent}{label + ':':<{width}}{value}"

def _summary_items(title: str, values: object, *, label: str) -> None:
    if not isinstance(values, (list, tuple)) or not values:
        return
    typer.echo(title)
    for value in values:
        typer.echo(_summary_line(label, value, indent=2))
    typer.echo("")

def _dirty_state_from_result(result) -> dict[str, object]:
    preflight = result.preflight if isinstance(result.preflight, dict) else {}
    dirty_state = preflight.get("dirty_state")
    if isinstance(dirty_state, dict):
        return dirty_state
    local_run_state = getattr(result.local_run, "state", None)
    if isinstance(local_run_state, dict):
        nested_dirty_state = local_run_state.get("dirty_state")
        if isinstance(nested_dirty_state, dict):
            return nested_dirty_state
    return {}

def _echo_remote_next_user_summary(result) -> None:
    actions = result.post_report_actions or {}
    committed = bool(actions.get("committed"))
    pushed = bool(actions.get("pushed"))
    uploaded = "yes" if pushed else "no_push_failed" if committed else "no_commit_failed"
    dirty_state = _dirty_state_from_result(result)
    rule_ack = result.rule_ack.as_json_data() if result.rule_ack else None

    typer.echo("*" * 36 + " START SUMMARY " + "*" * 36)
    typer.echo("TRANSFER_REMOTE_NEXT_DONE")
    typer.echo("")
    if "no_current_transfer_order" in result.reasons:
        primary_state = "NEW_ORDER_REQUIRED"
    elif "order_consumed" in result.reasons:
        primary_state = "ORDER_CONSUMED"
    elif any(
        reason in result.reasons
        for reason in (
            "stale_transfer_order_status",
            "stale_transfer_order_branch_mismatch",
            "stale_order_missing_freshness_anchor",
            "stale_transfer_order_head_mismatch",
        )
    ):
        primary_state = "STALE_ORDER"
    else:
        primary_state = result.result_status
    typer.echo(_summary_line("STATE", primary_state))
    typer.echo(_summary_line("RETURNCODE", result.returncode))
    if result.reasons:
        typer.echo(_summary_line("REASONS", ",".join(result.reasons)))
    typer.echo("")
    if dirty_state:
        typer.echo("LOCAL_STATE:")
        typer.echo(_summary_line("CLEAN", "yes" if dirty_state.get("clean") else "no", indent=2))
        typer.echo(_summary_line("BRANCH", result.preflight.get("current_branch", result.branch or ""), indent=2))
        typer.echo(_summary_line("HEAD", result.head, indent=2))
        for path in dirty_state.get("staged_changes", ()):
            typer.echo(_summary_line("STAGED", path, indent=2))
        for path in dirty_state.get("unstaged_changes", ()):
            typer.echo(_summary_line("UNSTAGED", path, indent=2))
        for path in dirty_state.get("untracked_files", ()):
            typer.echo(_summary_line("UNTRACKED", path, indent=2))
        typer.echo("")
    if rule_ack is not None:
        typer.echo("RULE_ACK:")
        typer.echo(_summary_line("PRESENT", "yes" if rule_ack.get("present") else "no", indent=2))
        typer.echo(_summary_line("CONFIRMED", "yes" if rule_ack.get("confirmed") else "no", indent=2))
        if rule_ack.get("head"):
            typer.echo(_summary_line("HEAD", rule_ack["head"], indent=2))
        for reason in rule_ack.get("blocking_reasons", ()):
            typer.echo(_summary_line("BLOCKING_REASON", reason, indent=2))
        typer.echo("")
    final_rule_ack = actions.get("rule_ack_after_report_commit")
    if isinstance(final_rule_ack, dict):
        typer.echo("RULE_ACK_AFTER_REPORT:")
        typer.echo(_summary_line("PRESENT", "yes" if final_rule_ack.get("present") else "no", indent=2))
        typer.echo(_summary_line("CONFIRMED", "yes" if final_rule_ack.get("confirmed") else "no", indent=2))
        if final_rule_ack.get("head"):
            typer.echo(_summary_line("HEAD", final_rule_ack["head"], indent=2))
        for reason in final_rule_ack.get("blocking_reasons", ()):
            typer.echo(_summary_line("BLOCKING_REASON", reason, indent=2))
        typer.echo("")
    _summary_items("BLOCKERS:", result.reasons, label="REASON")
    typer.echo("REMOTE_REPORT:")
    typer.echo(_summary_line("UPLOADED", uploaded, indent=2))
    typer.echo(_summary_line("COMMITTED", "yes" if committed else "no", indent=2))
    typer.echo(_summary_line("PUSHED", "yes" if pushed else "no", indent=2))
    typer.echo(_summary_line("REPORT_PATH", result.published_report_path, indent=2))
    if actions.get("commit_head"):
        typer.echo(_summary_line("REPORT_COMMIT", actions["commit_head"], indent=2))
    if actions.get("blocked_reason"):
        typer.echo(_summary_line("BLOCKED_REASON", actions["blocked_reason"], indent=2))
    typer.echo("")
    typer.echo("LOCAL:")
    typer.echo(_summary_line("REPORT_PATH", result.report_path, indent=2))
    typer.echo("")
    typer.echo(_summary_line("NEXT", result.next_action))
    typer.echo(_summary_line("CHAT_REPLY", "g"))
    typer.echo("*" * 37 + " END SUMMARY " + "*" * 37)

def _require_transfer_capability(capability: str) -> None:
    snapshot = build_transfer_state(Path("."))
    if snapshot.capabilities.get(capability, False):
        return
    typer.echo(
        json.dumps(
            {
                "chat_reply": "f",
                "next_safe_action": snapshot.next_action,
                "result_status": "BLOCKED",
                "returncode": 2,
                "required_capability": capability,
                "primary_state": snapshot.primary_state,
                "reasons": snapshot.reasons,
                "next_action": snapshot.next_action,
                "rule_acknowledgement": snapshot.rule_acknowledgement,
            },
            indent=2,
            sort_keys=True,
        )
    )
    typer.echo("FINAL_SIGNAL=f")
    typer.echo(f"FINAL_NEXT={snapshot.next_action}")
    typer.echo(f"CHAT_REPLY=f | NEXT={snapshot.next_action}")
    raise typer.Exit(code=2)


__all__ = [name for name in globals() if not name.startswith("__")]
