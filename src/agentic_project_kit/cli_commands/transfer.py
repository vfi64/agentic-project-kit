from __future__ import annotations

import json
import shlex
from pathlib import Path

import typer

from agentic_project_kit.transfer_closeout import closeout_transfer
from agentic_project_kit.transfer_local_runner import run_local_transfer
from agentic_project_kit.transfer_pr_actions import pr_status_transfer
from agentic_project_kit.transfer_remote_next import run_remote_next_transfer
from agentic_project_kit.transfer_repo_actions import (
    RepoActionResult,
    admin_refresh_pr,
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
    result_terminal,
)
from agentic_project_kit.transfer_runner import (
    DEFAULT_INBOX,
    apply_transfer_order,
    inspect_transfer_order,
    load_transfer_order,
    transfer_result_as_json_data,
)
from agentic_project_kit.transfer_state import build_transfer_state
from agentic_project_kit.transfer_uplink import (
    publish_latest_transfer_report,
    read_latest_transfer_report,
    run_and_log_transfer_command,
    run_and_log_transfer_sequence,
    write_transfer_report_from_repo_result,
)

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


def _echo_repo_result(result, json_output: bool) -> None:
    typer.echo(result_json(result) if json_output else result_terminal(result))


def _echo_quiet_repo_report(result: RepoActionResult, *, label: str) -> None:
    uplink = write_transfer_report_from_repo_result(result, label=label, cwd=Path("."))
    typer.echo("TRANSFER_UPLOAD=done")
    typer.echo(f"REMOTE_REPORT={uplink.remote_report_path}")
    typer.echo("CHAT_REPLY=g")


def _summary_line(label: str, value: object, *, indent: int = 0, width: int = 24) -> str:
    return f"{' ' * indent}{label + ':':<{width}}{value}"


def _echo_remote_next_user_summary(result) -> None:
    actions = result.post_report_actions or {}
    committed = bool(actions.get("committed"))
    pushed = bool(actions.get("pushed"))
    uploaded = "yes" if pushed else "no_push_failed" if committed else "no_commit_failed"

    typer.echo("*" * 36 + " START SUMMARY " + "*" * 36)
    typer.echo("TRANSFER_REMOTE_NEXT_DONE")
    typer.echo("")
    typer.echo(_summary_line("STATE", result.result_status))
    typer.echo(_summary_line("RETURNCODE", result.returncode))
    typer.echo("")
    typer.echo("REMOTE_REPORT:")
    typer.echo(_summary_line("UPLOADED", uploaded, indent=2))
    typer.echo(_summary_line("COMMITTED", "yes" if committed else "no", indent=2))
    typer.echo(_summary_line("PUSHED", "yes" if pushed else "no", indent=2))
    typer.echo(_summary_line("REPORT_PATH", result.published_report_path, indent=2))
    if actions.get("commit_head"):
        typer.echo(_summary_line("REPORT_COMMIT", actions["commit_head"], indent=2))
    if actions.get("blocked_reason"):
        typer.echo(_summary_line("BLOCKED_REASON", actions["blocked_reason"], indent=2))
    typer.echo("")
    typer.echo("LOCAL:")
    typer.echo(_summary_line("REPORT_PATH", result.report_path, indent=2))
    typer.echo("")
    typer.echo(_summary_line("NEXT", result.next_action))
    typer.echo(_summary_line("CHAT_REPLY", "g"))
    typer.echo("*" * 37 + " END SUMMARY " + "*" * 37)


def _require_transfer_capability(capability: str) -> None:
    snapshot = build_transfer_state(Path("."))
    if snapshot.capabilities.get(capability, False):
        return
    typer.echo(
        json.dumps(
            {
                "chat_reply": "f",
                "next_safe_action": snapshot.next_action,
                "result_status": "BLOCKED",
                "returncode": 2,
                "required_capability": capability,
                "primary_state": snapshot.primary_state,
                "reasons": snapshot.reasons,
                "next_action": snapshot.next_action,
                "rule_acknowledgement": snapshot.rule_acknowledgement,
            },
            indent=2,
            sort_keys=True,
        )
    )
    typer.echo("FINAL_SIGNAL=f")
    typer.echo(f"FINAL_NEXT={snapshot.next_action}")
    typer.echo(f"CHAT_REPLY=f | NEXT={snapshot.next_action}")
    raise typer.Exit(code=2)


