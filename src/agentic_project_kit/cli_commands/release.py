from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from agentic_project_kit.post_release import build_post_release_report, render_post_release_report
from agentic_project_kit.release import (
    build_release_plan,
    build_release_preflight_report,
    build_release_state_report,
    render_release_plan,
    render_release_preflight_report,
    render_release_state_report,
)

console = Console()


def register_release_commands(app: typer.Typer) -> None:
    app.command("release-plan")(release_plan_command)
    app.command("release-preflight")(release_preflight_command)
    app.command("release-check")(release_check_command)
    app.command("post-release-check")(post_release_check_command)


def release_plan_command(
    project_root: Path = typer.Option(Path("."), "--root"),
    version: str | None = typer.Option(None, "--version", help="Release version without leading v."),
) -> None:
    """Print a release preparation checklist for the current project."""
    plan = build_release_plan(project_root.resolve(), version=version)
    console.print(render_release_plan(plan), markup=False)


def release_preflight_command(
    version: str = typer.Option(..., "--version", help="Target release version without leading v."),
) -> None:
    """Validate before-metadata release readiness for a target version."""
    raise typer.Exit(code=run_release_preflight(version))


def run_release_preflight(version: str) -> int:
    """Validate the before-metadata release phase for a target version.

    This intentionally does not require project files to already contain the
    target version. That is the job of release-check after metadata is patched.
    """
    report = build_release_preflight_report(Path(".").resolve(), version=version)
    console.print(render_release_preflight_report(report), markup=False)
    return 0 if report.ok else 1


def release_check_command(
    project_root: Path = typer.Option(Path("."), "--root"),
    version: str | None = typer.Option(None, "--version", help="Release version without leading v."),
) -> None:
    """Validate release state for a target version."""
    report = build_release_state_report(project_root.resolve(), version=version)
    console.print(render_release_state_report(report), markup=False)
    if not report.ok:
        raise typer.Exit(code=1)


def post_release_check_command(
    project_root: Path = typer.Option(Path("."), "--root"),
    version: str | None = typer.Option(None, "--version", help="Release version without leading v."),
) -> None:
    """Validate post-release GitHub and Zenodo state without guessing DOI metadata."""
    report = build_post_release_report(project_root.resolve(), version=version)
    console.print(render_post_release_report(report), markup=False)
    if not report.ok:
        raise typer.Exit(code=1)
