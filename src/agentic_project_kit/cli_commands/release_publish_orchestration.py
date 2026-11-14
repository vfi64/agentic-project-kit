from __future__ import annotations

from pathlib import Path

import typer

from agentic_project_kit import __version__ as PACKAGE_VERSION
from agentic_project_kit.blocked_route import first_line
from agentic_project_kit.cli_commands.routed_output import emit_routed, human_reason
from agentic_project_kit.release_publish_orchestration import (
    evaluate_release_publish_plan,
    render_release_publish_plan,
)


def release_publish_command(
    version: str = typer.Option(PACKAGE_VERSION, "--version"),
    dry_run: bool = typer.Option(True, "--dry-run/--no-dry-run"),
    execute: bool = typer.Option(False, "--execute"),
    allow_execute: bool = typer.Option(False, "--allow-execute"),
    expected_signature: str = typer.Option("", "--expected-signature"),
    root: Path = typer.Option(Path("."), "--root"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Plan release publishing without live tag/release side effects."""
    plan = evaluate_release_publish_plan(
        root.resolve(),
        version=version,
        dry_run=dry_run,
        execute=execute,
        allow_execute=allow_execute,
        expected_signature=expected_signature,
    )
    payload = {**plan.as_dict(), "result_status": plan.status}
    if not plan.ok:
        first = plan.blockers[0]
        payload.update(human_reason(
            f"release-publish has {len(plan.blockers)} blocker(s), first {first.name}: "
            f"{first_line(first.detail) or 'no detail'}"
        ))
    emit_routed(payload, json_output=json_output, text=render_release_publish_plan(plan))
    if not plan.ok:
        raise typer.Exit(code=plan.returncode)