@transfer_app.command("run-and-log", context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
def run_and_log(
    ctx: typer.Context,
    label: str = typer.Option("transfer-run", "--label", help="Label for the transfer uplink report."),
    json_output: bool = typer.Option(False, "--json", help="Print JSON instead of text."),
) -> None:
    command = list(ctx.args)
    if command[:1] == ["--"]:
        command = command[1:]
    try:
        result = run_and_log_transfer_command(command, label=label, cwd=Path("."))
    except ValueError as exc:
        typer.echo(str(exc))
        typer.echo("FINAL_SIGNAL=f")
        typer.echo("FINAL_NEXT=Provide a command after run-and-log.")
        typer.echo("CHAT_REPLY=f | NEXT=Provide a command after run-and-log.")
        raise typer.Exit(code=2) from exc

    if json_output:
        typer.echo(json.dumps(result.as_json_data(), indent=2, sort_keys=True))
    else:
        typer.echo("TRANSFER_REPORT_WRITTEN=done")
        typer.echo(f"LOCAL_REPORT={result.remote_report_path}")
        typer.echo("CHAT_REPLY=d | NEXT=Run transfer publish-last-report")

    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)


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
    branch: str | None = typer.Argument(
        None,
        help="Optional remote transfer branch. If omitted, read branch from the transfer order.",
    ),
    json_output: bool = typer.Option(False, "--json/--no-json", help="Print machine-readable JSON."),
) -> None:
    try:
        result = run_remote_next_transfer(Path("."), branch)
    except (RuntimeError, ValueError, FileNotFoundError) as exc:
        typer.echo(str(exc))
        raise typer.Exit(code=1) from exc

    if json_output:
        typer.echo(json.dumps(result.as_json_data(), indent=2, sort_keys=True))
    else:
        _echo_remote_next_user_summary(result)

    if result.local_run.returncode != 0:
        raise typer.Exit(code=result.local_run.returncode)


@transfer_app.command("repo-status")
def repo_status_command(
    short: bool = typer.Option(True, "--short/--full", help="Use short git status by default."),
    json_output: bool = typer.Option(False, "--json", help="Print JSON instead of text."),
) -> None:
    result = repo_status(short=short)
    _echo_repo_result(result, json_output)
    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)


@transfer_app.command("repo-log")
def repo_log_command(
    limit: int = typer.Option(5, "--limit", "-n", min=1, help="Number of commits to show."),
    json_output: bool = typer.Option(False, "--json", help="Print JSON instead of text."),
) -> None:
    result = repo_log(limit=limit)
    _echo_repo_result(result, json_output)
    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)


@transfer_app.command("head-sha")
def head_sha_command(
    full: bool = typer.Option(
        False, "--full", help="Print the full HEAD SHA instead of the short SHA."
    ),
    json_output: bool = typer.Option(False, "--json", help="Print JSON instead of text."),
) -> None:
    result = head_sha(full=full)
    _echo_repo_result(result, json_output)
    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)


@transfer_app.command("repo-diff")
def repo_diff_command(
    cached: bool = typer.Option(False, "--cached", help="Show staged diff."),
    name_only: bool = typer.Option(False, "--name-only", help="Show only changed path names."),
    json_output: bool = typer.Option(False, "--json", help="Print JSON instead of text."),
) -> None:
    result = repo_diff(cached=cached, name_only=name_only)
    _echo_repo_result(result, json_output)
    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)


@transfer_app.command("fetch-origin")
def fetch_origin_command(
    branch: str = typer.Option("main", "--branch", help="Remote branch to fetch from origin."),
    json_output: bool = typer.Option(False, "--json", help="Print JSON instead of text."),
) -> None:
    result = fetch_origin(branch)
    _echo_repo_result(result, json_output)
    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)


@transfer_app.command("pull-current")
def pull_current_command(
    json_output: bool = typer.Option(False, "--json", help="Print JSON instead of text."),
) -> None:
    result = pull_current()
    _echo_repo_result(result, json_output)
    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)


@transfer_app.command("branch-delete")
def branch_delete_command(
    branch: str = typer.Argument(..., help="Branch name to delete."),
    remote: bool = typer.Option(
        False, "--remote", help="Delete branch on origin instead of locally."
    ),
    force: bool = typer.Option(False, "--force", help="Force local branch deletion with -D."),
    json_output: bool = typer.Option(False, "--json", help="Print JSON instead of text."),
) -> None:
    _require_transfer_capability("rules_confirmed")
    result = branch_delete(branch, remote=remote, force=force)
    _echo_repo_result(result, json_output)
    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)


