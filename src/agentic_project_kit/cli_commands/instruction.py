from __future__ import annotations

import json
import sys
from pathlib import Path

import typer

from agentic_project_kit.command_manifest import load_manifest
from agentic_project_kit.instruction_lint import (
    lint_instruction_text,
    render_instruction_lint_result,
)

instruction_app = typer.Typer(help="Lint LLM instruction text before applying it.")


@instruction_app.command("lint")
def instruction_lint_command(
    file_path: Path | None = typer.Option(None, "--file", help="Instruction text file to lint."),
    stdin_input: bool = typer.Option(False, "--stdin", help="Read instruction text from stdin."),
    require_ack: bool = typer.Option(
        True,
        "--require-ack/--no-require-ack",
        help="Require the current COMMAND_MANIFEST_ACK line.",
    ),
    strict_unknown: bool = typer.Option(
        False,
        "--strict-unknown",
        help="Treat unknown raw git/gh commands as blocking.",
    ),
    root: Path = typer.Option(Path("."), "--root", help="Repository root."),
    json_output: bool = typer.Option(False, "--json", help="Print machine-readable JSON."),
) -> None:
    """Lint instruction text against the current command manifest."""
    if (file_path is None) == (not stdin_input):
        typer.echo("Provide exactly one of --file or --stdin.", err=True)
        raise typer.Exit(code=2)
    checked_path = "<stdin>"
    if stdin_input:
        text = sys.stdin.read()
    else:
        assert file_path is not None
        checked_path = str(file_path)
        try:
            text = file_path.read_text(encoding="utf-8")
        except Exception as exc:
            typer.echo(f"Instruction input is unreadable: {exc}", err=True)
            raise typer.Exit(code=2) from exc

    result = lint_instruction_text(
        text,
        manifest=load_manifest(root.resolve()),
        checked_path=checked_path,
        require_ack=require_ack,
        strict_unknown=strict_unknown,
    )
    if json_output:
        typer.echo(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    else:
        typer.echo(render_instruction_lint_result(result), nl=False)
    if result.returncode:
        raise typer.Exit(code=result.returncode)
