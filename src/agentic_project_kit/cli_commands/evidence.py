from __future__ import annotations

from pathlib import Path

import typer

from agentic_project_kit.evidence_guard import check_terminal_log
from agentic_project_kit.evidence_clean import check_clean_except_expected_log

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

@app.command("clean-check")
def clean_check(expected_log: str = typer.Argument(...), root: Path = typer.Option(Path("."), "--root")) -> None:
    """Pass when git status is clean except one expected in-progress log."""
    result = check_clean_except_expected_log(root.resolve(), expected_log)
    if result.ok:
        typer.echo("PASS: worktree clean except expected log: " + result.expected_log)
        return
    typer.echo("FAIL: worktree dirty beyond expected log: " + result.expected_log)
    for line in result.unexpected_lines:
        typer.echo(line)
    raise typer.Exit(code=1)