@transfer_app.command("pr-wait-ci")
def pr_wait_ci_command(
    pr_number: int = typer.Argument(..., help="Pull request number to wait for."),
    expected_head_sha: str = typer.Option("", "--expected-head-sha", help="Expected PR head SHA."),
    timeout_seconds: int = typer.Option(300, "--timeout-seconds", min=1, help="Maximum wait time."),
    poll_seconds: int = typer.Option(
        10, "--interval-seconds", "--poll-seconds", min=1, help="Polling interval."
    ),
    quiet_report: bool = typer.Option(
        False,
        "--quiet-report",
        help="Write the detailed wait output to a transfer report and print only go lines.",
    ),
    json_output: bool = typer.Option(False, "--json", help="Print JSON instead of text."),
) -> None:
    result = pr_wait_ci(
        pr_number,
        expected_head_sha=expected_head_sha,
        timeout_seconds=timeout_seconds,
        poll_seconds=poll_seconds,
    )
    if quiet_report and not json_output:
        _echo_quiet_repo_report(result, label=f"pr-wait-ci-{pr_number}")
    else:
        _echo_repo_result(result, json_output)
    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)


@transfer_app.command("pr-merge-safe")
def pr_merge_safe_command(
    pr_number: int = typer.Argument(..., help="Pull request number to merge safely."),
    expected_head_sha: str = typer.Option(
        "",
        "--expected-head-sha",
        help="Expected PR head SHA. If omitted, the PR head SHA is resolved automatically.",
    ),
    main_branch: str = typer.Option("main", "--main-branch", help="Expected base branch."),
    merge_method: str = typer.Option("squash", "--merge-method", help="GitHub merge method."),
    no_verify_main: bool = typer.Option(
        False, "--no-verify-main", help="Skip post-merge main verification."
    ),
    json_output: bool = typer.Option(False, "--json", help="Print JSON instead of text."),
) -> None:
    _require_transfer_capability("rules_confirmed")
    result = pr_merge_safe(
        pr_number,
        expected_head_sha=expected_head_sha,
        main_branch=main_branch,
        merge_method=merge_method,
        no_verify_main=no_verify_main,
    )
    _echo_repo_result(result, json_output)
    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)


@transfer_app.command("post-merge-check")
def post_merge_check_command(
    main_branch: str = typer.Option(
        "main", "--main-branch", help="Expected current branch after merge."
    ),
    json_output: bool = typer.Option(False, "--json", help="Print JSON instead of text."),
) -> None:
    result = post_merge_check(main_branch=main_branch)
    _echo_repo_result(result, json_output)
    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)


@transfer_app.command("admin-refresh-pr")
def admin_refresh_pr_command(
    after_pr: int = typer.Option(
        ..., "--after-pr", help="Merged PR number that requires the administrative handoff refresh."
    ),
    main_branch: str = typer.Option("main", "--main-branch", help="Main branch to refresh from."),
    json_output: bool = typer.Option(False, "--json", help="Print JSON instead of text."),
) -> None:
    _require_transfer_capability("rules_confirmed")
    result = admin_refresh_pr(after_pr, main_branch=main_branch)
    _echo_repo_result(result, json_output)
    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)


@transfer_app.command("branch-create")
def branch_create_command(
    branch: str = typer.Argument(..., help="Branch name to create."),
    start_point: str = typer.Option("main", help="Start point for the new branch."),
    push: bool = typer.Option(False, "--push", help="Push the new branch and set upstream."),
    json_output: bool = typer.Option(False, "--json", help="Print JSON instead of text."),
) -> None:
    _require_transfer_capability("rules_confirmed")
    result = branch_create(branch, start_point=start_point, push=push)
    _echo_repo_result(result, json_output)
    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)


@transfer_app.command("branch-switch")
def branch_switch_command(
    branch: str = typer.Argument(..., help="Branch name to switch to."),
    pull: bool = typer.Option(
        False, "--pull", help="Fast-forward pull from origin after switching."
    ),
    json_output: bool = typer.Option(False, "--json", help="Print JSON instead of text."),
) -> None:
    _require_transfer_capability("rules_confirmed")
    result = branch_switch(branch, pull=pull)
    _echo_repo_result(result, json_output)
    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)


@transfer_app.command("commit")
def commit_command(
    message: str = typer.Option(..., "--message", "-m", help="Commit message."),
    path: list[str] = typer.Option([], "--path", help="Path to add before commit. Repeatable."),
    branch: str = typer.Option(
        "",
        "--branch",
        help="Expected branch for the commit. If set, the transfer monitor switches to it or blocks safely.",
    ),
    allow_main: bool = typer.Option(
        False,
        "--allow-main",
        help="Allow committing directly on main. Use only for explicit emergency/admin flows.",
    ),
    json_output: bool = typer.Option(False, "--json", help="Print JSON instead of text."),
) -> None:
    _require_transfer_capability("rules_confirmed")
    result = commit_paths(message, list(path), allow_main=allow_main, required_branch=branch)
    _echo_repo_result(result, json_output)
    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)


