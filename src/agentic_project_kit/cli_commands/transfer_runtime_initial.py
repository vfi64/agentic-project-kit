from __future__ import annotations

# ruff: noqa: F403,F405

from agentic_project_kit.cli_commands.transfer_shared import *
from agentic_project_kit.cli_commands.transfer_context_helpers import _ensure_fresh_llm_context_or_exit


@transfer_app.command("run-and-log", context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
def run_and_log(
    ctx: typer.Context,
    label: str = typer.Option("transfer-run", "--label", help="Label for the transfer uplink report."),
    json_output: bool = typer.Option(False, "--json", help="Print JSON instead of text."),
) -> None:
    command = list(ctx.args)
    if command[:1] == ["--"]:
        command = command[1:]
    try:
        result = run_and_log_transfer_command(command, label=label, cwd=Path("."))
    except ValueError as exc:
        typer.echo(str(exc))
        typer.echo("FINAL_SIGNAL=f")
        typer.echo("FINAL_NEXT=Provide a command after run-and-log.")
        typer.echo("CHAT_REPLY=f | NEXT=Provide a command after run-and-log.")
        raise typer.Exit(code=2) from exc

    if json_output:
        typer.echo(json.dumps(result.as_json_data(), indent=2, sort_keys=True))
    else:
        typer.echo("TRANSFER_REPORT_WRITTEN=done")
        typer.echo(f"LOCAL_REPORT={result.remote_report_path}")
        typer.echo("CHAT_REPLY=d | NEXT=Run transfer publish-last-report")

    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)

@transfer_app.command("closeout")
def closeout(
    no_remove_transfer_dir: bool = typer.Option(
        False,
        "--no-remove-transfer-dir",
        help="Do not remove .agentic/transfer during closeout.",
    ),
    json_output: bool = typer.Option(True, "--json/--no-json", help="Print machine-readable JSON."),
) -> None:
    try:
        result = closeout_transfer(Path("."), remove_transfer_dir=not no_remove_transfer_dir)
    except RuntimeError as exc:
        typer.echo(str(exc))
        raise typer.Exit(code=1) from exc

    if json_output:
        typer.echo(json.dumps(result.as_json_data(), indent=2, sort_keys=True))
    else:
        typer.echo(f"result_status={result.result_status}")
        typer.echo(f"returncode={result.returncode}")
        typer.echo(f"removed_transfer_dir={result.removed_transfer_dir}")
        typer.echo(f"latest_command_run_path={result.latest_command_run_path}")
        typer.echo(f"blocked_dirty_paths={','.join(result.blocked_dirty_paths)}")
        typer.echo(f"next_action={result.next_action}")

    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)

@transfer_app.command("continue")
def continue_transfer_command(
    branch: str | None = typer.Argument(
        None,
        help="Optional target branch. If omitted, infer a single active transfer order.",
    ),
    json_output: bool = typer.Option(False, "--json/--no-json", help="Print machine-readable JSON."),
    skip_llm_context_gate: bool = typer.Option(
        False,
        "--skip-llm-context-gate",
        help="Recovery-only: continue without requiring fresh generated LLM context.",
    ),
) -> None:
    """Continue chat/local transfer communication through the safest available wrapper path."""
    if not skip_llm_context_gate:
        ensure = _public_transfer_attr("_ensure_fresh_llm_context_or_exit", _ensure_fresh_llm_context_or_exit)
        ensure(max_age_minutes=60, json_output=json_output)
    run_continue = _public_transfer_attr("run_transfer_continue", run_transfer_continue)
    result = run_continue(Path("."), branch)
    if json_output:
        typer.echo(json.dumps(result, indent=2, sort_keys=True))
    else:
        render_summary = _public_transfer_attr("render_transfer_continue_summary", render_transfer_continue_summary)
        typer.echo(render_summary(result))
    if int(result.get("returncode", 2)) != 0:
        raise typer.Exit(code=int(result.get("returncode", 2)))

