from __future__ import annotations

from pathlib import Path

import typer

from agentic_project_kit.evidence_clean import check_clean_except_expected_log, clean_local_evidence
from agentic_project_kit.evidence_guard import check_change_scope
from agentic_project_kit.evidence_guard import check_terminal_log
from agentic_project_kit.evidence_inspector import inspect_evidence
from agentic_project_kit.evidence_inspector import render_evidence_inspection

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


@app.command("inspect")
def inspect(
    path: Path | None = typer.Argument(None),
    root: Path = typer.Option(Path("."), "--root"),
    require_summary: bool = typer.Option(False, "--require-summary"),
) -> None:
    """Inspect explicit or latest terminal evidence before continuing after chat control signals."""
    result = inspect_evidence(path, root=root, require_summary=require_summary)
    typer.echo(render_evidence_inspection(result))
    if not result.success:
        raise typer.Exit(code=1)


@app.command("scope-check")
def scope_check(
    changed: list[str] = typer.Option([], "--changed", help="Changed repository path. Repeat for multiple paths."),
    expected: list[str] = typer.Option([], "--expected", help="Expected target path. Repeat for multiple paths."),
) -> None:
    """Fail if expected target paths are missing from a change set."""
    result = check_change_scope(changed_paths=changed, expected_paths=expected)
    status = "PASS" if result.ok else "FAIL"
    typer.echo(f"{status}: change scope check")
    typer.echo("changed_paths=" + ", ".join(result.changed_paths))
    typer.echo("expected_paths=" + ", ".join(result.expected_paths))
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


@app.command("clean")
def clean(root: Path = typer.Option(Path("."), "--root")) -> None:
    """Clean local evidence according to repo policy."""
    result = clean_local_evidence(root.resolve())

    typer.echo("\n\n\n")
    typer.echo("-------------------------------------------------------------------------")
    typer.echo("-------------------------------------------------------------------------")
    typer.echo("-------------------------------------------------------------------------")
    typer.echo("\n\n\n")
    typer.echo("NS CLEAN EVIDENCE")

    typer.echo("\n### SAFETY ###")
    typer.echo(
        "Safety: removes ignored tmp evidence and restores known tracked workflow evidence only; "
        "does not delete arbitrary docs/reports files."
    )

    typer.echo("\n### BEFORE STATUS ###")
    if result.before_status:
        for line in result.before_status:
            typer.echo(line)
    else:
        typer.echo("clean")

    typer.echo("\n### RESTORE KNOWN TRACKED WORKFLOW EVIDENCE ###")
    for line in result.restore_lines:
        typer.echo(line)

    typer.echo("\n### REMOVE IGNORED TMP EVIDENCE ###")
    if result.removed_tmp_evidence:
        typer.echo("remove_ignored_dir=tmp/agent-evidence")
    else:
        typer.echo("no_ignored_tmp_evidence=tmp/agent-evidence")

    typer.echo("\n### UNTRACKED DOC REPORTS REVIEW ###")
    if result.untracked_doc_reports:
        for line in result.untracked_doc_reports:
            typer.echo(line)
        typer.echo("NEEDS_HUMAN_REVIEW: untracked docs/reports files were not deleted automatically.")
    else:
        typer.echo("No untracked docs/reports files found.")

    if result.errors:
        typer.echo("\n### ERRORS ###")
        for line in result.errors:
            typer.echo(line)

    typer.echo("\n### AFTER STATUS ###")
    if result.after_status:
        for line in result.after_status:
            typer.echo(line)
    else:
        typer.echo("clean")

    if result.ok:
        typer.echo("\n### RESULT: PASS ###")
        return
    typer.echo("\n### RESULT: FAIL ###")
    raise typer.Exit(code=1)
