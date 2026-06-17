from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer

from agentic_project_kit.removed_ns_commands import (
    build_removed_ns_command_report,
    write_markdown_report,
)

app = typer.Typer(help="Diagnose ns commands removed between release refs.")


@app.command("diagnose-removed-ns-commands")
def diagnose_removed_ns_commands(
    old: str = typer.Option("0.4.6", "--old", help="Old release tag/ref."),
    new: str = typer.Option("0.4.8", "--new", help="New release tag/ref."),
    json_out: Optional[Path] = typer.Option(None, "--json-out", help="Write machine-readable report."),
    md_out: Optional[Path] = typer.Option(None, "--md-out", help="Write Markdown report."),
    json_output: bool = typer.Option(False, "--json", help="Print full JSON report to stdout."),
) -> None:
    """Diagnose ns command definitions/usages removed or reduced between release refs."""
    report = build_removed_ns_command_report(old=old, new=new)

    if json_out is not None:
        json_out.parent.mkdir(parents=True, exist_ok=True)
        json_out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if md_out is not None:
        md_out.parent.mkdir(parents=True, exist_ok=True)
        write_markdown_report(report, md_out)

    if json_output:
        typer.echo(json.dumps(report, indent=2, ensure_ascii=False))
        return

    typer.echo("REMOVED_NS_COMMAND_DIAGNOSIS")
    typer.echo(f"old_ref={report['old_ref']}")
    typer.echo(f"new_ref={report['new_ref']}")
    typer.echo(f"old_commit={report['old_commit']}")
    typer.echo(f"new_commit={report['new_commit']}")
    typer.echo("candidate_commands:")
    for item in report["candidate_commands"][:40]:
        typer.echo(
            "- {name}: old={old_count} new={new_count} main={main_count} "
            "removed_or_decreased={signal}".format(
                name=item["name"],
                old_count=item["evidence_count_old"],
                new_count=item["evidence_count_new"],
                main_count=item["evidence_count_main"],
                signal=item["removed_or_decreased_signal"],
            )
        )
    if json_out is not None:
        typer.echo(f"json_out={json_out}")
    if md_out is not None:
        typer.echo(f"md_out={md_out}")
    typer.echo("RESULT=REMOVED_NS_COMMAND_DIAGNOSIS_DONE")


def register_removed_ns_commands(transfer_app: typer.Typer) -> None:
    transfer_app.add_typer(app)