@transfer_app.command("push-current")
def push_current_command(
    branch: str = typer.Option(
        "",
        "--branch",
        help="Expected branch to push. If set, the transfer monitor switches to it or blocks safely.",
    ),
    json_output: bool = typer.Option(False, "--json", help="Print JSON instead of text."),
) -> None:
    _require_transfer_capability("rules_confirmed")
    result = push_current(required_branch=branch)
    _echo_repo_result(result, json_output)
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
    _require_transfer_capability("rules_confirmed")
    result = pr_create(base=base, head=head, title=title, body=body)
    _echo_repo_result(result, json_output)
    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)


@transfer_app.command("pr-status")
def pr_status_command(
    pr_number: int = typer.Argument(
        ..., help="Pull request number to inspect through the transfer wrapper."
    ),
    json_output: bool = typer.Option(False, "--json", help="Print JSON instead of text report."),
    no_failed_log_fetch: bool = typer.Option(
        False,
        "--no-failed-log-fetch",
        help="Do not fetch failed GitHub Actions logs for red checks.",
    ),
    failed_log_lines: int = typer.Option(120, min=0, help="Maximum failed-log excerpt lines."),
    expected_head_sha: str = typer.Option(
        "", "--expected-head-sha", help="Expected full PR head SHA."
    ),
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
    _require_transfer_capability("run_next_command")
    order = _load_or_exit(path)
    result = apply_transfer_order(order, Path("."))
    _emit_result(result, json_output)
    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)


@transfer_app.command("publish-last-report")
def publish_last_report(
    label: str = typer.Option(
        "transfer-handoff",
        "--label",
        help="Label for the published tracked handoff report.",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Print JSON instead of concise handoff lines.",
    ),
) -> None:
    try:
        result = publish_latest_transfer_report(Path("."), label=label)
    except (FileNotFoundError, ValueError) as exc:
        typer.echo(str(exc))
        typer.echo("TRANSFER_UPLOAD=missing")
        typer.echo("REMOTE_REPORT=")
        typer.echo("CHAT_REPLY=f")
        raise typer.Exit(code=1) from exc

    if json_output:
        typer.echo(json.dumps(result, indent=2, sort_keys=True))
    else:
        typer.echo("TRANSFER_UPLOAD=done")
        typer.echo(f"REMOTE_REPORT={result['remote_report']}")
        typer.echo(f"CHAT_REPLY={result['chat_reply']}")


@transfer_app.command("show-last-report")
def show_last_report() -> None:
    try:
        typer.echo(read_latest_transfer_report(Path(".")))
    except FileNotFoundError as exc:
        typer.echo(str(exc))
        typer.echo("TRANSFER_UPLOAD=missing")
        typer.echo("REMOTE_REPORT=")
        typer.echo("CHAT_REPLY=f")
        raise typer.Exit(code=1) from exc


@transfer_app.command("run-sequence-and-log")
def run_sequence_and_log(
    step: list[str] = typer.Option(
        ...,
        "--step",
        help="One command step; quote it as one shell argument.",
    ),
    label: str = typer.Option(
        "transfer-sequence",
        "--label",
        help="Label for the transfer sequence report.",
    ),
    json_output: bool = typer.Option(False, "--json", help="Print JSON instead of text."),
) -> None:
    commands = [shlex.split(item) for item in step]
    try:
        result = run_and_log_transfer_sequence(commands, label=label, cwd=Path("."))
    except ValueError as exc:
        typer.echo(str(exc))
        typer.echo("TRANSFER_REPORT_WRITTEN=f")
        typer.echo("TRANSFER_REPORT_PATH=")
        typer.echo("FINAL_SIGNAL=f")
        typer.echo("FINAL_NEXT=Provide at least one non-empty --step command.")
        typer.echo("CHAT_REPLY=f | NEXT=Provide at least one non-empty --step command.")
        raise typer.Exit(code=2) from exc

    if json_output:
        typer.echo(json.dumps(result.as_json_data(), indent=2, sort_keys=True))
    else:
        typer.echo("TRANSFER_REPORT_WRITTEN=done")
        typer.echo(f"LOCAL_REPORT={result.remote_report_path}")
        typer.echo("CHAT_REPLY=d | NEXT=Run transfer publish-last-report")

    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)
