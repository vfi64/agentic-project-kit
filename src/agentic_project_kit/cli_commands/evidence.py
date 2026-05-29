from __future__ import annotations

from pathlib import Path

import typer

from agentic_project_kit.evidence_clean import check_clean_except_expected_log, clean_local_evidence
from agentic_project_kit.evidence_finalize_log import finalize_log
from agentic_project_kit.evidence_finalize_log import render_finalize_log_error
from agentic_project_kit.evidence_finalize_log import render_finalize_log_result
from agentic_project_kit.evidence_guard import check_change_scope
from agentic_project_kit.evidence_guard import check_terminal_log
from agentic_project_kit.evidence_inspector import classify_log
from agentic_project_kit.evidence_inspector import inspect_evidence
from agentic_project_kit.evidence_inspector import render_evidence_inspection
from agentic_project_kit.evidence_inspector import render_log_classification

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


@app.command("classify-log")
def classify_log_command(
    path: Path | None = typer.Argument(None),
    root: Path = typer.Option(Path("."), "--root"),
    require_summary: bool = typer.Option(False, "--require-summary"),
    ignore_git_status: bool = typer.Option(False, "--ignore-git-status"),
) -> None:
    """Classify a terminal/evidence log for deterministic gatekeeper decisions."""
    result = classify_log(
        path,
        root=root,
        require_summary=require_summary,
        check_git_status=not ignore_git_status,
    )
    typer.echo(render_log_classification(result))
    if not result.success:
        raise typer.Exit(code=1)


@app.command("finalize-log")
def finalize_log_command(
    run_log: Path = typer.Option(..., "--run-log"),
    remote_log: Path = typer.Option(..., "--remote-log"),
    slice_name: str = typer.Option(..., "--slice"),
    scope: str = typer.Option(..., "--scope"),
    mode_check: str = typer.Option(..., "--mode-check"),
    work: str = typer.Option("PASS", "--work"),
    evidence: str = typer.Option("PASS", "--evidence"),
    overall: str = typer.Option("PASS", "--overall"),
    remote_evidence: str = typer.Option("NOT_REQUIRED", "--remote-evidence"),
    pr: str = typer.Option("NONE", "--pr"),
    ci: str = typer.Option("not-required", "--ci"),
    merge: str = typer.Option("not-required", "--merge"),
    command_report: str = typer.Option(..., "--command-report"),
    interpretation: str = typer.Option(..., "--interpretation"),
    safe_step: str = typer.Option(..., "--safe-step"),
    chat_reply: str = typer.Option("d", "--next"),
    origin: str = typer.Option("local", "--origin"),
    state_mode: str = typer.Option("local", "--state-mode"),
    comm_id: str = typer.Option("COMM-LOCAL", "--comm-id"),
    commit_message: str | None = typer.Option(None, "--commit-message"),
    push: bool = typer.Option(False, "--push"),
    root: Path = typer.Option(Path("."), "--root"),
) -> None:
    """Append a canonical summary, require strict inspection, then upload the evidence log."""
    try:
        result = finalize_log(
            root=root,
            run_log=run_log,
            remote_log=remote_log,
            slice_name=slice_name,
            scope=scope,
            mode_check=mode_check,
            work=work,
            evidence=evidence,
            overall=overall,
            remote_evidence=remote_evidence,
            pr=pr,
            ci=ci,
            merge=merge,
            command_report=command_report,
            interpretation=interpretation,
            safe_step=safe_step,
            chat_reply=chat_reply,
            origin=origin,
            state_mode=state_mode,
            comm_id=comm_id,
            commit_message=commit_message,
            push=push,
        )
    except (ValueError, FileNotFoundError) as exc:
        typer.echo(render_finalize_log_error(str(exc)))
        raise typer.Exit(code=1) from None
    typer.echo(render_finalize_log_result(result))
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
