from __future__ import annotations

import json
from pathlib import Path

import typer

from agentic_project_kit.invocation_ledger import (
    find_repository_root,
    ledger_report,
    ledger_typer_class,
    render_ledger_report,
    write_finding_drafts,
)

ledger_app = typer.Typer(help="Read the local invocation ledger of Kit commands.")


def kit_root_app(**kwargs: object) -> typer.Typer:
    """Root ``agentic-kit`` app: records process starts and carries the ``ledger`` group."""
    root = ledger_typer_class()(**kwargs)
    root.add_typer(ledger_app, name="ledger")
    return root


@ledger_app.command("report")
def ledger_report_command(
    root: Path = typer.Option(Path("."), "--root", help="Repository root or a path inside it."),
    days: int = typer.Option(0, "--days", help="Only records of the last N days; 0 reads all."),
    json_output: bool = typer.Option(False, "--json", help="Print machine-readable JSON."),
    write_finding_drafts_flag: bool = typer.Option(
        False,
        "--write-finding-drafts",
        help="Write a local finding draft per new repeated-failure fingerprint; existing drafts are kept.",
    ),
) -> None:
    """Summarise the local invocation ledger: counts, nesting, failures, work cycles and repeated failures."""
    repository = find_repository_root(root) or root.resolve()
    report = ledger_report(repository, since_days=days or None)
    if write_finding_drafts_flag:
        report["finding_drafts_written"] = write_finding_drafts(repository, report["repeated_failures"])
    if json_output:
        typer.echo(json.dumps(report, indent=2, sort_keys=True))
    else:
        typer.echo(render_ledger_report(report))
