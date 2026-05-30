from __future__ import annotations

import json
from pathlib import Path

import typer

from agentic_project_kit.transfer_closeout import closeout_transfer
from agentic_project_kit.transfer_local_runner import run_local_transfer
from agentic_project_kit.transfer_pr_actions import pr_status_transfer
from agentic_project_kit.transfer_remote_next import run_remote_next_transfer
from agentic_project_kit.transfer_repo_actions import (
    branch_create,
    branch_delete,
    branch_switch,
    commit_paths,
    fetch_origin,
    head_sha,
    pr_create,
    pr_merge_safe,
    pr_wait_ci,
    post_merge_check,
    pull_current,
    push_current,
    repo_diff,
    repo_log,
    repo_status,
    result_json,
)
from agentic_project_kit.transfer_runner import (
    DEFAULT_INBOX,
    apply_transfer_order,
    inspect_transfer_order,
    load_transfer_order,
    transfer_result_as_json_data,
)
from agentic_project_kit.transfer_state import build_transfer_state

transfer_app = typer.Typer(help="Inspect and apply repo-backed text transfer orders.")


def _load_or_exit(path: Path):
    try:
        return load_transfer_order(path)
    except (FileNotFoundError, ValueError) as exc:
        typer.echo(str(exc))
        raise typer.Exit(code=1) from exc


def _emit_result(result, json_output: bool) -> None:
    if json_output:
        typer.echo(json.dumps(transfer_result_as_json_data(result), indent=2, sort_keys=True))
    else:
        typer.echo(f"transfer_id={result.transfer_id}")
        typer.echo(f"result_status={result.result_status}")
        typer.echo(f"returncode={result.returncode}")
        typer.echo(f"report_path={result.report_path}")
        typer.echo(f"message={result.message}")


@transfer_app.command("closeout")
def closeout(
    no_remove_transfer_dir: bool = typer.Option(
        False,
        "--no-remove-transfer-dir",
        help="Do not remove .agentic/transfer during closeout.",
    ),
    json_output: bool = typer.Option(True, "--json/--no-json", help="Print machine-readable JSON."),
) -> None:
    try:
        result = closeout_transfer(Path("."), remove_transfer_dir=not no_remove_transfer_dir)
    except RuntimeError as exc:
        typer.echo(str(exc))
        raise typer.Exit(code=1) from exc

    if json_output:
        typer.echo(json.dumps(result.as_json_data(), indent=2, sort_keys=True))
    else:
        typer.echo(f"result_status={result.result_status}")
        typer.echo(f"returncode={result.returncode}")
        typer.echo(f"removed_transfer_dir={result.removed_transfer_dir}")
        typer.echo(f"latest_command_run_path={result.latest_command_run_path}")
        typer.echo(f"blocked_dirty_paths={','.join(result.blocked_dirty_paths)}")
        typer.echo(f"next_action={result.next_action}")

    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)


@transfer_app.command("remote-next")
def remote_next(
    branch: str = typer.Argument(..., help="Remote transfer branch to fetch, switch to, pull, and run."),
    json_output: bool = typer.Option(True, "--json/--no-json", help="Print machine-readable JSON."),
) -> None:
    try:
        result = run_remote_next_transfer(Path("."), branch)
    except (RuntimeError, ValueError, FileNotFoundError) as exc:
        typer.echo(str(exc))
        raise typer.Exit(code=1) from exc

    if json_output:
        typer.echo(json.dumps(result.as_json_data(), indent=2, sort_keys=True))
    else:
        typer.echo(f"branch={result.branch}")
        typer.echo(f"head={result.head}")
        typer.echo(f"result_status={result.local_run.result_status}")
        typer.echo(f"returncode={result.local_run.returncode}")
        typer.echo(f"next_action={result.local_run.next_action}")

    if result.local_run.returncode != 0:
        raise typer.Exit(code=result.local_run.returncode)



@transfer_app.command("repo-status")
def repo_status_command(
    short: bool = typer.Option(True, "--short/--full", help="Use short git status by default."),
    json_output: bool = typer.Option(False, "--json", help="Print JSON instead of text."),
) -> None:
    result = repo_status(short=short)
    typer.echo(result_json(result))
    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)


@transfer_app.command("repo-log")
def repo_log_command(
    limit: int = typer.Option(5, "--limit", "-n", min=1, help="Number of commits to show."),
    json_output: bool = typer.Option(False, "--json", help="Print JSON instead of text."),
) -> None:
    result = repo_log(limit=limit)
    typer.echo(result_json(result))
    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)


@transfer_app.command("head-sha")
def head_sha_command(
    full: bool = typer.Option(False, "--full", help="Print the full HEAD SHA instead of the short SHA."),
    json_output: bool = typer.Option(False, "--json", help="Print JSON instead of text."),
) -> None:
    result = head_sha(full=full)
    typer.echo(result_json(result))
    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)


