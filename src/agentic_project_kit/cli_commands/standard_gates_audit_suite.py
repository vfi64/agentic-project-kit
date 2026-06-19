from __future__ import annotations

import json
from pathlib import Path

import typer

from agentic_project_kit import __version__ as PACKAGE_VERSION
from agentic_project_kit.standard_gates_audit_suite import (
    evaluate_standard_gates_audit_suite,
    render_standard_gates_audit_suite,
)


def standard_gates_audit_suite_command(
    root: Path = typer.Option(Path("."), "--root"),
    version: str = typer.Option(PACKAGE_VERSION, "--version"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Run the audit suite required by standard project gates."""
    result = evaluate_standard_gates_audit_suite(root.resolve(), version=version)
    if json_output:
        typer.echo(json.dumps(result.as_dict(), indent=2, sort_keys=True))
    else:
        typer.echo(render_standard_gates_audit_suite(result), nl=False)
    if not result.ok:
        raise typer.Exit(code=result.returncode)