@transfer_app.command("remote-next")
def remote_next(
    branch: str | None = typer.Argument(
        None,
        help="Optional remote transfer branch. If omitted, read branch from the transfer order.",
    ),
    json_output: bool = typer.Option(False, "--json/--no-json", help="Print machine-readable JSON."),
) -> None:
    try:
        result = run_remote_next_transfer(Path("."), branch)
    except (RuntimeError, ValueError, FileNotFoundError) as exc:
        typer.echo(str(exc))
        raise typer.Exit(code=1) from exc

    if json_output:
        typer.echo(json.dumps(result.as_json_data(), indent=2, sort_keys=True))
    else:
        _echo_remote_next_user_summary(result)

    if result.local_run.returncode != 0:
        raise typer.Exit(code=result.local_run.returncode)

@transfer_app.command("command-stack-begin")
def command_stack_begin_command(
    json_output: bool = typer.Option(True, "--json/--no-json", help="Print machine-readable JSON."),
) -> None:
    """Begin a repo-local command-stack state for deterministic local preflight cleanup."""
    state = begin_local_command_stack(Path("."))
    if json_output:
        typer.echo(json.dumps(state, indent=2, sort_keys=True))
    else:
        typer.echo(_summary_line("STATE", "PASS"))
        typer.echo(_summary_line("COMMAND_STACK_ID", state["command_stack_id"]))
        typer.echo(_summary_line("NEXT", "Run normalize-session."))

@transfer_app.command("command-stack-end")
def command_stack_end_command(
    json_output: bool = typer.Option(True, "--json/--no-json", help="Print machine-readable JSON."),
) -> None:
    """End the repo-local command-stack state after a local command stack completed."""
    state = end_local_command_stack(Path("."))
    if json_output:
        typer.echo(json.dumps(state, indent=2, sort_keys=True))
    else:
        typer.echo(_summary_line("STATE", "PASS"))
        typer.echo(_summary_line("COMMAND_STACK_ID", state.get("command_stack_id", "")))
        typer.echo(_summary_line("NEXT", "Command stack ended."))

@transfer_app.command("normalize-files")
def normalize_transfer_files_command(
    dry_run: bool = typer.Option(False, "--dry-run", help="Report transfer file lifecycle repairs without applying them."),
    json_output: bool = typer.Option(True, "--json/--no-json", help="Print machine-readable JSON."),
) -> None:
    """Normalize active transfer files by adding missing command IDs and archiving stale active files."""
    result = normalize_transfer_file_lifecycle(Path("."), dry_run=dry_run)
    if json_output:
        typer.echo(json.dumps(result, indent=2, sort_keys=True))
    else:
        _echo_transfer_payload_summary(
            title="TRANSFER_NORMALIZE_FILES",
            result_status=str(result["result_status"]),
            final_signal="d" if result["result_status"] == "PASS" else "f",
            next_action=str(result["next_action"]),
            fields={
                "DRY_RUN": "yes" if dry_run else "no",
                "OPERATIONS": len(result["operations"]),
                "BEFORE": result["before"]["state"],
                "AFTER": result["after"]["state"],
            },
        )
    if int(result["returncode"]) != 0:
        raise typer.Exit(code=int(result["returncode"]))

@transfer_app.command("workflow-next")
def workflow_next_command(
    json_output: bool = typer.Option(False, "--json/--no-json", help="Print machine-readable JSON."),
) -> None:
    """Read repo and transfer state and print the next safe wrapper command without mutating state."""
    result = run_workflow_next(Path("."))
    if json_output:
        typer.echo(json.dumps(result.as_json_data(), indent=2, sort_keys=True))
    else:
        typer.echo("*" * 35 + " START SUMMARY " + "*" * 35)
        typer.echo("TRANSFER_WORKFLOW_NEXT")
        typer.echo("")
        typer.echo(_summary_line("STATE", result.state))
        typer.echo(_summary_line("RETURNCODE", result.returncode))
        if result.reasons:
            typer.echo(_summary_line("REASONS", ",".join(result.reasons)))
        if result.command:
            typer.echo(_summary_line("COMMAND", " ".join(result.command)))
        typer.echo("")
        typer.echo(_summary_line("NEXT", result.next_action))
        typer.echo(_summary_line("CHAT_REPLY", ("g" if result.returncode == 0 else "f")))
        typer.echo("*" * 36 + " END SUMMARY " + "*" * 36)
    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)


__all__ = [name for name in globals() if not name.startswith("__")]
