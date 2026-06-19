from __future__ import annotations

from pathlib import Path
from typing import Literal

import typer

from agentic_project_kit.project_direction import load_project_direction, render_project_direction

Section = Literal["all", "strategy", "roadmap", "ideas"]
OutputFormat = Literal["text", "markdown", "json"]


def project_direction_command(
    root: Path = typer.Option(Path("."), "--root", help="Repository root."),
    section: Section = typer.Option("all", "--section", help="all, strategy, roadmap, or ideas."),
    output_format: OutputFormat = typer.Option("text", "--format", help="text, markdown, or json."),
) -> None:
    """Render strategy, roadmap, and ideas from the project direction YAML source."""
    direction = load_project_direction(root)
    typer.echo(render_project_direction(direction, section=section, output_format=output_format), nl=False)
