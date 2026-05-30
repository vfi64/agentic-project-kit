from __future__ import annotations

import json
from pathlib import Path

import typer

from agentic_project_kit.transfer_runner import (
    DEFAULT_INBOX,
    apply_transfer_order,
    inspect_transfer_order,
    load_transfer_order,
    transfer_result_as_json_data,
)

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
