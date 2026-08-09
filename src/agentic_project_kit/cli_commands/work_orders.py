from __future__ import annotations

import json
from pathlib import Path

import typer

from agentic_project_kit.typed_work_order_queue import (
    inspect_typed_work_order_queue,
    render_typed_work_order_queue_status,
    run_typed_next,
    typed_next_result_as_json_data,
    typed_work_order_queue_status_as_json_data,
)
from agentic_project_kit.typed_work_order_runner import (
    load_typed_work_order,
    run_typed_work_order,
    typed_work_order_result_as_json_data,
)
from agentic_project_kit.work_orders import (
    check_work_orders,
    list_work_order_templates,
    list_work_orders,
    load_work_order,
    prepare_work_order,
    render_work_order,
    run_work_order,
)
from agentic_project_kit.work_order_uploader import (
    render_work_order_upload_result,
    upload_next_turn_result_log,
)

work_orders_app = typer.Typer(help="Inspect and run repo-backed work orders.")


@work_orders_app.command("list")
def list_command() -> None:
    for order in list_work_orders():
        typer.echo(f"{order.work_order_id}\t{order.safety}\t{order.title}")


@work_orders_app.command("show")
def show_command(work_order_id: str) -> None:
    try:
        order = load_work_order(work_order_id)
    except (FileNotFoundError, ValueError) as exc:
        typer.echo(str(exc))
        raise typer.Exit(code=1) from exc
    typer.echo(render_work_order(order))


@work_orders_app.command("check")
def check_command() -> None:
    errors = check_work_orders()
    if errors:
        for error in errors:
            typer.echo(f"[FAIL] {error}")
        raise typer.Exit(code=1)
    typer.echo("Work order contract check passed")


@work_orders_app.command("run")
def run_command(work_order_id: str, execute: bool = typer.Option(False, "--execute", help="Actually run the work order. Omit for dry-run.")) -> None:
    try:
        order = load_work_order(work_order_id)
    except (FileNotFoundError, ValueError) as exc:
        typer.echo(str(exc))
        raise typer.Exit(code=1) from exc
    typer.echo(render_work_order(order))
    if not execute:
        typer.echo("Dry run only. Re-run with --execute to run the command.")
        return
    result_code = run_work_order(order)
    typer.echo(f"Work order log written: {order.log_path}")
    if result_code != 0:
        raise typer.Exit(code=result_code)




@work_orders_app.command("typed-next")
def typed_next_command(
    json_output: bool = typer.Option(False, "--json", help="Print machine-readable JSON result."),
) -> None:
    result = run_typed_next(Path("."))
    data = typed_next_result_as_json_data(result)
    if json_output:
        typer.echo(json.dumps(data, indent=2, sort_keys=True))
    else:
        typer.echo(f"typed_next_status={result.result_status}")
        typer.echo(f"queue_status={result.queue_status}")
        typer.echo(f"message={result.message}")
        if result.terminal_log:
            typer.echo(f"terminal_log={result.terminal_log}")
    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)


@work_orders_app.command("typed-queue-status")
def typed_queue_status_command(
    inbox_path: Path = typer.Option(Path(".agentic/typed_work_orders/inbox"), "--inbox", help="Typed work order inbox directory."),
    json_output: bool = typer.Option(False, "--json", help="Print machine-readable JSON queue status."),
) -> None:
    try:
        status = inspect_typed_work_order_queue(inbox_path)
    except ValueError as exc:
        typer.echo(str(exc))
        raise typer.Exit(code=2) from exc
    if json_output:
        typer.echo(json.dumps(typed_work_order_queue_status_as_json_data(status), indent=2, sort_keys=True))
    else:
        typer.echo(render_typed_work_order_queue_status(status))
    if status.status == "multiple_commands":
        raise typer.Exit(code=2)


@work_orders_app.command("typed-run")
def typed_run_command(
    work_order_path: Path,
    execute: bool = typer.Option(False, "--execute", help="Actually run the typed work order. Omit for dry-run."),
    json_output: bool = typer.Option(False, "--json", help="Print machine-readable JSON result."),
) -> None:
    try:
        order = load_typed_work_order(work_order_path)
    except (FileNotFoundError, ValueError) as exc:
        typer.echo(str(exc))
        raise typer.Exit(code=1) from exc
    if not execute:
        typer.echo(f"Typed work order: {order.work_order_id}")
        typer.echo(f"Safety: {order.safety}")
        typer.echo(f"Steps: {len(order.steps)}")
        typer.echo("Dry run only. Re-run with --execute to run the typed work order.")
        return
    result = run_typed_work_order(order, Path("."))
    data = typed_work_order_result_as_json_data(result)
    if json_output:
        typer.echo(json.dumps(data, indent=2, sort_keys=True))
    else:
        typer.echo(f"Typed work order result: {result.result_status}")
        typer.echo(f"Typed work order log written: {result.terminal_log}")
    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)


@work_orders_app.command("upload")
def upload_command(
    log_path: Path | None = typer.Option(
        None,
        "--log-path",
        help="Repository evidence log path to commit; defaults to the next-turn result log.",
    ),
    local_log_path: Path | None = typer.Option(
        None,
        "--local-log-path",
        help="Local result log to promote before committing.",
    ),
    commit_message: str = typer.Option(
        "Upload next-turn result log",
        "--commit-message",
        help="Commit message for the bounded result-log upload.",
    ),
    required_branch: str = typer.Option(
        "",
        "--required-branch",
        help="Require the current branch to match this value before committing.",
    ),
    allow_main: bool = typer.Option(
        False,
        "--allow-main",
        help="Allow committing on main; reserved for explicit maintainer-controlled recovery.",
    ),
    json_output: bool = typer.Option(False, "--json", help="Print machine-readable JSON result."),
) -> None:
    result = upload_next_turn_result_log(
        log_path=log_path,
        local_log_path=local_log_path,
        commit_message=commit_message,
        required_branch=required_branch,
        allow_main=allow_main,
    )
    if json_output:
        typer.echo(
            json.dumps(
                {
                    "schema_version": 1,
                    "kind": "work_order_upload_result",
                    "ok": result.ok,
                    "committed": result.committed,
                    "pushed": result.pushed,
                    "returncode": result.returncode,
                    "log_path": str(result.log_path),
                    "message": result.message,
                    "commit_sha": result.commit_sha,
                },
                indent=2,
                sort_keys=True,
            )
        )
    else:
        typer.echo(render_work_order_upload_result(result))
    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)


@work_orders_app.command("templates")
def templates() -> None:
    for template_id in list_work_order_templates():
        typer.echo(template_id)


@work_orders_app.command("prepare")
def prepare(template_id: str, work_order_id: str, expected_branch: str) -> None:
    try:
        path = prepare_work_order(template_id, work_order_id, expected_branch)
    except (FileNotFoundError, ValueError) as exc:
        typer.echo(str(exc))
        raise typer.Exit(code=1) from exc
    typer.echo(f"Prepared work order: {path}")
