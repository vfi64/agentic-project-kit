from __future__ import annotations

import json
from pathlib import Path

import typer

from agentic_project_kit.ns_legacy_reference_audit import (
    audit_ns_legacy_references,
    render_ns_legacy_reference_audit,
)


def audit_ns_legacy_references_command(
    root: Path = typer.Option(Path("."), "--root"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Audit remaining legacy ./ns/ns-menu/ns_release references."""
    result = audit_ns_legacy_references(root.resolve())
    if json_output:
        typer.echo(json.dumps(result.as_dict(), indent=2, sort_keys=True))
    else:
        typer.echo(render_ns_legacy_reference_audit(result), nl=False)
    if not result.ok:
        raise typer.Exit(code=result.returncode)
