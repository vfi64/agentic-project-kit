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


def _summary_items(title: str, values: object, *, label: str) -> None:
    if not isinstance(values, (list, tuple)) or not values:
        return
    typer.echo(title)
    for value in values:
        typer.echo(_summary_line(label, value, indent=2))
    typer.echo("")


def _dirty_state_from_result(result) -> dict[str, object]:
    preflight = result.preflight if isinstance(result.preflight, dict) else {}
    dirty_state = preflight.get("dirty_state")
    if isinstance(dirty_state, dict):
        return dirty_state
    local_run_state = getattr(result.local_run, "state", None)
    if isinstance(local_run_state, dict):
        nested_dirty_state = local_run_state.get("dirty_state")
        if isinstance(nested_dirty_state, dict):
            return nested_dirty_state
    return {}


def _echo_remote_next_user_summary(result) -> None:
    actions = result.post_report_actions or {}
    committed = bool(actions.get("committed"))
    pushed = bool(actions.get("pushed"))
    uploaded = "yes" if pushed else "no_push_failed" if committed else "no_commit_failed"
    dirty_state = _dirty_state_from_result(result)
    rule_ack = result.rule_ack.as_json_data() if result.rule_ack else None

    typer.echo("*" * 36 + " START SUMMARY " + "*" * 36)
    typer.echo("TRANSFER_REMOTE_NEXT_DONE")
    typer.echo("")
    if "no_current_transfer_order" in result.reasons:
        primary_state = "NEW_ORDER_REQUIRED"
    elif "order_consumed" in result.reasons:
        primary_state = "ORDER_CONSUMED"
    elif any(
        reason in result.reasons
        for reason in (
            "stale_transfer_order_status",
            "stale_transfer_order_branch_mismatch",
            "stale_order_missing_freshness_anchor",
            "stale_transfer_order_head_mismatch",
        )
    ):
        primary_state = "STALE_ORDER"
    else:
        primary_state = result.result_status
    typer.echo(_summary_line("STATE", primary_state))
    typer.echo(_summary_line("RETURNCODE", result.returncode))
    if result.reasons:
        typer.echo(_summary_line("REASONS", ",".join(result.reasons)))
    typer.echo("")
    if dirty_state:
        typer.echo("LOCAL_STATE:")
        typer.echo(_summary_line("CLEAN", "yes" if dirty_state.get("clean") else "no", indent=2))
        typer.echo(_summary_line("BRANCH", result.preflight.get("current_branch", result.branch or ""), indent=2))
        typer.echo(_summary_line("HEAD", result.head, indent=2))
        for path in dirty_state.get("staged_changes", ()):
            typer.echo(_summary_line("STAGED", path, indent=2))
        for path in dirty_state.get("unstaged_changes", ()):
            typer.echo(_summary_line("UNSTAGED", path, indent=2))
        for path in dirty_state.get("untracked_files", ()):
            typer.echo(_summary_line("UNTRACKED", path, indent=2))
        typer.echo("")
    if rule_ack is not None:
        typer.echo("RULE_ACK:")
        typer.echo(_summary_line("PRESENT", "yes" if rule_ack.get("present") else "no", indent=2))
        typer.echo(_summary_line("CONFIRMED", "yes" if rule_ack.get("confirmed") else "no", indent=2))
        if rule_ack.get("head"):
            typer.echo(_summary_line("HEAD", rule_ack["head"], indent=2))
        for reason in rule_ack.get("blocking_reasons", ()): 
            typer.echo(_summary_line("BLOCKING_REASON", reason, indent=2))
        typer.echo("")
    final_rule_ack = actions.get("rule_ack_after_report_commit")
    if isinstance(final_rule_ack, dict):
        typer.echo("RULE_ACK_AFTER_REPORT:")
        typer.echo(_summary_line("PRESENT", "yes" if final_rule_ack.get("present") else "no", indent=2))
        typer.echo(_summary_line("CONFIRMED", "yes" if final_rule_ack.get("confirmed") else "no", indent=2))
        if final_rule_ack.get("head"):
            typer.echo(_summary_line("HEAD", final_rule_ack["head"], indent=2))
        for reason in final_rule_ack.get("blocking_reasons", ()):
            typer.echo(_summary_line("BLOCKING_REASON", reason, indent=2))
        typer.echo("")
    _summary_items("BLOCKERS:", result.reasons, label="REASON")
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



