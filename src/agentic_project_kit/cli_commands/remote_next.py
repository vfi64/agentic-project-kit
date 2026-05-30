from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from agentic_project_kit.remote_next import (
    remote_next_result_as_json_data,
    render_remote_next_result,
    run_remote_next,
)
from agentic_project_kit.remote_next_closeout import (
    render_remote_next_closeout_result,
    run_remote_next_closeout,
)


def register_remote_next_command(app: typer.Typer) -> None:
    @app.command("remote-next")
    def remote_next_command(
        project_root: Annotated[Path, typer.Option("--root")] = Path("."),
        json_output: Annotated[bool, typer.Option("--json", help="Print machine-readable JSON result.")] = False,
    ) -> None:
        result = run_remote_next(project_root)
        if json_output:
            typer.echo(json.dumps(remote_next_result_as_json_data(result), indent=2, sort_keys=True))
        else:
            typer.echo(render_remote_next_result(result))
        if result.returncode != 0:
            raise typer.Exit(code=result.returncode)

    @app.command("rn")
    def rn_command(
        project_root: Annotated[Path, typer.Option("--root")] = Path("."),
        json_output: Annotated[bool, typer.Option("--json", help="Print machine-readable JSON result.")] = False,
    ) -> None:
        result = run_remote_next(project_root)
        if json_output:
            typer.echo(json.dumps(remote_next_result_as_json_data(result), indent=2, sort_keys=True))
        else:
            typer.echo(render_remote_next_result(result))
        if result.returncode != 0:
            raise typer.Exit(code=result.returncode)

    @app.command("rnc")
    def rnc_command(
        project_root: Annotated[Path, typer.Option("--root")] = Path("."),
        no_push: Annotated[bool, typer.Option("--no-push", help="Commit locally without pushing.")] = False,
    ) -> None:
        result = run_remote_next_closeout(project_root, push=not no_push)
        typer.echo(render_remote_next_closeout_result(result))
        if result.status == "no_closeout":
            raise typer.Exit(code=2)
        if not result.success:
            raise typer.Exit(code=1)
