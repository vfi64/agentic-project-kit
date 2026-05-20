from __future__ import annotations

from pathlib import Path

import typer

from agentic_project_kit.evidence_guard import check_terminal_log

app = typer.Typer(help="Validate terminal evidence logs.")


@app.command("guard")
def guard(logfile: Path) -> None:
    """Fail if a terminal evidence log has contradictory final state."""
    result = check_terminal_log(logfile)
    status = "PASS" if result.ok else "FAIL"
    typer.echo(f"{status}: {result.path} final_result={result.final_result}")
    for finding in result.findings:
        typer.echo(f"  - {finding}")
    if not result.ok:
        raise typer.Exit(1)