def _resolve_expected_head_sha_alias(expected_head_sha: str) -> str:
    """Resolve supported expected-head aliases before guarded PR actions."""
    if expected_head_sha != "current":
        return expected_head_sha

    import subprocess

    completed = subprocess.run(["git", "rev-parse", "HEAD"], text=True, capture_output=True)
    if completed.returncode != 0:
        raise typer.BadParameter(
            "Could not resolve --expected-head-sha current via git rev-parse HEAD: "
            + completed.stderr.strip()
        )
    return completed.stdout.strip()


@transfer_app.command("pr-wait-ci")
def pr_wait_ci_command(
    pr_number: int = typer.Argument(..., help="Pull request number to wait for."),
    expected_head_sha: str = typer.Option("", "--expected-head-sha", help="Expected PR head SHA, or current to use git rev-parse HEAD."),
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
        expected_head_sha=_resolve_expected_head_sha_alias(expected_head_sha),
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
    merge_state_timeout_seconds: int = typer.Option(
        60, "--merge-state-timeout-seconds", min=1, help="Pre-merge GitHub merge-state wait timeout."
    ),
    merge_state_poll_seconds: int = typer.Option(
        5, "--merge-state-poll-seconds", min=1, help="Pre-merge GitHub merge-state polling interval."
    ),
    json_output: bool = typer.Option(False, "--json", help="Print JSON instead of text."),
) -> None:
    _require_transfer_capability("rules_confirmed")
    result = pr_merge_safe(
        pr_number,
        expected_head_sha=_resolve_expected_head_sha_alias(expected_head_sha),
        main_branch=main_branch,
        merge_method=merge_method,
        no_verify_main=no_verify_main,
        merge_state_timeout_seconds=merge_state_timeout_seconds,
        merge_state_poll_seconds=merge_state_poll_seconds,
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
        expected_head_sha=_resolve_expected_head_sha_alias(expected_head_sha),
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



@transfer_app.command("normalize-session")
def normalize_session(
    json_output: bool = typer.Option(False, "--json", help="Print machine-readable JSON only."),
    repair_known_volatile: bool = typer.Option(
        False,
        "--repair-known-volatile",
        help="Restore known volatile transfer output files before checking the session.",
    ),
) -> None:
    """Normalize and summarize the local transfer session state.

    The MVP is diagnostic and evidence-producing only. It does not switch branches,
    pull, delete files, commit, push, or mutate the worktree except for writing the
    canonical transfer outbox file.
    """
    import ast
    import json
    import subprocess
    from pathlib import Path
    from typing import Any

    from agentic_project_kit.transfer_safety_context import write_transfer_outbox

    root = Path(".")

    known_volatile_paths = [
        ".agentic/transfer/outbox/last_result.txt",
        "docs/reports/terminal/transfer_handoff_reports/latest-transfer-handoff-report.json",
        "docs/reports/terminal/transfer_handoff_reports/latest-transfer-handoff-report.log",
    ]

    def run(argv: list[str]) -> dict[str, Any]:
        completed = subprocess.run(argv, cwd=root, text=True, capture_output=True)
        return {
            "argv": argv,
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "ok": completed.returncode == 0,
        }

    volatile_repair_result = None
    if repair_known_volatile:
        volatile_repair_result = run(["git", "restore", "--", *known_volatile_paths])

    volatile_repair_result = None
    if repair_known_volatile:
        volatile_repair_result = run(["git", "restore", "--", *known_volatile_paths])

    branch_result = run(["git", "branch", "--show-current"])
    status_result = run(["git", "status", "--short"])
    head_result = run(["git", "rev-parse", "HEAD"])
    upstream_result = run(["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"])
    upstream_head_result = (
        run(["git", "rev-parse", "@{u}"])
        if upstream_result["ok"]
        else {
            "argv": ["git", "rev-parse", "@{u}"],
            "returncode": 1,
            "stdout": "",
            "stderr": "no upstream",
            "ok": False,
        }
    )

    branch = branch_result["stdout"].strip()
    head = head_result["stdout"].strip()
    upstream = upstream_result["stdout"].strip() if upstream_result["ok"] else ""
    upstream_head = upstream_head_result["stdout"].strip() if upstream_head_result["ok"] else ""
    dirty_status = status_result["stdout"]

    ack_path = root / ".agentic" / "rule_ack" / "current.json"
    rule_ack: dict[str, Any] = {
        "path": str(ack_path),
        "exists": ack_path.exists(),
        "repo_head": None,
        "matches_head": False,
        "error": None,
    }
    if ack_path.exists():
        try:
            ack_data = json.loads(ack_path.read_text(encoding="utf-8"))
            rule_ack["repo_head"] = ack_data.get("repo_head")
            rule_ack["matches_head"] = bool(head and ack_data.get("repo_head") == head[:7])
        except Exception as exc:
            rule_ack["error"] = str(exc)

    inbox_path = root / ".agentic" / "transfer" / "inbox" / "next_command.py.txt"
    outbox_path = root / ".agentic" / "transfer" / "outbox" / "last_result.txt"

    inbox_status: dict[str, Any] = {
        "path": str(inbox_path),
        "exists": inbox_path.exists(),
        "syntax_ok": None,
        "error": None,
    }
    if inbox_path.exists():
        try:
            ast.parse(inbox_path.read_text(encoding="utf-8"), filename=str(inbox_path))
            inbox_status["syntax_ok"] = True
        except SyntaxError as exc:
            inbox_status["syntax_ok"] = False
            inbox_status["error"] = f"{exc.__class__.__name__}: {exc}"

    typed_inbox = root / ".agentic" / "typed_work_orders" / "inbox"
    typed_pending = sorted(str(p) for p in typed_inbox.glob("*.yaml")) if typed_inbox.exists() else []
    typed_queue_status = (
        "no_command"
        if not typed_pending
        else "single_command"
        if len(typed_pending) == 1
        else "multiple_commands"
    )

    checks = {
        "branch_present": bool(branch),
        "worktree_clean": dirty_status == "",
        "head_matches_upstream": bool(head and upstream_head and head == upstream_head),
        "rule_ack_current": bool(rule_ack["matches_head"]),
        "canonical_inbox_syntax_ok": inbox_status["syntax_ok"] is not False,
        "typed_queue_not_ambiguous": typed_queue_status != "multiple_commands",
    }

    blockers: list[str] = []
    if not checks["branch_present"]:
        blockers.append("branch_missing")
    if not checks["worktree_clean"]:
        blockers.append("dirty_worktree")
    if not checks["head_matches_upstream"]:
        blockers.append("head_upstream_mismatch_or_missing_upstream")
    if not checks["rule_ack_current"]:
        blockers.append("rule_ack_not_current")
    if not checks["canonical_inbox_syntax_ok"]:
        blockers.append("canonical_inbox_syntax_error")
    if not checks["typed_queue_not_ambiguous"]:
        blockers.append("typed_queue_multiple_commands")

    result_status = "PASS" if not blockers else "BLOCK"
    final_signal = "d" if result_status == "PASS" else "f"
    next_action = (
        "Session normalized; proceed with the next explicit transfer or product slice."
        if result_status == "PASS"
        else "Resolve blockers before running transfer work: " + ", ".join(blockers)
    )

    payload: dict[str, Any] = {
        "schema_version": 1,
        "kind": "transfer_normalize_session_result",
        "action": "normalize-session",
        "result_status": result_status,
        "final_signal": final_signal,
        "next_action": next_action,
        "repo": {
            "branch": branch,
            "head": head,
            "upstream": upstream,
            "upstream_head": upstream_head,
            "head_matches_upstream": checks["head_matches_upstream"],
            "dirty_status": dirty_status,
            "worktree_clean": checks["worktree_clean"],
        },
        "rule_ack": rule_ack,
        "canonical_transfer_files": {
            "inbox": inbox_status,
            "outbox": {
                "path": str(outbox_path),
                "exists": outbox_path.exists(),
            },
        },
        "typed_work_orders": {
            "inbox_path": str(typed_inbox),
            "status": typed_queue_status,
            "pending_count": len(typed_pending),
            "pending": typed_pending,
        },
        "checks": checks,
        "blockers": blockers,
        "volatile_repair": {
            "requested": repair_known_volatile,
            "known_paths": known_volatile_paths,
            "result": volatile_repair_result,
        },
    }

    outbox_written = write_transfer_outbox(root, payload)
    payload["outbox_written"] = str(outbox_written)

    typer.echo(json.dumps(payload, indent=2, ensure_ascii=False))
    if not json_output:
        typer.echo(f"FINAL_SIGNAL={final_signal}")
        typer.echo(f"FINAL_NEXT={next_action}")
        typer.echo(f"CHAT_REPLY={final_signal} | NEXT={next_action}")


@transfer_app.command("prepare-successor-handoff")
def prepare_successor_handoff(
    json_output: bool = typer.Option(False, "--json", help="Print machine-readable JSON only."),
    repair_known_volatile: bool = typer.Option(
        False,
        "--repair-known-volatile",
        help="Restore known volatile transfer output files before preparing the handoff request.",
    ),
    render_prompt: bool = typer.Option(
        False,
        "--render-prompt",
        help="Render a copy-and-paste successor chat prompt directly from the handoff payload.",
    ),
) -> None:
    """Prepare a canonical LLM handoff assignment in the transfer outbox.

    This command creates a repo-backed local-to-LLM transfer message. The LLM can
    read it after a simple "g" and produce a copy-and-paste successor chat prompt.
    """
    import hashlib
    import json
    import subprocess
    from datetime import datetime, timezone
    from pathlib import Path
    from typing import Any

    from agentic_project_kit.transfer_safety_context import write_transfer_outbox

    root = Path(".")

    known_volatile_paths = [
        ".agentic/transfer/outbox/last_result.txt",
        "docs/reports/terminal/transfer_handoff_reports/latest-transfer-handoff-report.json",
        "docs/reports/terminal/transfer_handoff_reports/latest-transfer-handoff-report.log",
    ]

    required_sources = [
        "docs/handoff/NEXT_CHAT_BOOTSTRAP.md",
        "docs/handoff/START_NEW_CHAT_PROMPT.md",
        "docs/handoff/CLOSEOUT_BEFORE_CHAT_SWITCH_PROMPT.md",
        "docs/handoff/CURRENT_HANDOFF.md",
        "docs/STATUS.md",
        ".agentic/handoff_state.yaml",
        ".agentic/compiled_agent_context.yaml",
        ".agentic/rule_mechanism_inventory.yaml",
        ".agentic/rule_migrations.yaml",
        ".agentic/rule_preservation.yaml",
        ".agentic/transfer_safety_rules.yaml",
        "docs/governance/FINAL_SUMMARY_CONTRACT.md",
        "docs/governance/CHAT_COMMUNICATION_CONTRACT.md",
        "docs/governance/PORTABLE_CHAT_EXECUTION_CONTRACT.md",
        "docs/governance/CHAT_BOOTSTRAP_AND_DRIFT_CONTRACT.md",
        "docs/planning/RULE_REGISTRY_IMPROVEMENT_PLAN.md",
        "docs/planning/WORKFLOW_REDUCTION_FOCUS.md",
    ]

    help_commands = [
        ["./.venv/bin/agentic-kit", "--help"],
        ["./.venv/bin/agentic-kit", "transfer", "--help"],
        ["./.venv/bin/agentic-kit", "work-order", "--help"],
        ["./.venv/bin/agentic-kit", "handoff", "--help"],
        ["./.venv/bin/agentic-kit", "evidence", "--help"],
        ["./.venv/bin/agentic-kit", "rules", "--help"],
    ]

    transfer_rules_text = """Transferregeln
1. Remote arbeiten
Vorrang hat remote-repo-backed Arbeit.
Das bedeutet:
* Änderungen, Aufträge, Reports und Übergaben sollen möglichst über das Remote-Repo laufen.
* Der lokale Rechner führt nur klar definierte, repo-gestützte Aktionen aus.
* Vor jeder Arbeit gilt:
    * aktuellen Branch prüfen,
    * Status prüfen,
    * Regel-Acknowledgement prüfen,
    * keine Arbeit auf schmutzigem oder falschem Branch.
* Für Git-, Status- und Transferaktionen sind bevorzugt vorhandene agentic-kit transfer ...-Kommandos zu verwenden, nicht rohe Shell-Kommandos.
* PRs, Checks, Merge und Handoff-Refresh laufen über die vorhandenen sicheren Wrapper.
* Dauerhafte Evidenz gehört ins Repo unter geeignete Report- oder Evidence-Pfade.
* Temporäre Transferdaten dürfen das Repo nicht dauerhaft zumüllen.
2. Via Transferdateien arbeiten
Wenn Remote-Arbeit allein nicht reicht, wird über feste Transferdateien gearbeitet.
Es gibt je Richtung genau eine kanonische Datei:
.agentic/transfer/inbox/next_command.py.txt
.agentic/transfer/outbox/last_result.txt
Regeln:
* next_command.py.txt ist die Datei LLM → lokal.
* last_result.txt ist die Datei lokal → LLM.
* Diese Dateien werden überschrieben, nicht jedes Mal neu angelegt.
* Keine ständig neuen Dateien wie b11_..._repair.py.txt, außer es gibt einen ausdrücklich begründeten Archiv- oder Evidence-Fall.
* Python-Transferdateien behalten die Endung .py.txt.
* Lokal wird eine Transferdatei bewusst mit dem Projekt-Python ausgeführt:
./.venv/bin/python .agentic/transfer/inbox/next_command.py.txt
* Die Ausführung soll das Ergebnis nach .agentic/transfer/outbox/last_result.txt schreiben.
* Die Rückmeldung an den Chat soll bevorzugt nur den Inhalt oder die Kerndaten aus last_result.txt enthalten.
* Wenn ein Ergebnis dauerhaft nachweisbar sein soll, wird es zusätzlich über einen vorhandenen Publish- oder Report-Mechanismus ins Repo geschrieben, nicht durch wahlloses Sammeln neuer Transferdateien.
3. Copy and Paste
Copy & Paste ist nur der Fallback.
Es wird nur genutzt, wenn:
* Remote-Arbeit nicht möglich ist,
* Transferdateien nicht funktionieren,
* oder eine kurze manuelle Bestätigung wirklich schneller und risikoärmer ist.
Regeln:
* Keine langen Shellskripte per Copy & Paste.
* Keine heredocs.
* Keine fragilen mehrzeiligen Kommando-Blöcke.
* Keine Blöcke, die den Terminalprozess versehentlich beenden.
* Wenn Copy & Paste nötig ist, dann nur:
    * kurze Einzelkommandos,
    * klarer Zweck,
    * vorher Branch- und Statusprüfung,
    * danach Ausgabe zurückmelden.
* Copy & Paste ist keine dauerhafte Evidenz. Dauerhafte Evidenz muss ins Repo oder in einen Report.
Für Fehlerzustände gilt konkret: keine neuen ad-hoc-Patch-Dateinamen erzeugen, sondern die kanonische Datei .agentic/transfer/inbox/next_command.py.txt remote überschreiben lassen. Danach lokal genau diese Datei mit ./.venv/bin/python ... ausführen und die Antwort aus .agentic/transfer/outbox/last_result.txt zurückgeben.
Zusätzlich: Möglichst komplexere agentic-kit-Kommandos bevorzugen, damit die Zusammenarbeit nicht in zu viele manuelle Einzelschritte zerfällt.
"""

    def run(argv: list[str]) -> dict[str, Any]:
        completed = subprocess.run(argv, cwd=root, text=True, capture_output=True)
        return {
            "argv": argv,
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "ok": completed.returncode == 0,
        }

    def file_info(rel_path: str) -> dict[str, Any]:
        p = root / rel_path
        if not p.exists():
            return {"path": rel_path, "exists": False, "sha256": None, "size": None}
        data = p.read_bytes()
        return {
            "path": rel_path,
            "exists": True,
            "sha256": hashlib.sha256(data).hexdigest(),
            "size": len(data),
        }

    volatile_repair_result = None
    if repair_known_volatile:
        volatile_repair_result = run(["git", "restore", "--", *known_volatile_paths])

    branch_result = run(["git", "branch", "--show-current"])
    status_result = run(["git", "status", "--short"])
    head_result = run(["git", "rev-parse", "HEAD"])
    upstream_result = run(["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"])
    upstream_head_result = (
        run(["git", "rev-parse", "@{u}"])
        if upstream_result["ok"]
        else {"argv": ["git", "rev-parse", "@{u}"], "returncode": 1, "stdout": "", "stderr": "no upstream", "ok": False}
    )

    command_inventory = []
    for argv in help_commands:
        command_inventory.append(run(argv))

    branch = branch_result["stdout"].strip()
    head = head_result["stdout"].strip()
    upstream = upstream_result["stdout"].strip() if upstream_result["ok"] else ""
    upstream_head = upstream_head_result["stdout"].strip() if upstream_head_result["ok"] else ""
    dirty_status = status_result["stdout"]

    source_inventory = [file_info(path) for path in required_sources]
    missing_sources = [item["path"] for item in source_inventory if not item["exists"]]

    result_status = "PASS" if branch and head and head == upstream_head and dirty_status == "" and not missing_sources else "BLOCK"
    final_signal = "d" if result_status == "PASS" else "f"
    blockers = []
    if not branch:
        blockers.append("branch_missing")
    if not head or head != upstream_head:
        blockers.append("head_upstream_mismatch")
    if dirty_status:
        blockers.append("dirty_worktree")
    if missing_sources:
        blockers.append("missing_required_sources")

    next_action = (
        "Tell the LLM 'g'; it should read this handoff_request and return a copy-and-paste successor chat prompt."
        if result_status == "PASS"
        else "Resolve handoff preparation blockers before asking the LLM for a successor prompt: " + ", ".join(blockers)
    )

    payload: dict[str, Any] = {
        "schema_version": 1,
        "kind": "local_to_llm_last_result",
        "message_kind": "handoff_request",
        "assignment_kind": "successor_chat_prompt",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "result_status": result_status,
        "final_signal": final_signal,
        "chat_reply": f"{final_signal} | NEXT={next_action}",
        "next_action": next_action,
        "repo": {
            "full_name": "vfi64/agentic-project-kit",
            "local_path": "/Users/hof/Dropbox/Privat/GitHub/agentic-project-kit",
            "branch": branch,
            "head": head,
            "upstream": upstream,
            "upstream_head": upstream_head,
            "head_matches_upstream": bool(head and head == upstream_head),
            "dirty_status": dirty_status,
            "worktree_clean": dirty_status == "",
        },
        "llm_assignment": {
            "task": "Erzeuge einen vollständigen Copy-and-Paste-Übergabeprompt für einen neuen Chat.",
            "language": "de",
            "must_do": [
                "Nicht aus Chat-Erinnerung arbeiten.",
                "Die aufgeführten Repo-Pflichtquellen und maschinenlesbaren Regeln als Quellen der Wahrheit behandeln.",
                "Alle Erfahrungen, Ideen, Fehlerklassen und offenen Aufgaben aus dem aktuellen Chat ergänzen, soweit sie noch nicht in Handoff-, Status-, Planungs- oder Governance-Dateien enthalten sind.",
                "Unsicherheit und stale-verdächtige Quellen klar markieren.",
                "Dem neuen Chat die vollständigen Transferregeln geben.",
                "Dem neuen Chat den aktuellen agentic-kit-Kommandobestand und die Präferenz für komplexere transfer-Kommandos mitgeben.",
                "Einen direkt kopierbaren Startprompt ausgeben, der Repo, lokalen Pfad, Startbefehle, Pflichtquellen, aktuellen Stand, offene Blocker und nächsten sicheren Slice enthält.",
            ],
            "must_not_do": [
                "Keine erfolgreichen Checks oder Merges erfinden.",
                "Keine rohen Git-Kommandos bevorzugen, wenn agentic-kit transfer-Kommandos existieren.",
                "Keine Copy/Paste-Skripte als Primärweg vorschlagen.",
                "Keine geschützten Dateien breit überschreiben.",
            ],
            "response_contract": {
                "must_return_sections": [
                    "Copy-and-paste successor prompt",
                    "Machine-readable current state summary",
                    "Missing or stale repo updates",
                    "Next safest slice",
                ],
                "format": "markdown with a fenced YAML or JSON state block inside the prompt",
            },
        },
        "transfer_rules_text": transfer_rules_text,
        "transfer_protocol_machine": {
            "priority_order": [
                "remote_repo_backed_work_first",
                "canonical_transfer_files_second",
                "copy_paste_only_fallback",
            ],
            "canonical_files": {
                "llm_to_local": ".agentic/transfer/inbox/next_command.py.txt",
                "local_to_llm": ".agentic/transfer/outbox/last_result.txt",
            },
            "command_policy": {
                "prefer_agentic_kit_transfer_commands": True,
                "prefer_complex_wrappers_over_single_step_mode": True,
            },
        },
        "required_sources": source_inventory,
        "missing_sources": missing_sources,
        "command_inventory": {
            "source": "local_cli_help",
            "commands": command_inventory,
        },
        "chat_delta_capture_instruction": (
            "Die LLM soll zusätzlich alles aus dem aktuellen Chat aufnehmen, was noch nicht repo-backed "
            "dokumentiert ist: Transferdatei-Zustandsmodell, handoff_request/message_kind-Idee, "
            "prepare-successor-handoff-MVP, normalize-session-Erfahrungen, volatile repair, current-SHA-Automatisierung "
            "für PR-Kommandos, und die Forderung nach weniger Einzelschrittmodus."
        ),
        "blockers": blockers,
        "volatile_repair": {
            "requested": repair_known_volatile,
            "known_paths": known_volatile_paths,
            "result": volatile_repair_result,
        },
    }

    outbox_path = write_transfer_outbox(root, payload)
    payload["outbox_written"] = str(outbox_path)

    if render_prompt and not json_output:
        prompt_state = {
            "schema_version": 1,
            "kind": "successor_chat_handoff_state",
            "repo": payload["repo"],
            "message_kind": payload["message_kind"],
            "assignment_kind": payload["assignment_kind"],
            "result_status": payload["result_status"],
            "blockers": payload["blockers"],
            "missing_sources": payload["missing_sources"],
            "transfer_protocol_machine": payload["transfer_protocol_machine"],
        }
        required_source_lines = [
            "- {path}: exists={exists}, sha256={sha256}, size={size}".format(**item)
            for item in source_inventory
        ]
        template_path = root / ".agentic/transfer/templates/successor_handoff_prompt.md"
        if not template_path.exists():
            raise typer.BadParameter("Missing successor handoff prompt template: .agentic/transfer/templates/successor_handoff_prompt.md")
        rendered_prompt = template_path.read_text(encoding="utf-8").format(
            repo_full_name=payload["repo"]["full_name"],
            local_path_command="cd " + payload["repo"]["local_path"],
            prompt_state_json=json.dumps(prompt_state, indent=2, ensure_ascii=False),
            required_sources="\n".join(required_source_lines),
            transfer_rules=transfer_rules_text.strip(),
        )
        payload["rendered_successor_prompt"] = rendered_prompt
        write_transfer_outbox(root, payload)
        typer.echo(rendered_prompt)
        return

    typer.echo(json.dumps(payload, indent=2, ensure_ascii=False))
    if not json_output:
        typer.echo(f"FINAL_SIGNAL={final_signal}")
        typer.echo(f"FINAL_NEXT={next_action}")
        typer.echo(f"CHAT_REPLY={final_signal} | NEXT={next_action}")


@transfer_app.command("remote-work-start")
def remote_work_start(
    branch: str = typer.Argument(..., help="Feature branch to prepare, for example feature/name."),
    main_branch: str = typer.Option("main", "--main-branch", help="Base branch for new work branches."),
    json_output: bool = typer.Option(False, "--json", help="Print machine-readable JSON only."),
) -> None:
    import json
    import re
    import subprocess
    from datetime import datetime, timezone
    from pathlib import Path
    from typing import Any

    root = Path(".")
    known_volatile_paths = [
        ".agentic/transfer/outbox/last_result.txt",
        "docs/reports/terminal/transfer_handoff_reports/latest-transfer-handoff-report.json",
        "docs/reports/terminal/transfer_handoff_reports/latest-transfer-handoff-report.log",
    ]

    steps: list[dict[str, Any]] = []
    blockers: list[str] = []

    def run_step(name: str, argv: list[str], *, allow_fail: bool = False) -> dict[str, Any]:
        completed = subprocess.run(argv, cwd=root, text=True, capture_output=True)
        item = {
            "name": name,
            "argv": argv,
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "ok": completed.returncode == 0,
            "allowed_failure": allow_fail,
        }
        steps.append(item)
        if completed.returncode != 0 and not allow_fail:
            blockers.append(name + "_failed")
        return item

    def restore_volatile(name: str) -> None:
        run_step(name, ["git", "restore", "--", *known_volatile_paths], allow_fail=True)

    if not re.fullmatch(r"[A-Za-z0-9._/-]+", branch):
        blockers.append("invalid_branch_name")
    if branch in {main_branch, "main", "master"}:
        blockers.append("refuse_main_branch")
    if branch.startswith("/") or branch.endswith("/") or ".." in branch:
        blockers.append("unsafe_branch_name")
    if not branch.startswith(("feature/", "fix/", "docs/", "chore/")):
        blockers.append("branch_prefix_not_allowed")

    if not blockers:
        restore_volatile("restore-before-start")
        run_step("rules-acknowledge-before-start", ["./.venv/bin/agentic-kit", "rules", "acknowledge"])
        restore_volatile("restore-after-ack")

        run_step("switch-main", ["./.venv/bin/agentic-kit", "transfer", "branch-switch", main_branch])
        restore_volatile("restore-after-switch-main")

        run_step("pull-main", ["./.venv/bin/agentic-kit", "transfer", "pull-current"])
        restore_volatile("restore-after-pull-main")

        run_step("rules-acknowledge-main", ["./.venv/bin/agentic-kit", "rules", "acknowledge"])
        restore_volatile("restore-after-main-ack")

        run_step("normalize-main", ["./.venv/bin/agentic-kit", "transfer", "normalize-session", "--repair-known-volatile"])
        restore_volatile("restore-after-normalize-main")

        create = run_step("branch-create", ["./.venv/bin/agentic-kit", "transfer", "branch-create", branch], allow_fail=True)
        restore_volatile("restore-after-branch-create")

        create_text = create["stdout"] + create["stderr"]
        if create["ok"]:
            run_step("branch-switch-created", ["./.venv/bin/agentic-kit", "transfer", "branch-switch", branch])
        elif "already exists" in create_text:
            run_step("branch-switch-existing", ["./.venv/bin/agentic-kit", "transfer", "branch-switch", branch])
        else:
            blockers.append("branch_create_failed")

        restore_volatile("restore-after-work-branch-switch")
        run_step("rules-acknowledge-work-branch", ["./.venv/bin/agentic-kit", "rules", "acknowledge"])
        restore_volatile("restore-after-work-branch-ack")

        run_step("push-current", ["./.venv/bin/agentic-kit", "transfer", "push-current"])
        restore_volatile("restore-after-push")

        run_step("repo-status", ["./.venv/bin/agentic-kit", "transfer", "repo-status"])

    blockers = list(dict.fromkeys(blockers))
    result_status = "PASS" if not blockers else "BLOCK"
    final_signal = "d" if result_status == "PASS" else "f"
    next_action = "Remote work branch is ready; continue with the product slice." if result_status == "PASS" else "Resolve remote-work-start blockers before continuing: " + ", ".join(blockers)

    payload = {
        "schema_version": 1,
        "kind": "transfer_remote_work_start_result",
        "action": "remote-work-start",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "result_status": result_status,
        "final_signal": final_signal,
        "branch": branch,
        "main_branch": main_branch,
        "blockers": blockers,
        "steps": steps,
        "next_action": next_action,
    }

    typer.echo(json.dumps(payload, indent=2, ensure_ascii=False))
    if not json_output:
        typer.echo("********************************** START SUMMARY ***********************************")
        typer.echo("TRANSFER_REMOTE_WORK_START")
        typer.echo("")
        typer.echo(f"STATE:                 {result_status}")
        typer.echo(f"BRANCH:                {branch}")
        typer.echo(f"MAIN_BRANCH:           {main_branch}")
        typer.echo(f"BLOCKERS:              {len(blockers)}")
        typer.echo("")
        typer.echo(f"NEXT:                  {next_action}")
        typer.echo(f"CHAT_REPLY:            {final_signal} | NEXT={next_action}")
        typer.echo("*********************************** END SUMMARY ************************************")


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