@transfer_app.command("repo-diff")
def repo_diff_command(
    cached: bool = typer.Option(False, "--cached", help="Show staged diff."),
    name_only: bool = typer.Option(False, "--name-only", help="Show only changed path names."),
    json_output: bool = typer.Option(False, "--json", help="Print JSON instead of text."),
) -> None:
    result = repo_diff(cached=cached, name_only=name_only)
    typer.echo(result_json(result))
    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)


@transfer_app.command("fetch-origin")
def fetch_origin_command(
    branch: str = typer.Option("main", "--branch", help="Remote branch to fetch from origin."),
    json_output: bool = typer.Option(False, "--json", help="Print JSON instead of text."),
) -> None:
    result = fetch_origin(branch)
    typer.echo(result_json(result))
    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)


@transfer_app.command("pull-current")
def pull_current_command(
    json_output: bool = typer.Option(False, "--json", help="Print JSON instead of text."),
) -> None:
    result = pull_current()
    typer.echo(result_json(result))
    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)


@transfer_app.command("branch-delete")
def branch_delete_command(
    branch: str = typer.Argument(..., help="Branch name to delete."),
    remote: bool = typer.Option(False, "--remote", help="Delete branch on origin instead of locally."),
    force: bool = typer.Option(False, "--force", help="Force local branch deletion with -D."),
    json_output: bool = typer.Option(False, "--json", help="Print JSON instead of text."),
) -> None:
    result = branch_delete(branch, remote=remote, force=force)
    typer.echo(result_json(result))
    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)


@transfer_app.command("pr-wait-ci")
def pr_wait_ci_command(
    pr_number: int = typer.Argument(..., help="Pull request number to wait for."),
    expected_head_sha: str = typer.Option("", "--expected-head-sha", help="Expected PR head SHA."),
    timeout_seconds: int = typer.Option(300, "--timeout-seconds", min=1, help="Maximum wait time."),
    poll_seconds: int = typer.Option(10, "--interval-seconds", "--poll-seconds", min=1, help="Polling interval."),
    json_output: bool = typer.Option(False, "--json", help="Print JSON instead of text."),
) -> None:
    result = pr_wait_ci(
        pr_number,
        expected_head_sha=expected_head_sha,
        timeout_seconds=timeout_seconds,
        poll_seconds=poll_seconds,
    )
    typer.echo(result_json(result))
    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)


@transfer_app.command("pr-merge-safe")
def pr_merge_safe_command(
    pr_number: int = typer.Argument(..., help="Pull request number to merge safely."),
    expected_head_sha: str = typer.Option(..., "--expected-head-sha", help="Expected PR head SHA."),
    main_branch: str = typer.Option("main", "--main-branch", help="Expected base branch."),
    merge_method: str = typer.Option("squash", "--merge-method", help="GitHub merge method."),
    no_verify_main: bool = typer.Option(False, "--no-verify-main", help="Skip post-merge main verification."),
    json_output: bool = typer.Option(False, "--json", help="Print JSON instead of text."),
) -> None:
    result = pr_merge_safe(
        pr_number,
        expected_head_sha=expected_head_sha,
        main_branch=main_branch,
        merge_method=merge_method,
        no_verify_main=no_verify_main,
    )
    typer.echo(result_json(result))
    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)


@transfer_app.command("post-merge-check")
def post_merge_check_command(
    main_branch: str = typer.Option("main", "--main-branch", help="Expected current branch after merge."),
    json_output: bool = typer.Option(False, "--json", help="Print JSON instead of text."),
) -> None:
    result = post_merge_check(main_branch=main_branch)
    typer.echo(result_json(result))
    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)


@transfer_app.command("branch-create")
def branch_create_command(
    branch: str = typer.Argument(..., help="Branch name to create."),
    start_point: str = typer.Option("main", help="Start point for the new branch."),
    push: bool = typer.Option(False, "--push", help="Push the new branch and set upstream."),
    json_output: bool = typer.Option(False, "--json", help="Print JSON instead of text."),
) -> None:
    result = branch_create(branch, start_point=start_point, push=push)
    if json_output:
        typer.echo(result_json(result))
    else:
        typer.echo(result_json(result))
    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)


@transfer_app.command("branch-switch")
def branch_switch_command(
    branch: str = typer.Argument(..., help="Branch name to switch to."),
    pull: bool = typer.Option(False, "--pull", help="Fast-forward pull from origin after switching."),
    json_output: bool = typer.Option(False, "--json", help="Print JSON instead of text."),
) -> None:
    result = branch_switch(branch, pull=pull)
    if json_output:
        typer.echo(result_json(result))
    else:
        typer.echo(result_json(result))
    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)


