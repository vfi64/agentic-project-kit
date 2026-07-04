from __future__ import annotations

# ruff: noqa: F403,F405

from agentic_project_kit.cli_commands.transfer_shared import *
from agentic_project_kit.cli_commands.transfer_context_helpers import *


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
    wait_ci = _public_transfer_attr("pr_wait_ci", pr_wait_ci)
    result = wait_ci(
        pr_number,
        expected_head_sha=_resolve_expected_head_sha_alias(expected_head_sha),
        timeout_seconds=timeout_seconds,
        poll_seconds=poll_seconds,
    )
    if quiet_report and not json_output:
        _echo_quiet_repo_report(result, label=f"pr-wait-ci-{pr_number}")
    else:
        echo_repo_result = _public_transfer_attr("_echo_repo_result", _echo_repo_result)
        echo_repo_result(result, json_output)
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
    skip_llm_context_gate: bool = typer.Option(
        False,
        "--skip-llm-context-gate",
        help="Recovery-only: run PR merge without requiring fresh generated LLM context.",
    ),
) -> None:
    if not skip_llm_context_gate:
        require_fresh = _public_transfer_attr("_require_fresh_llm_context_or_exit", _require_fresh_llm_context_or_exit)
        require_fresh(max_age_minutes=60, json_output=json_output)
    require_capability = _public_transfer_attr("_require_transfer_capability", _require_transfer_capability)
    require_capability("rules_confirmed")
    merge_safe = _public_transfer_attr("pr_merge_safe", pr_merge_safe)
    result = merge_safe(
        pr_number,
        expected_head_sha=_resolve_expected_head_sha_alias(expected_head_sha),
        main_branch=main_branch,
        merge_method=merge_method,
        no_verify_main=no_verify_main,
        merge_state_timeout_seconds=merge_state_timeout_seconds,
        merge_state_poll_seconds=merge_state_poll_seconds,
    )
    echo_repo_result = _public_transfer_attr("_echo_repo_result", _echo_repo_result)
    echo_repo_result(result, json_output)
    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)

