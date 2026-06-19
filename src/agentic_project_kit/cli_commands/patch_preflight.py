from __future__ import annotations

import json
from pathlib import Path

import typer

from agentic_project_kit.patch_preflight import (
    build_patch_preflight_report,
    render_patch_preflight_report,
)


def patch_preflight_command(
    root: Path = typer.Option(Path("."), "--root"),
    label: str = typer.Option("patch", "--label"),
    base_ref: str = typer.Option("HEAD", "--base-ref"),
    max_files: int = typer.Option(6, "--max-files"),
    max_diff_lines: int = typer.Option(400, "--max-diff-lines"),
    strict: bool = typer.Option(False, "--strict"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Diagnose patch size, protected paths, and diff-risk before closeout."""
    report = build_patch_preflight_report(
        root.resolve(),
        label=label,
        base_ref=base_ref,
        max_files=max_files,
        max_diff_lines=max_diff_lines,
        strict=strict,
    )
    if json_output:
        typer.echo(json.dumps(report.as_dict(), indent=2, sort_keys=True))
    else:
        typer.echo(render_patch_preflight_report(report), nl=False)
    if not report.ok:
        raise typer.Exit(code=1)
