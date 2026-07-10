from __future__ import annotations

import json

import typer

from agentic_project_kit.mutation_lock_audit import (
    audit_mutation_lock_coverage,
    render_mutation_lock_coverage_audit,
)


def register_mutation_lock_audit_command(app: typer.Typer) -> None:
    @app.command("audit-mutation-lock-coverage")
    def audit_mutation_lock_coverage_command(
        json_output: bool = typer.Option(False, "--json", help="Emit JSON output."),
    ) -> None:
        """Audit mutating entrypoints for workspace mutation-lock coverage."""
        result = audit_mutation_lock_coverage(".")
        if json_output:
            typer.echo(json.dumps(result.to_dict(), indent=2, sort_keys=True))
        else:
            typer.echo(render_mutation_lock_coverage_audit(result), nl=False)
        raise typer.Exit(result.returncode)