@transfer_app.command("commit")
def commit_command(
    message: str = typer.Option(..., "--message", "-m", help="Commit message."),
    path: list[str] = typer.Option([], "--path", help="Path to add before commit. Repeatable."),
    json_output: bool = typer.Option(False, "--json", help="Print JSON instead of text."),
) -> None:
    result = commit_paths(message, list(path))
    if json_output:
        typer.echo(result_json(result))
    else:
        typer.echo(result_json(result))
    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)


@transfer_app.command("push-current")
def push_current_command(
    json_output: bool = typer.Option(False, "--json", help="Print JSON instead of text."),
) -> None:
    result = push_current()
    if json_output:
        typer.echo(result_json(result))
    else:
        typer.echo(result_json(result))
    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)


@transfer_app.command("pr-create")
def pr_create_command(
    base: str = typer.Option("main", "--base", help="Base branch."),
    head: str = typer.Option(..., "--head", help="Head branch."),
    title: str = typer.Option(..., "--title", help="Pull request title."),
    body: str = typer.Option("", "--body", help="Pull request body."),
    json_output: bool = typer.Option(False, "--json", help="Print JSON instead of text."),
) -> None:
    result = pr_create(base=base, head=head, title=title, body=body)
    if json_output:
        typer.echo(result_json(result))
    else:
        typer.echo(result_json(result))
    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)


@transfer_app.command("pr-status")
def pr_status_command(
    pr_number: int = typer.Argument(..., help="Pull request number to inspect through the transfer wrapper."),
    json_output: bool = typer.Option(False, "--json", help="Print JSON instead of text report."),
    no_failed_log_fetch: bool = typer.Option(
        False,
        "--no-failed-log-fetch",
        help="Do not fetch failed GitHub Actions logs for red checks.",
    ),
    failed_log_lines: int = typer.Option(120, min=0, help="Maximum failed-log excerpt lines."),
    expected_head_sha: str = typer.Option("", "--expected-head-sha", help="Expected full PR head SHA."),
) -> None:
    result = pr_status_transfer(
        pr_number,
        no_failed_log_fetch=no_failed_log_fetch,
        failed_log_lines=failed_log_lines,
        expected_head_sha=expected_head_sha,
    )
    if json_output:
        typer.echo(json.dumps(result.as_json_data(), indent=2, sort_keys=True))
    else:
        typer.echo(result.report)
    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)


@transfer_app.command("run-local")
def run_local(
    path: Path = typer.Option(DEFAULT_INBOX, "--path", help="Transfer order path."),
    json_output: bool = typer.Option(True, "--json/--no-json", help="Print machine-readable JSON."),
) -> None:
    try:
        result = run_local_transfer(Path("."), path)
    except (FileNotFoundError, ValueError) as exc:
        typer.echo(str(exc))
        raise typer.Exit(code=1) from exc

    if json_output:
        typer.echo(json.dumps(result.as_json_data(), indent=2, sort_keys=True))
    else:
        typer.echo(f"transfer_id={result.transfer_id}")
        typer.echo(f"result_status={result.result_status}")
        typer.echo(f"returncode={result.returncode}")
        typer.echo(f"next_action={result.next_action}")

    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)


@transfer_app.command("state")
def state(
    json_output: bool = typer.Option(True, "--json/--no-json", help="Print machine-readable JSON."),
) -> None:
    snapshot = build_transfer_state(Path("."))
    data = snapshot.as_json_data()
    if json_output:
        typer.echo(json.dumps(data, indent=2, sort_keys=True))
    else:
        typer.echo(f"primary_state={snapshot.primary_state}")
        typer.echo(f"next_action={snapshot.next_action}")


@transfer_app.command("status")
def status(
    path: Path = typer.Option(DEFAULT_INBOX, "--path", help="Transfer order path."),
    json_output: bool = typer.Option(False, "--json", help="Print machine-readable JSON."),
) -> None:
    order = _load_or_exit(path)
    result = inspect_transfer_order(order, Path("."))
    _emit_result(result, json_output)
    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)


@transfer_app.command("inspect")
def inspect(
    path: Path = typer.Option(DEFAULT_INBOX, "--path", help="Transfer order path."),
    json_output: bool = typer.Option(False, "--json", help="Print machine-readable JSON."),
) -> None:
    order = _load_or_exit(path)
    result = inspect_transfer_order(order, Path("."))
    _emit_result(result, json_output)
    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)


@transfer_app.command("apply")
def apply(
    path: Path = typer.Option(DEFAULT_INBOX, "--path", help="Transfer order path."),
    json_output: bool = typer.Option(False, "--json", help="Print machine-readable JSON."),
) -> None:
    order = _load_or_exit(path)
    result = apply_transfer_order(order, Path("."))
    _emit_result(result, json_output)
    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)
