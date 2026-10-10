"""Thin CLI boundary for workspace-owned Kit installation maintenance."""

from __future__ import annotations

import json
from pathlib import Path

import typer

from agentic_project_kit.kit_installation import installation_status
from agentic_project_kit.kit_update import run_kit_update


kit_app = typer.Typer(help="Inspect and update the Kit installed in an external workspace.")


def _emit(payload: dict, json_output: bool) -> None:
    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        typer.echo(f"KIT\nSTATUS={payload['result_status']}")
        if payload.get("approval_signature"):
            typer.echo(f"APPROVAL_SIGNATURE={payload['approval_signature']}")
        if payload.get("changed_paths"):
            typer.echo("CHANGED_PATHS=" + ", ".join(payload["changed_paths"]))
        if payload.get("blocker"):
            typer.echo("BLOCKER=" + payload["blocker"])
        typer.echo("NEXT_ACTION=" + payload["next_action"])
    if payload["result_status"] == "BLOCKED":
        raise typer.Exit(2)


def _error(exc: Exception) -> dict:
    return {
        "result_status": "BLOCKED",
        "blocker": str(exc),
        "next_action": "Inspect workspace configuration and update evidence, then obtain a fresh plan.",
    }


@kit_app.command("status")
def status(
    root: Path = typer.Option(Path("."), "--root", help="Workspace root."),
    json_output: bool = typer.Option(False, "--json", help="Emit one JSON document."),
) -> None:
    """Verify the workspace-owned Kit interpreter and installation without global PATH guesses."""
    try:
        payload = installation_status(root.resolve())
    except (OSError, RuntimeError, ValueError) as exc:
        payload = _error(exc)
    _emit(payload, json_output)


@kit_app.command("update")
def update(
    version: str = typer.Option(
        ..., "--version", help="Exact released stable Kit version (X.Y.Z)."
    ),
    root: Path = typer.Option(Path("."), "--root", help="External workspace on a work branch."),
    execute: bool = typer.Option(
        False, "--execute", help="Execute the exactly signed update plan."
    ),
    expected_signature: str = typer.Option(
        "", "--expected-signature", help="Approval signature from the current dry run."
    ),
    json_output: bool = typer.Option(False, "--json", help="Emit one JSON document."),
) -> None:
    """Plan a released Kit update; signed execution installs locally, updates CI pins and checks the workspace."""
    try:
        payload = run_kit_update(
            root, version, execute=execute, expected_signature=expected_signature
        )
    except (OSError, RuntimeError, ValueError) as exc:
        payload = _error(exc)
    _emit(payload, json_output)
