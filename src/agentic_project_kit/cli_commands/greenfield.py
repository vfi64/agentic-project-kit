"""Thin public adapters for finding evidence."""

import json
from pathlib import Path
import typer
from agentic_project_kit.greenfield_status import export, read_status

greenfield_app = typer.Typer(
    help="Read Kit adjudications and executable external retest contracts."
)


def emit(call, json_output):
    try:
        result = call()
    except (ValueError, OSError, KeyError, TypeError, RuntimeError) as exc:
        typer.echo(json.dumps({"result_status": "BLOCKED", "error": str(exc)}, sort_keys=True))
        raise typer.Exit(2)
    typer.echo(json.dumps(result, indent=2, sort_keys=True) if json_output else str(result))


@greenfield_app.command("status")
def status(
    finding_id: str = typer.Option("", "--id"), json_output: bool = typer.Option(False, "--json")
):
    """Read the installed Kit's public adjudications; never change a consumer ledger."""
    emit(lambda: read_status(finding_id), json_output)


@greenfield_app.command("export")
def export_command(
    root: Path = typer.Option(Path("."), "--root"),
    execute: bool = typer.Option(False, "--execute"),
    expected_signature: str = typer.Option("", "--expected-signature"),
    json_output: bool = typer.Option(False, "--json"),
):
    """Plan or sign the Kit maintainer's deterministic local status projections."""
    emit(lambda: export(root, execute=execute, expected_signature=expected_signature), json_output)


@greenfield_app.command("retest")
def retest_command(
    finding_ids: list[str] = typer.Option([], "--id", help="Finding id; repeatable."),
    run_all: bool = typer.Option(False, "--all", help="Retest every finding of the installed Kit."),
    json_output: bool = typer.Option(False, "--json"),
):
    """Run the installed Kit's machine retests in a temporary workspace; never touch this workspace."""
    from agentic_project_kit.greenfield_retest import exit_code, retest

    try:
        result = retest(finding_ids, run_all=run_all)
    except (ValueError, OSError, KeyError, TypeError, RuntimeError) as exc:
        typer.echo(json.dumps({"result_status": "BLOCKED", "error": str(exc)}, sort_keys=True))
        raise typer.Exit(2)
    if json_output:
        typer.echo(json.dumps(result, indent=2, sort_keys=True))
    else:
        typer.echo(f"greenfield retest: {result['result_status']} {json.dumps(result['counts'], sort_keys=True)}")
        for record in result["results"]:
            typer.echo(f"- {record['id']}: {record['result']} ({record['execution_class']})")
    raise typer.Exit(exit_code(result))
