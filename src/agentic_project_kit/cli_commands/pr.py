from __future__ import annotations

import json
from pathlib import Path

import typer

from agentic_project_kit.ci_readiness import (
    WAITING,
    gh_pr_snapshot_provider,
    render_pr_readiness,
    wait_for_pr_readiness,
)
from agentic_project_kit.next_turn_merge_if_green import main_verification_passed, merge_if_green, render_result
from agentic_project_kit.next_turn_pr_status import (
    attach_failed_run_logs,
    classify_pr_status,
    fetch_pr_payload,
    render_decision,
)
from agentic_project_kit.pr_closeout import BLOCKED, evaluate_pr_closeout, render_pr_closeout

pr_app = typer.Typer(help="Evaluate deterministic PR closeout and readiness state.")


@pr_app.command("closeout-check")
def closeout_check(json_file: Path) -> None:
    data = json.loads(json_file.read_text(encoding="utf-8"))
    result = evaluate_pr_closeout(data)
    typer.echo(render_pr_closeout(result))
    if result.outcome == BLOCKED:
        raise typer.Exit(code=1)


@pr_app.command("status")
def status(
    pr_number: int = typer.Argument(..., help="Pull request number to inspect."),
    json_output: bool = typer.Option(False, "--json", help="Print JSON instead of the text report."),
    no_failed_log_fetch: bool = typer.Option(
        False,
        "--no-failed-log-fetch",
        help="Do not fetch failed GitHub Actions logs for red checks.",
    ),
    failed_log_lines: int = typer.Option(120, min=0, help="Maximum failed-log excerpt lines."),
) -> None:
    """Print deterministic PR/CI status and fetch failed logs for red CI."""
    payload = fetch_pr_payload(str(pr_number))
    decision = classify_pr_status(payload, pr=str(pr_number))
    if decision.decision == "red" and not no_failed_log_fetch:
        decision = attach_failed_run_logs(decision, max_lines=failed_log_lines)
    if json_output:
        typer.echo(json.dumps(decision, default=lambda item: item.__dict__, indent=2, sort_keys=True))
    else:
        typer.echo(render_decision(decision))


@pr_app.command("merge-if-green")
def merge_if_green_command(
    pr_number: int = typer.Argument(..., help="Pull request number to merge only after green checks."),
    merge_method: str = typer.Option(
        "squash",
        help="GitHub merge method: squash, merge, or rebase.",
    ),
    delete_branch: bool = typer.Option(True, help="Delete the branch after a successful merge."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Evaluate without merging."),
    no_verify_main: bool = typer.Option(False, "--no-verify-main", help="Do not verify main CI after merge."),
    main_branch: str = typer.Option("main", help="Expected base branch and post-merge verification branch."),
    expected_base_branch: str = typer.Option("", help="Expected PR base branch. Defaults to --main-branch."),
    expected_head_sha: str = typer.Option("", help="Expected PR head SHA. Refuses merge if the head moved."),
    main_ci_timeout_seconds: int = typer.Option(300, min=1, help="Post-merge main CI wait timeout."),
    main_ci_poll_seconds: int = typer.Option(10, min=1, help="Post-merge main CI polling interval."),
) -> None:
    """Merge only when PR checks are green, refs match, and merge state is clean."""
    result = merge_if_green(
        str(pr_number),
        merge_method=merge_method,
        delete_branch=delete_branch,
        dry_run=dry_run,
        verify_main=not no_verify_main,
        main_branch=main_branch,
        expected_base_branch=expected_base_branch,
        expected_head_sha=expected_head_sha,
        main_ci_timeout_seconds=main_ci_timeout_seconds,
        main_ci_poll_seconds=main_ci_poll_seconds,
    )
    typer.echo(render_result(result))
    if dry_run:
        return
    if result.decision != "merge" or not result.merged or not main_verification_passed(result):
        raise typer.Exit(code=1)


@pr_app.command("wait-ci")
def wait_ci(
    pr_number: int = typer.Argument(..., help="Pull request number to inspect."),
    expected_head_sha: str | None = typer.Option(
        None,
        "--expected-head-sha",
        help="Expected PR head SHA for --expected-head-sha. The command fails closed if the head moves.",
    ),
    timeout_seconds: int = typer.Option(2700, min=1, help="Maximum wait time."),
    interval_seconds: int = typer.Option(20, min=1, help="Polling interval."),
    expected_check: list[str] = typer.Option(
        [],
        "--expected-check",
        help="Check name that must be present before readiness can pass. Repeatable.",
    ),
) -> None:
    """Wait for pull-request CI; guard merge preparation with --expected-head-sha."""
    result = wait_for_pr_readiness(
        gh_pr_snapshot_provider(pr_number),
        expected_head_sha=expected_head_sha,
        timeout_seconds=timeout_seconds,
        interval_seconds=interval_seconds,
        expected_checks=tuple(expected_check),
    )
    typer.echo(render_pr_readiness(result))
    if not result.success:
        raise typer.Exit(code=2 if result.outcome == WAITING else 1)


def register_pr_closeout_alias(app: typer.Typer) -> None:
    @app.command("pr-closeout")
    def pr_closeout_alias(json_file: Path) -> None:
        data = json.loads(json_file.read_text(encoding="utf-8"))
        result = evaluate_pr_closeout(data)
        typer.echo(render_pr_closeout(result))
        if result.outcome == BLOCKED:
            raise typer.Exit(code=1)
