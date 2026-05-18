from __future__ import annotations

import typer

from agentic_project_kit.work_orders import check_work_orders, load_work_order, list_work_orders, render_work_order, run_work_order

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
