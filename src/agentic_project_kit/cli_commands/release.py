from __future__ import annotations

from pathlib import Path
import json

import typer
from rich.console import Console

from agentic_project_kit.post_release import build_post_release_report, render_post_release_report
from agentic_project_kit.release_state import check_release_state
from agentic_project_kit.release_prepare import prepare_release_state
from agentic_project_kit.post_release_closeout import post_release_doi_closeout, render_post_release_doi_closeout_result
from agentic_project_kit.release import (
    ReleaseCheckStatus,
    build_release_plan,
    build_release_preflight_report,
    build_release_state_report,
    render_release_plan,
    render_release_preflight_report,
    render_release_state_report,
)

console = Console()


release_app = typer.Typer(help="Release preparation and validation commands.")


def register_release_commands(app: typer.Typer) -> None:
    app.command("release-plan")(release_plan_command)
    app.command("release-preflight")(release_preflight_command)
    app.command("release-check")(release_check_command)
    app.command("post-release-check")(post_release_check_command)
    app.command("post-release-doi-closeout")(post_release_doi_closeout_command)
    app.add_typer(release_app, name="release")


def release_plan_command(
    project_root: Path = typer.Option(Path("."), "--root"),
    version: str | None = typer.Option(None, "--version", help="Release version without leading v."),
) -> None:
    """Print a release preparation checklist for the current project."""
    root = project_root.resolve()
    if version is None:
        current_version = build_release_plan(root).version
        current_report = build_release_preflight_report(root, version=current_version)
        already_released = any(
            check.status == ReleaseCheckStatus.FAIL
            for check in current_report.checks
            if check.name in {"remote tag unused", "GitHub release unused"}
        )
        if already_released:
            console.print(
                "Current package version is already released. "
                "Pass the next target explicitly, for example: "
                "agentic-kit release-plan --version <next-version>",
                markup=False,
            )
            raise typer.Exit(code=2)
    plan = build_release_plan(root, version=version)
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


def post_release_doi_closeout_command(
    project_root: Path = typer.Option(Path("."), "--root"),
    version: str = typer.Option(..., "--version", help="Release version without leading v."),
    write: bool = typer.Option(False, "--write", help="Write verified DOI metadata updates."),
) -> None:
    result = post_release_doi_closeout(project_root.resolve(), version=version, write=write)
    console.print(render_post_release_doi_closeout_result(result), markup=False)
    if not result.ok:
        raise typer.Exit(code=result.returncode)

@release_app.command("prepare")
def release_prepare_subcommand(
    version: str = typer.Option(
        ...,
        "--version",
        help="Target release version without leading v.",
    ),
    date: str = typer.Option(
        ...,
        "--date",
        help="Release date in YYYY-MM-DD format.",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show planned file changes without writing them.",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Print machine-readable JSON output.",
    ),
) -> None:
    """Prepare release metadata files without publishing anything."""
    result = prepare_release_state(version=version, date=date, dry_run=dry_run)
    payload = result.as_dict()
    if json_output:
        console.print(json.dumps(payload, indent=2, sort_keys=True), markup=False)
        return
    mode = "DRY-RUN" if dry_run else "WRITE"
    console.print(f"Release prepare: version={version} date={date} mode={mode}", markup=False)
    if result.changed_paths:
        for changed_path in result.changed_paths:
            console.print(f"CHANGED: {changed_path}", markup=False)
    else:
        console.print("NOOP: release metadata already matches target state", markup=False)


@release_app.command("check")
def release_check_subcommand(
    version: str | None = typer.Option(
        None,
        "--version",
        help="Expected prepared release version. Defaults to pyproject.toml.",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Print machine-readable JSON output.",
    ),
) -> None:
    """Check prepared release-state anchors without mutating the repository."""
    result = check_release_state(expected_version=version)
    payload = result.as_dict()
    if json_output:
        console.print(json.dumps(payload, indent=2, sort_keys=True), markup=False)
    else:
        console.print(f"Release state check: version={result.version}", markup=False)
        for finding in result.findings:
            console.print(f"PASS: {finding}", markup=False)
        for error in result.errors:
            console.print(f"FAIL: {error}", markup=False)
    if not result.ok:
        raise typer.Exit(1)

