from __future__ import annotations

import json
from pathlib import Path

import typer

from agentic_project_kit.context_budget import PACKET_DIR, PROFILES, context_report, render_context_report, render_packet

context_app = typer.Typer(help="Measure successor context and render task-specific context packets.")


@context_app.command("report")
def context_report_command(
    root: Path = typer.Option(Path("."), "--root", help="Repository root."),
    json_output: bool = typer.Option(False, "--json", help="Print machine-readable JSON."),
) -> None:
    """Measure the successor's required reads (baseline) and each task packet, read-only."""
    report = context_report(root.resolve())
    typer.echo(json.dumps(report, indent=2, sort_keys=True) if json_output else render_context_report(report))


@context_app.command("render")
def context_render_command(
    profile: str = typer.Option(..., "--profile", help=f"Task profile: {', '.join(sorted(PROFILES))}."),
    root: Path = typer.Option(Path("."), "--root", help="Repository root."),
    write: bool = typer.Option(False, "--write", help=f"Also write the packet to {PACKET_DIR.as_posix()}/<profile>.md (git-ignored)."),
) -> None:
    """Render a deterministic task-specific context packet from repository authorities."""
    repository = root.resolve()
    try:
        text = render_packet(repository, profile)
    except KeyError as exc:
        typer.echo(str(exc.args[0]))
        raise typer.Exit(code=2) from exc
    if write:
        path = repository / PACKET_DIR / f"{profile}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    typer.echo(text)
