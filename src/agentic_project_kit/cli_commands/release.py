from __future__ import annotations

from datetime import date as date_cls
import json
import re
from typing import Annotated
from pathlib import Path

import typer
from rich.console import Console

from agentic_project_kit.post_release import build_post_release_report, render_post_release_report
from agentic_project_kit.release_prepare import prepare_release_state
from agentic_project_kit.release_metadata_authority_gate import (
    evaluate_release_metadata_authority_gate,
    render_release_metadata_authority_gate_result,
)
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


def register_release_commands(app: typer.Typer) -> None:
    app.command("release-plan")(release_plan_command)
    app.command("release-preflight")(release_preflight_command)
    app.command("release-prep")(release_prep_command)
    app.command("release-metadata-authority-gate")(release_metadata_authority_gate_command)
    app.command("release-check")(release_check_command)
    app.command("post-release-check")(post_release_check_command)
    app.command("post-release-doi-closeout")(post_release_doi_closeout_command)


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


def release_prep_command(
    project_root: Path = typer.Option(Path("."), "--root"),
    version: str = typer.Option(..., "--version", help="Target release version without leading v."),
    release_date: str | None = typer.Option(
        None,
        "--date",
        help="Release metadata date in YYYY-MM-DD format. Defaults to today.",
    ),
    dry_run: bool = typer.Option(False, "--dry-run", help="Report changed paths without writing files."),
    json_output: bool = typer.Option(False, "--json", help="Print a machine-readable result."),
) -> None:
    """Prepare release metadata through the supported agentic-kit route.

    This edits only local release metadata files. It does not tag, publish,
    push, create GitHub releases, or write Zenodo DOI metadata.
    """
    plain_version = version.removeprefix("v")
    date_value = release_date or date_cls.today().isoformat()
    if not re.fullmatch(r"\d+\.\d+\.\d+", plain_version):
        message = f"Invalid release version: {version!r}; expected MAJOR.MINOR.PATCH"
        if json_output:
            console.print(
                json.dumps(
                    {
                        "ok": False,
                        "version": plain_version,
                        "date": date_value,
                        "dry_run": dry_run,
                        "error": message,
                    },
                    indent=2,
                    sort_keys=True,
                ),
                markup=False,
            )
        else:
            console.print(f"ERROR: {message}", markup=False)
        raise typer.Exit(code=2)

    try:
        result = prepare_release_state(
            project_root.resolve(),
            version=plain_version,
            date=date_value,
            dry_run=dry_run,
        )
    except (FileNotFoundError, ValueError) as exc:
        if json_output:
            console.print(
                json.dumps(
                    {
                        "ok": False,
                        "version": plain_version,
                        "date": date_value,
                        "dry_run": dry_run,
                        "error": str(exc),
                    },
                    indent=2,
                    sort_keys=True,
                ),
                markup=False,
            )
        else:
            console.print(f"ERROR: {exc}", markup=False)
        raise typer.Exit(code=2) from exc

    if json_output:
        console.print(json.dumps(result.as_dict(), indent=2, sort_keys=True), markup=False)
    else:
        mode = "DRY-RUN" if dry_run else "WRITE"
        if result.changed_paths:
            console.print(
                f"{mode}: prepared release metadata for v{result.version} on {result.date}",
                markup=False,
            )
            for changed_path in result.changed_paths:
                console.print(f"CHANGED: {changed_path}", markup=False)
        else:
            console.print(f"{mode}: release metadata already prepared for v{result.version}", markup=False)


def release_metadata_authority_gate_command(
    project_root: Path = typer.Option(Path("."), "--root"),
    base_ref: str = typer.Option("origin/main", "--base-ref", help="Git ref used as the diff base."),
    version: str | None = typer.Option(None, "--version", help="Expected release version without leading v."),
    evidence: Annotated[
        list[Path] | None,
        typer.Option(
            "--evidence",
            help="Authoritative release-prep evidence file. May be passed more than once.",
        ),
    ] = None,
    json_output: bool = typer.Option(False, "--json", help="Print a machine-readable result."),
) -> None:
    """Block manual release metadata anchor edits without release-prep evidence."""
    try:
        result = evaluate_release_metadata_authority_gate(
            project_root.resolve(),
            base_ref=base_ref,
            version=version,
            evidence_paths=evidence or [],
        )
    except (RuntimeError, ValueError) as exc:
        result = None
        if json_output:
            console.print(
                json.dumps(
                    {
                        "ok": False,
                        "status": "BLOCK",
                        "version": version,
                        "base_ref": base_ref,
                        "changed_release_anchor_paths": [],
                        "evidence_paths": [path.as_posix() for path in evidence or []],
                        "message": str(exc),
                    },
                    indent=2,
                    sort_keys=True,
                ),
                markup=False,
            )
        else:
            console.print(f"BLOCK: {exc}", markup=False)
        raise typer.Exit(code=2) from exc

    if json_output:
        console.print(json.dumps(result.as_dict(), indent=2, sort_keys=True), markup=False)
    else:
        console.print(render_release_metadata_authority_gate_result(result), markup=False)

    if not result.ok:
        raise typer.Exit(code=1)


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
    json_output: bool = typer.Option(False, "--json", help="Print a machine-readable result."),
) -> None:
    result = post_release_doi_closeout(project_root.resolve(), version=version, write=write)
    if json_output:
        console.print(json.dumps(result.as_dict(), indent=2, sort_keys=True), markup=False)
    else:
        console.print(render_post_release_doi_closeout_result(result), markup=False)
    if not result.ok:
        raise typer.Exit(code=result.returncode)
