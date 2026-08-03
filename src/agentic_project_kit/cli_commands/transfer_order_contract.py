from __future__ import annotations

from pathlib import Path

import typer

from agentic_project_kit.remote_next_order_contract import (
    create_remote_next_order,
    remote_next_order_result_json,
    render_remote_next_order_result,
    validate_remote_next_order,
)
from agentic_project_kit.transfer_runner import DEFAULT_INBOX

from .transfer_shared import transfer_app


@transfer_app.command("order-create")
def remote_next_order_create_command(
    branch: str = typer.Option(..., "--branch", help="Safe remote-next transfer branch."),
    write_actions: list[str] = typer.Option(
        [],
        "--write-action",
        help="Write action in target_path=payload_path form. Repeatable.",
    ),
    path: Path = typer.Option(DEFAULT_INBOX, "--path", help="Transfer order path."),
    order_id: str = typer.Option("", "--id", help="Transfer order id. Defaults to branch and HEAD."),
    title: str = typer.Option("", "--title", help="Transfer order title."),
    safety: str = typer.Option("", "--safety", help="Transfer order safety label."),
    report_path: str = typer.Option("", "--report-path", help="Bounded command-run report path."),
    status: str = typer.Option("active", "--status", help="Remote-next order status."),
    execute: bool = typer.Option(False, "--execute", help="Write the transfer order file."),
    allow_overwrite: bool = typer.Option(
        False,
        "--allow-overwrite",
        help="Allow replacing an existing transfer order file.",
    ),
    json_output: bool = typer.Option(False, "--json", help="Print machine-readable JSON."),
) -> None:
    """Generate a head-anchored executable remote-next transfer order."""
    result = create_remote_next_order(
        Path("."),
        branch=branch,
        write_actions=tuple(write_actions),
        path=path,
        order_id=order_id,
        title=title,
        safety=safety,
        report_path=report_path,
        status=status,
        execute=execute,
        allow_overwrite=allow_overwrite,
    )
    if json_output:
        typer.echo(remote_next_order_result_json(result))
    else:
        typer.echo(render_remote_next_order_result(result), nl=False)
    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)


@transfer_app.command("order-validate")
def remote_next_order_validate_command(
    path: Path = typer.Option(DEFAULT_INBOX, "--path", help="Transfer order path."),
    json_output: bool = typer.Option(False, "--json", help="Print machine-readable JSON."),
) -> None:
    """Validate a remote-next transfer order without mutating the repository."""
    result = validate_remote_next_order(Path("."), path=path)
    if json_output:
        typer.echo(remote_next_order_result_json(result))
    else:
        typer.echo(render_remote_next_order_result(result), nl=False)
    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)
