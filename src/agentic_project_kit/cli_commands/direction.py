from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

import typer

from agentic_project_kit.project_direction import (
    audit_project_direction_drift,
    load_project_direction,
    render_direction_drift_audit,
    render_direction_validation,
    render_project_direction,
    validate_project_direction,
)

direction_app = typer.Typer(help="Validate, render, and audit project direction state.")

Section = Literal["all", "strategy", "roadmap", "plans", "ideas", "done", "discarded"]
OutputFormat = Literal["text", "markdown", "json"]


@direction_app.command("validate")
def direction_validate_command(
    root: Path = typer.Option(Path("."), "--root", help="Repository root."),
    strict_planning_files: bool = typer.Option(
        False,
        "--strict-planning-files",
        help="Fail when free docs/planning files are not canonical files or listed sources.",
    ),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    """Validate docs/planning/PROJECT_DIRECTION.yaml."""
    result = validate_project_direction(root, strict_planning_files=strict_planning_files)
    if json_output:
        typer.echo(json.dumps(result.as_dict(), indent=2, sort_keys=True))
    else:
        typer.echo(render_direction_validation(result), nl=False)
    if not result.ok:
        raise typer.Exit(code=result.returncode)


@direction_app.command("render")
def direction_render_command(
    root: Path = typer.Option(Path("."), "--root", help="Repository root."),
    section: Section = typer.Option(
        "all",
        "--section",
        help="all, strategy, roadmap, plans, ideas, done, or discarded.",
    ),
    output_format: OutputFormat = typer.Option("text", "--format", help="text, markdown, or json."),
    output: Path | None = typer.Option(
        None,
        "--output",
        help="Optional tmp/*.md, tmp/*.txt, or tmp/*.json output path.",
    ),
) -> None:
    """Render project direction without overwriting committed projections."""
    rendered = render_project_direction(
        load_project_direction(root),
        section=section,
        output_format=output_format,
    )
    if output is None:
        typer.echo(rendered, nl=False)
        return

    root_path = root.resolve()
    output_path = output if output.is_absolute() else root_path / output
    try:
        relative = output_path.resolve().relative_to(root_path)
    except ValueError as exc:
        raise typer.BadParameter("output must stay inside the repository") from exc
    if not relative.as_posix().startswith("tmp/"):
        raise typer.BadParameter("output must be under tmp/")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered, encoding="utf-8")
    typer.echo(f"PROJECT_DIRECTION_RENDER\nSTATUS=PASS\nOUTPUT={relative.as_posix()}")


@direction_app.command("audit-drift")
def direction_audit_drift_command(
    root: Path = typer.Option(Path("."), "--root", help="Repository root."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    """Report planning files that are not yet represented in project direction."""
    result = audit_project_direction_drift(root)
    if json_output:
        typer.echo(json.dumps(result.as_dict(), indent=2, sort_keys=True))
    else:
        typer.echo(render_direction_drift_audit(result), nl=False)
