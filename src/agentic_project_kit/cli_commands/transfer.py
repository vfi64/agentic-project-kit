from __future__ import annotations

import json
from pathlib import Path

import typer

from agentic_project_kit.transfer_closeout import closeout_transfer
from agentic_project_kit.transfer_local_runner import run_local_transfer
from agentic_project_kit.transfer_pr_actions import pr_status_transfer
from agentic_project_kit.transfer_remote_next import run_remote_next_transfer
from agentic_project_kit.transfer_repo_actions import branch_create, branch_switch, commit_paths, pr_create, push_current, result_json
from agentic_project_kit.transfer_runner import (
    DEFAULT_INBOX,
    apply_transfer_order,
    inspect_transfer_order,
    load_transfer_order,
    transfer_result_as_json_data,
)
from agentic_project_kit.transfer_state import build_transfer_state

transfer_app = typer.Typer(help="Inspect and apply repo-backed text transfer orders.")


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


@transfer_app.command("remote-next")
def remote_next(
    branch: str = typer.Argument(..., help="Remote transfer branch to fetch, switch to, pull, and run."),
    json_output: bool = typer.Option(True, "--json/--no-json", help="Print machine-readable JSON."),
) -> None:
    try:
        result = run_remote_next_transfer(Path("."), branch)
    except (RuntimeError, ValueError, FileNotFoundError) as exc:
        typer.echo(str(exc))
        raise typer.Exit(code=1) from exc

    if json_output:
        typer.echo(json.dumps(result.as_json_data(), indent=2, sort_keys=True))
    else:
        typer.echo(f"branch={result.branch}")
        typer.echo(f"head={result.head}")
        typer.echo(f"result_status={result.local_run.result_status}")
        typer.echo(f"returncode={result.local_run.returncode}")
        typer.echo(f"next_action={result.local_run.next_action}")

    if result.local_run.returncode != 0:
        raise typer.Exit(code=result.local_run.returncode)



@transfer_app.command("branch-create")
def branch_create_command(
    branch: str = typer.Argument(..., help="Branch name to create."),
    start_point: str = typer.Option("main", help="Start point for the new branch."),
    push: bool = typer.Option(False, "--push", help="Push the new branch and set upstream."),
    json_output: bool = typer.Option(False, "--json", help="Print JSON instead of text."),
) -> None:
    result = branch_create(branch, start_point=start_point, push=push)
    if json_output:
        typer.echo(result_json(result))
    else:
        typer.echo(result_json(result))
    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)


@transfer_app.command("branch-switch")
def branch_switch_command(
    branch: str = typer.Argument(..., help="Branch name to switch to."),
    pull: bool = typer.Option(False, "--pull", help="Fast-forward pull from origin after switching."),
    json_output: bool = typer.Option(False, "--json", help="Print JSON instead of text."),
) -> None:
    result = branch_switch(branch, pull=pull)
    if json_output:
        typer.echo(result_json(result))
    else:
        typer.echo(result_json(result))
    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)


@transfer_app.command("commit")
def commit_command(
    message: str = typer.Option(..., "--message", "-m", help="Commit message."),
    path: list[str] = typer.Option([], "--path", help="Path to add before commit. Repeatable."),
    json_output: bool = typer.Option(False, "--json", help="Print JSON instead of text."),
) -> None:
    result = commit_paths(message, list(path))
    if json_output:
        typer.echo(result_json(result))
    else:
        typer.echo(result_json(result))
    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)


@transfer_app.command("push-current")
def push_current_command(
    json_output: bool = typer.Option(False, "--json", help="Print JSON instead of text."),
) -> None:
    result = push_current()
    if json_output:
        typer.echo(result_json(result))
    else:
        typer.echo(result_json(result))
    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)


@transfer_app.command("pr-create")
def pr_create_command(
    base: str = typer.Option("main", "--base", help="Base branch."),
    head: str = typer.Option(..., "--head", help="Head branch."),
    title: str = typer.Option(..., "--title", help="Pull request title."),
    body: str = typer.Option("", "--body", help="Pull request body."),
    json_output: bool = typer.Option(False, "--json", help="Print JSON instead of text."),
) -> None:
    result = pr_create(base=base, head=head, title=title, body=body)
    if json_output:
        typer.echo(result_json(result))
    else:
        typer.echo(result_json(result))
    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)


@transfer_app.command("pr-status")
def pr_status_command(
    pr_number: int = typer.Argument(..., help="Pull request number to inspect through the transfer wrapper."),
    json_output: bool = typer.Option(False, "--json", help="Print JSON instead of text report."),
    no_failed_log_fetch: bool = typer.Option(
        False,
        "--no-failed-log-fetch",
        help="Do not fetch failed GitHub Actions logs for red checks.",
    ),
    failed_log_lines: int = typer.Option(120, min=0, help="Maximum failed-log excerpt lines."),
) -> None:
    result = pr_status_transfer(
        pr_number,
        no_failed_log_fetch=no_failed_log_fetch,
        failed_log_lines=failed_log_lines,
    )
    if json_output:
        typer.echo(json.dumps(result.as_json_data(), indent=2, sort_keys=True))
    else:
        typer.echo(result.report)
    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)


@transfer_app.command("run-local")
def run_local(
    path: Path = typer.Option(DEFAULT_INBOX, "--path", help="Transfer order path."),
    json_output: bool = typer.Option(True, "--json/--no-json", help="Print machine-readable JSON."),
) -> None:
    try:
        result = run_local_transfer(Path("."), path)
    except (FileNotFoundError, ValueError) as exc:
        typer.echo(str(exc))
        raise typer.Exit(code=1) from exc

    if json_output:
        typer.echo(json.dumps(result.as_json_data(), indent=2, sort_keys=True))
    else:
        typer.echo(f"transfer_id={result.transfer_id}")
        typer.echo(f"result_status={result.result_status}")
        typer.echo(f"returncode={result.returncode}")
        typer.echo(f"next_action={result.next_action}")

    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)


@transfer_app.command("state")
def state(
    json_output: bool = typer.Option(True, "--json/--no-json", help="Print machine-readable JSON."),
) -> None:
    snapshot = build_transfer_state(Path("."))
    data = snapshot.as_json_data()
    if json_output:
        typer.echo(json.dumps(data, indent=2, sort_keys=True))
    else:
        typer.echo(f"primary_state={snapshot.primary_state}")
        typer.echo(f"next_action={snapshot.next_action}")


@transfer_app.command("status")
def status(
    path: Path = typer.Option(DEFAULT_INBOX, "--path", help="Transfer order path."),
    json_output: bool = typer.Option(False, "--json", help="Print machine-readable JSON."),
) -> None:
    order = _load_or_exit(path)
    result = inspect_transfer_order(order, Path("."))
    _emit_result(result, json_output)
    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)


@transfer_app.command("inspect")
def inspect(
    path: Path = typer.Option(DEFAULT_INBOX, "--path", help="Transfer order path."),
    json_output: bool = typer.Option(False, "--json", help="Print machine-readable JSON."),
) -> None:
    order = _load_or_exit(path)
    result = inspect_transfer_order(order, Path("."))
    _emit_result(result, json_output)
    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)


@transfer_app.command("apply")
def apply(
    path: Path = typer.Option(DEFAULT_INBOX, "--path", help="Transfer order path."),
    json_output: bool = typer.Option(False, "--json", help="Print machine-readable JSON."),
) -> None:
    order = _load_or_exit(path)
    result = apply_transfer_order(order, Path("."))
    _emit_result(result, json_output)
    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)