@transfer_app.command("pr-complete")
def pr_complete_command(
    pr_number: int = typer.Argument(..., help="Pull request number to complete."),
    expected_head_sha: str = typer.Option(
        "",
        "--expected-head-sha",
        help="Expected PR head SHA, or current to use git rev-parse HEAD before the merge.",
    ),
    main_branch: str = typer.Option("main", "--main-branch", help="Main branch to sync after the merge."),
    merge_method: str = typer.Option("squash", "--merge-method", help="GitHub merge method."),
    timeout_seconds: int = typer.Option(300, "--timeout-seconds", min=1, help="Maximum CI wait time."),
    poll_seconds: int = typer.Option(
        10,
        "--interval-seconds",
        "--poll-seconds",
        min=1,
        help="CI polling interval.",
    ),
    json_output: bool = typer.Option(False, "--json", help="Print JSON instead of text."),
    skip_llm_context_gate: bool = typer.Option(
        False,
        "--skip-llm-context-gate",
        help="Recovery-only: run PR completion without requiring fresh generated LLM context.",
    ),
    post_merge_complete: bool = typer.Option(
        False,
        "--post-merge-complete",
        help=(
            "Invalid for pr-complete. Use pr-create-complete --post-merge-complete for new PRs, "
            "or run post-merge-complete separately after an existing PR is merged."
        ),
    ),
) -> None:
    if post_merge_complete:
        payload = {
            "schema_version": 1,
            "kind": "transfer_pr_complete_result",
            "action": "pr-complete",
            "result_status": "BLOCKED",
            "final_signal": "f",
            "failed_step": "invalid_argument_post_merge_complete",
            "blockers": ["invalid_argument_post_merge_complete"],
            "next_action": (
                "--post-merge-complete is not valid for transfer pr-complete. "
                "For an existing PR: run transfer pr-complete, then transfer post-merge-complete --after-pr <PR>."
            ),
        }
        if json_output:
            typer.echo(json.dumps(payload, indent=2, sort_keys=True))
        else:
            typer.echo("TRANSFER_PR_COMPLETE_BLOCKED")
            typer.echo("reason=invalid_argument_post_merge_complete")
            typer.echo(f"NEXT: {payload['next_action']}")
        raise typer.Exit(code=2)

    if not skip_llm_context_gate:
        require_fresh = _public_transfer_attr("_require_fresh_llm_context_or_exit", _require_fresh_llm_context_or_exit)
        require_fresh(max_age_minutes=60, json_output=json_output)

    import os
    import re
    import subprocess
    from datetime import datetime, timezone

    resolved_head_sha = _resolve_expected_head_sha_alias(expected_head_sha)
    agentic_kit = "./.venv/bin/agentic-kit"
    steps: list[dict[str, object]] = []

    live_status_parent = os.environ.get("AGENTIC_KIT_WRAPPER_LIVE_STATUS_PARENT", "")

    def update_parent_live_status(
        phase: wrapper_live_status.WrapperPhase,
        *,
        result_status: str = "RUNNING",
        step: str = "",
        failed_step: str = "",
    ) -> None:
        if live_status_parent != "pr-create-complete":
            return
        wrapper_live_status.write_wrapper_live_status(
            Path("."),
            wrapper="pr-create-complete",
            phase=phase,
            result_status=result_status,
            base=os.environ.get("AGENTIC_KIT_WRAPPER_LIVE_STATUS_BASE", main_branch),
            head=os.environ.get("AGENTIC_KIT_WRAPPER_LIVE_STATUS_HEAD", ""),
            expected_head_sha=os.environ.get(
                "AGENTIC_KIT_WRAPPER_LIVE_STATUS_EXPECTED_HEAD_SHA",
                resolved_head_sha,
            ),
            pr_number=pr_number,
            blockers=[failed_step] if failed_step else [],
            step=step,
        )

    def run_step(name: str, argv: list[str]) -> int:
        completed = subprocess.run(argv, text=True, capture_output=True)
        item: dict[str, object] = {
            "name": name,
            "argv": argv,
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "ok": completed.returncode == 0,
        }
        steps.append(item)
        return completed.returncode

    def pr_status_allows_wait_ci_fallback() -> bool:
        completed = subprocess.run(
            [agentic_kit, "transfer", "pr-status", str(pr_number)],
            text=True,
            capture_output=True,
        )
        item: dict[str, object] = {
            "name": "pr-status-after-wait-ci-failure",
            "argv": [agentic_kit, "transfer", "pr-status", str(pr_number)],
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "ok": completed.returncode == 0,
        }
        steps.append(item)
        if completed.returncode != 0:
            return False
        status_text = completed.stdout
        expected_line = f"head_ref_oid={resolved_head_sha}"
        return (
            "decision=green" in status_text
            and "state=OPEN" in status_text
            and expected_line in status_text
        )

    def pr_is_merged_after_post_merge_complete_failure() -> bool:
        command = ["gh", "pr", "view", str(pr_number), "--json", "state,mergedAt,mergeCommit"]
        completed = subprocess.run(command, text=True, capture_output=True)
        item: dict[str, object] = {
            "name": "pr-merged-after-post-merge-complete-failure",
            "argv": command,
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "ok": completed.returncode == 0,
        }
        steps.append(item)
        if completed.returncode != 0:
            return False
        try:
            data = json.loads(completed.stdout or "{}")
        except json.JSONDecodeError:
            return False
        return bool(data.get("mergedAt")) or str(data.get("state", "")).upper() == "MERGED"
    def post_merge_check_requests_successor_refresh(output: str) -> bool:
        return "NEEDS_SUCCESSOR_PACKAGE_REFRESH" in output or "successor package stale" in output
    def _extract_admin_refresh_pr_number(output: str) -> int | None:
        pull_match = re.search(r"/pull/(\d+)", output)
        if pull_match:
            return int(pull_match.group(1))
        existing_match = re.search(r"existing_pr=(\d+)", output)
        if existing_match:
            return int(existing_match.group(1))
        try:
            payload = json.loads(output or "{}")
        except json.JSONDecodeError:
            return None
        if not isinstance(payload, dict):
            return None
        combined = "\n".join(
            str(payload.get(key, ""))
            for key in ("stdout", "stderr", "next_action")
        )
        pull_match = re.search(r"/pull/(\d+)", combined)
        if pull_match:
            return int(pull_match.group(1))
        existing_match = re.search(r"existing_pr=(\d+)", combined)
        if existing_match:
            return int(existing_match.group(1))
        return None
    def run_admin_refresh_followup_if_needed() -> tuple[bool, str]:
        sync_command = [agentic_kit, "transfer", "sync-main"]
        sync = subprocess.run(sync_command, text=True, capture_output=True)
        steps.append(
            {
                "name": "sync-main-before-post-merge-check-after-post-merge-complete",
                "argv": sync_command,
                "returncode": sync.returncode,
                "stdout": sync.stdout,
                "stderr": sync.stderr,
                "ok": sync.returncode == 0,
            }
        )
        if sync.returncode != 0:
            return False, "sync-main_failed_before_post-merge-check_after_post-merge-complete"

        check_command = [agentic_kit, "transfer", "post-merge-check"]
        check = subprocess.run(check_command, text=True, capture_output=True)
        steps.append(
            {
                "name": "post-merge-check-after-post-merge-complete",
                "argv": check_command,
                "returncode": check.returncode,
                "stdout": check.stdout,
                "stderr": check.stderr,
                "ok": check.returncode == 0,
            }
        )
        check_output = f"{check.stdout}\n{check.stderr}"
        if check.returncode == 0 and not post_merge_check_requests_successor_refresh(check_output):
            return True, ""
        if not post_merge_check_requests_successor_refresh(check_output):
            return False, "post-merge-check_failed_after_post-merge-complete"
        admin_command = [
            agentic_kit,
            "transfer",
            "admin-refresh-pr",
            "--after-pr",
            str(pr_number),
            "--main-branch",
            main_branch,
            "--json",
        ]
        admin = subprocess.run(admin_command, text=True, capture_output=True)
        steps.append(
            {
                "name": "admin-refresh-pr-after-successor-refresh-needed",
                "argv": admin_command,
                "returncode": admin.returncode,
                "stdout": admin.stdout,
                "stderr": admin.stderr,
                "ok": admin.returncode == 0,
            }
        )
        if admin.returncode != 0:
            return False, "admin-refresh-pr_failed_after_successor_refresh_needed"
        admin_pr_number = _extract_admin_refresh_pr_number(admin.stdout)
        if admin_pr_number is None:
            return False, "admin-refresh-pr_number_not_found"
        head_command = [
            "gh",
            "pr",
            "view",
            str(admin_pr_number),
            "--json",
            "headRefOid",
            "--jq",
            ".headRefOid",
        ]
        head = subprocess.run(head_command, text=True, capture_output=True)
        steps.append(
            {
                "name": "admin-refresh-pr-head-sha",
                "argv": head_command,
                "returncode": head.returncode,
                "stdout": head.stdout,
                "stderr": head.stderr,
                "ok": head.returncode == 0,
            }
        )
        admin_head_sha = head.stdout.strip()
        if head.returncode != 0 or len(admin_head_sha) != 40:
            return False, "admin-refresh-pr_head_sha_not_resolved"
        ack_command = [agentic_kit, "rules", "acknowledge"]
        ack = subprocess.run(ack_command, text=True, capture_output=True)
        steps.append(
            {
                "name": "rules-acknowledge-before-admin-refresh-complete",
                "argv": ack_command,
                "returncode": ack.returncode,
                "stdout": ack.stdout,
                "stderr": ack.stderr,
                "ok": ack.returncode == 0,
            }
        )
        if ack.returncode != 0:
            return False, "rules-acknowledge_failed_before_admin_refresh_complete"
        complete_command = [
            agentic_kit,
            "transfer",
            "pr-complete",
            str(admin_pr_number),
            "--expected-head-sha",
            admin_head_sha,
            "--merge-method",
            merge_method,
            "--timeout-seconds",
            str(timeout_seconds),
            "--interval-seconds",
            str(poll_seconds),
            "--skip-llm-context-gate",
            "--json",
        ]
        complete = subprocess.run(complete_command, text=True, capture_output=True)
        steps.append(
            {
                "name": "admin-refresh-pr-complete",
                "argv": complete_command,
                "returncode": complete.returncode,
                "stdout": complete.stdout,
                "stderr": complete.stderr,
                "ok": complete.returncode == 0,
            }
        )
        if complete.returncode != 0:
            return False, "admin-refresh-pr-complete_failed"
        final_check = subprocess.run(check_command, text=True, capture_output=True)
        steps.append(
            {
                "name": "post-merge-check-after-admin-refresh-complete",
                "argv": check_command,
                "returncode": final_check.returncode,
                "stdout": final_check.stdout,
                "stderr": final_check.stderr,
                "ok": final_check.returncode == 0,
            }
        )
        final_output = f"{final_check.stdout}\n{final_check.stderr}"
        if final_check.returncode != 0 or post_merge_check_requests_successor_refresh(final_output):
            return False, "post-merge-check_still_requires_successor_refresh"
        return True, ""

    step_plan = [
        (
            "pr-wait-ci",
            [
                agentic_kit,
                "transfer",
                "pr-wait-ci",
                str(pr_number),
                "--expected-head-sha",
                resolved_head_sha,
                "--timeout-seconds",
                str(timeout_seconds),
                "--interval-seconds",
                str(poll_seconds),
            ],
        ),
        (
            "pr-merge-safe",
            [
                agentic_kit,
                "transfer",
                "pr-merge-safe",
                str(pr_number),
                "--expected-head-sha",
                resolved_head_sha,
                "--main-branch",
                main_branch,
                "--merge-method",
                merge_method,
                "--skip-llm-context-gate",
            ],
        ),
        ("main-switch", ["git", "switch", main_branch]),
        ("main-pull", ["git", "pull", "--ff-only", "origin", main_branch]),
        ("rules-acknowledge", [agentic_kit, "rules", "acknowledge"]),
        ("post-merge-complete", [agentic_kit, "transfer", "post-merge-complete", "--after-pr", str(pr_number)]),
    ]

    failed_step = None
    for name, argv in step_plan:
        if name == "pr-wait-ci":
            update_parent_live_status("waiting_ci", step=name)
        elif name == "pr-merge-safe":
            update_parent_live_status("merging", step=name)
        else:
            update_parent_live_status("post_merge", step=name)
        step_returncode = run_step(name, argv)
        if step_returncode != 0:
            if name == "pr-wait-ci" and pr_status_allows_wait_ci_fallback():
                continue
            failed_step = name
            break

    post_merge_complete_followup_required = False
    if failed_step == "post-merge-complete" and pr_is_merged_after_post_merge_complete_failure():
        followup_ok, followup_blocker = run_admin_refresh_followup_if_needed()
        if followup_ok:
            failed_step = None
            post_merge_complete_followup_required = True
        else:
            failed_step = followup_blocker or "post-merge-complete_followup_failed"

    result_status = "PASS" if failed_step is None else "BLOCKED"
    update_parent_live_status(
        "done" if result_status == "PASS" else "blocked",
        result_status=result_status,
        step="pr-complete",
        failed_step=failed_step or "",
    )
    final_signal = "d" if result_status == "PASS" else "f"
    if failed_step is None:
        if post_merge_complete_followup_required:
            next_action = (
                "PR is merged and required administrative handoff refresh PR was "
                "created, completed, and verified by post-merge-check."
            )
        else:
            next_action = "PR completion lifecycle is complete."
        returncode = 0
    else:
        next_action = f"Inspect pr-complete step failure before continuing: {failed_step}."
        returncode = 2

    payload = {
        "schema_version": 1,
        "kind": "transfer_pr_complete_result",
        "action": "pr-complete",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "pr_number": pr_number,
        "expected_head_sha": resolved_head_sha,
        "main_branch": main_branch,
        "merge_method": merge_method,
        "timeout_seconds": timeout_seconds,
        "poll_seconds": poll_seconds,
        "result_status": result_status,
        "final_signal": final_signal,
        "failed_step": failed_step,
        "post_merge_complete_followup_required": post_merge_complete_followup_required,
        "steps": steps,
        "next_action": next_action,
    }

    if json_output:
        typer.echo(json.dumps(payload, indent=2, sort_keys=True))
    else:
        typer.echo("*" * 36 + " START SUMMARY " + "*" * 36)
        typer.echo("TRANSFER_PR_COMPLETE")
        typer.echo("")
        typer.echo(_summary_line("STATE", result_status))
        typer.echo(_summary_line("RETURNCODE", returncode))
        typer.echo("")
        typer.echo("LIFECYCLE")
        typer.echo(_summary_line("- PR", pr_number))
        typer.echo(_summary_line("- FAILED_STEP", failed_step or "none"))
        typer.echo(_summary_line("- STEPS", len(steps)))
        typer.echo("")
        typer.echo(_summary_line("NEXT", next_action))
        typer.echo(_summary_line("CHAT_REPLY", f"{final_signal} | NEXT={next_action}"))
        typer.echo("*" * 35 + " END SUMMARY " + "*" * 36)

    if returncode != 0:
        raise typer.Exit(code=returncode)


__all__ = [name for name in globals() if not name.startswith("__")]
