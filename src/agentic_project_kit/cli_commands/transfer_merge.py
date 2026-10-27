"""Thin CLI adapter for the local, explicitly approved merge lifecycle."""
import json
from pathlib import Path

import typer

from .transfer_shared import transfer_app, _require_transfer_capability
from agentic_project_kit.transfer_merge import merge_upstream


@transfer_app.command("merge-upstream")
def merge_upstream_command(
    branch: str = typer.Option(..., "--branch", help="Expected current work branch; main is refused."),
    upstream: str = typer.Option("origin/main", "--upstream", help="Already fetched origin ref; never fetched or pushed here."),
    continue_merge: bool = typer.Option(False, "--continue", help="Preview/finish the resolved active merge."),
    abort: bool = typer.Option(False, "--abort", help="Preview/discard tracked progress of the active merge; preserve untracked files."),
    execute: bool = typer.Option(False, "--execute", help="Execute one approved action; preview is the default."),
    expected_signature: str = typer.Option("", "--expected-signature", help="Approval signature from this action's preview."),
    json_output: bool = typer.Option(False, "--json", help="Print the same structured result as JSON."),
) -> None:
    """Merge a fetched upstream locally, preserve conflicts, then explicitly continue or abort."""
    if execute:
        _require_transfer_capability("rules_confirmed", json_output=json_output)
    if continue_merge and abort:
        payload = {"result_status": "BLOCKED", "returncode": 2, "reasons": ["mutually_exclusive_actions"],
                   "next_safe_action": "Select only one of start, continue or abort."}
    else:
        payload = merge_upstream(Path.cwd(), branch=branch, upstream=upstream,
                                 action="continue" if continue_merge else "abort" if abort else "start",
                                 execute=execute, expected_signature=expected_signature)
    # Keep text/JSON information identical, including explicit non-PASS stop states.
    if not json_output:
        typer.echo("TRANSFER_MERGE_UPSTREAM")
    typer.echo(json.dumps(payload, indent=2, sort_keys=True))
    if payload["returncode"]:
        raise typer.Exit(payload["returncode"])
