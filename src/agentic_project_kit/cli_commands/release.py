from __future__ import annotations

from pathlib import Path
import re
import subprocess

import typer
from rich.console import Console

from agentic_project_kit.post_release import build_post_release_report, render_post_release_report
from agentic_project_kit.release import (
    build_release_plan,
    build_release_state_report,
    render_release_plan,
    render_release_state_report,
)

console = Console()
SEMVER_RE = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+")


def _run_quiet(args: list[str]) -> tuple[int, str]:
    completed = subprocess.run(
        args,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    return completed.returncode, completed.stdout.strip()


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
    tag = "v" + version
    results: list[tuple[str, bool, str]] = []

    valid_version = bool(SEMVER_RE.fullmatch(version))
    if valid_version:
        results.append(("semantic version", True, version + " is valid"))
    else:
        results.append(("semantic version", False, version + " is not valid"))

    code, out = _run_quiet(["git", "tag", "-l", tag])
    local_unused = code == 0 and out == ""
    if local_unused:
        results.append(("local tag unused", True, "tag is unused: " + tag))
    else:
        results.append(("local tag unused", False, "tag already exists locally: " + tag))

    code, out = _run_quiet(["git", "ls-remote", "--tags", "origin", tag])
    remote_unused = code == 0 and out == ""
    if remote_unused:
        results.append(("remote tag unused", True, "remote tag is unused: " + tag))
    else:
        results.append(("remote tag unused", False, "remote tag already exists: " + tag))

    code, _out = _run_quiet(["gh", "release", "view", tag])
    release_absent = code != 0
    if release_absent:
        results.append(("GitHub release unused", True, "GitHub release is absent: " + tag))
    else:
        results.append(("GitHub release unused", False, "GitHub release already exists: " + tag))

    typer.echo("Release preflight for target " + tag)
    typer.echo("")
    for name, passed, detail in results:
        status = "PASS" if passed else "FAIL"
        typer.echo("[" + status + "] " + name + ": " + detail)
    typer.echo("")
    overall = all(passed for _name, passed, _detail in results)
    typer.echo("Overall: " + ("PASS" if overall else "FAIL"))
    return 0 if overall else 1


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
