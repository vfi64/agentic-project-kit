from __future__ import annotations

import sys
# ruff: noqa: F403,F405

from agentic_project_kit.cli_commands.transfer_shared import *
from agentic_project_kit.cli_commands.transfer_context_helpers import *
from agentic_project_kit.cli_commands.transfer_pr_merge_flow import _resolve_expected_head_sha_alias



def _auto_preflight_pr_create_complete(*, root: Path) -> None:
    """Prepare rule/context carriers before pr-create-complete mutates GitHub state."""

    # Isolated CliRunner fixtures may not be real Git worktrees. In that case,
    # do not shadow the canonical fresh-LLM-context gate with rule/context
    # repair blockers from the auto-preflight.
    if not (root / ".git").exists():
        return

    def run_step(
        name: str,
        command: list[str],
        *,
        allow_nonzero: bool = False,
    ) -> subprocess.CompletedProcess[str]:
        completed = subprocess.run(
            command,
            cwd=root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if completed.returncode != 0 and not allow_nonzero:
            typer.echo(
                {
                    "result_status": "BLOCKED",
                    "blocker": name,
                    "returncode": completed.returncode,
                    "stdout": completed.stdout,
                    "stderr": completed.stderr,
                    "next_action": "Fix the automatic pr-create-complete preflight blocker before PR creation.",
                }
            )
            raise typer.Exit(code=2)
        return completed

    # Rule acknowledgement can be unavailable in isolated test fixtures. Do not let it
    # shadow the canonical fresh-LLM-context gate; the later gate remains authoritative.
    run_step(
        "rules_acknowledge",
        [
            sys.executable,
            "-m",
            "agentic_project_kit.cli",
            "rules",
            "acknowledge",
            "--json",
        ],
        allow_nonzero=True,
    )
    run_step(
        "refresh_llm_context_carriers",
        [
            sys.executable,
            "-m",
            "agentic_project_kit.cli",
            "transfer",
            "refresh-llm-context-carriers",
            "--json",
        ],
        allow_nonzero=True,
    )
    run_step(
        "require_fresh_llm_context",
        [
            sys.executable,
            "-m",
            "agentic_project_kit.cli",
            "transfer",
            "require-fresh-llm-context",
            "--json",
        ],
        allow_nonzero=True,
    )

    for rel_path in sorted(
        {
            Path("docs/reports/terminal/transfer_handoff_reports/latest-transfer-handoff-report.json"),
            Path("docs/reports/terminal/transfer_handoff_reports/latest-transfer-handoff-report.log"),
        }
    ):
        run_step(
            "restore_known_volatile_tracked_carrier",
            ["git", "restore", "--", str(rel_path)],
            allow_nonzero=True,
        )

    status_result = run_step("git_status", ["git", "status", "--porcelain"], allow_nonzero=True)
    if status_result.returncode != 0:
        return
    status = status_result.stdout.splitlines()
    unexpected_dirt: list[str] = []
    for line in status:
        if not line:
            continue
        marker = line[:2]
        rel = line[3:]
        if marker == "??" and (rel.startswith("tmp/") or rel == ".agentic/transfer/outbox/last_result.txt"):
            continue
        if rel in {
            "docs/reports/terminal/transfer_handoff_reports/latest-transfer-handoff-report.json",
            "docs/reports/terminal/transfer_handoff_reports/latest-transfer-handoff-report.log",
        }:
            continue
        unexpected_dirt.append(line)

    if unexpected_dirt:
        typer.echo(
            {
                "result_status": "BLOCKED",
                "blocker": "unexpected_dirt_after_pr_create_complete_preflight",
                "unexpected_dirt": unexpected_dirt,
                "next_action": "Review unexpected dirt before PR creation.",
            }
        )
        raise typer.Exit(code=2)



@transfer_app.command("pr-create")
def pr_create_command(
    base: str = typer.Option("main", "--base", help="Base branch."),
    head: str = typer.Option(..., "--head", help="Head branch."),
    title: str = typer.Option(..., "--title", help="Pull request title."),
    body: str = typer.Option("", "--body", help="Pull request body."),
    json_output: bool = typer.Option(False, "--json", help="Print JSON instead of text."),
    skip_llm_context_gate: bool = typer.Option(
        False,
        "--skip-llm-context-gate",
        help="Recovery-only: create PR without requiring fresh generated LLM context.",
    ),
) -> None:
    if not skip_llm_context_gate:
        require_fresh = _public_transfer_attr("_require_fresh_llm_context_or_exit", _require_fresh_llm_context_or_exit)
        require_fresh(max_age_minutes=60, json_output=json_output)
    resolved_head = head
    if head == "current":
        import subprocess

        completed = subprocess.run(["git", "branch", "--show-current"], text=True, capture_output=True)
        resolved_head = completed.stdout.strip()
        if completed.returncode != 0 or not resolved_head:
            payload = {
                "action": "pr-create",
                "result_status": "BLOCKED",
                "final_signal": "f",
                "next_action": "Resolve current branch before creating a PR.",
                "blockers": ["current_branch_missing"],
                "stderr": completed.stderr,
            }
            typer.echo(json.dumps(payload, indent=2, sort_keys=True) if json_output else "PR_CREATE_BLOCKED\nreason=current_branch_missing")
            raise typer.Exit(code=2)
    require_capability = _public_transfer_attr("_require_transfer_capability", _require_transfer_capability)
    require_capability("rules_confirmed")
    create_pr = _public_transfer_attr("pr_create", pr_create)
    result = create_pr(base=base, head=resolved_head, title=title, body=body)
    echo_repo_result = _public_transfer_attr("_echo_repo_result", _echo_repo_result)
    echo_repo_result(result, json_output)
    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)

@transfer_app.command("pr-existing-for-branch")
def pr_existing_for_branch_command(
    head: str = typer.Option(
        "current",
        "--head",
        help="Head branch to look up. Use current to resolve git branch --show-current.",
    ),
    base: str = typer.Option("main", "--base", help="Base branch to match."),
    state: str = typer.Option("all", "--state", help="GitHub PR state filter."),
    json_output: bool = typer.Option(False, "--json", help="Print JSON instead of text report."),
) -> None:
    import subprocess
    from datetime import datetime, timezone

    steps: list[dict[str, object]] = []
    blockers: list[str] = []
    resolved_head = head

    def run_step(name: str, argv: list[str]) -> subprocess.CompletedProcess[str]:
        completed = subprocess.run(argv, text=True, capture_output=True, check=False)
        steps.append(
            {
                "name": name,
                "argv": argv,
                "returncode": completed.returncode,
                "stdout": completed.stdout,
                "stderr": completed.stderr,
                "ok": completed.returncode == 0,
            }
        )
        return completed

    if head == "current":
        branch_result = run_step("resolve-current-branch", ["git", "branch", "--show-current"])
        resolved_head = branch_result.stdout.strip()
        if branch_result.returncode != 0 or not resolved_head:
            blockers.append("current_branch_missing")

    prs: list[dict[str, object]] = []
    parse_error = ""
    if not blockers:
        lookup_result = run_step(
            "gh-pr-list",
            [
                "gh",
                "pr",
                "list",
                "--head",
                resolved_head,
                "--base",
                base,
                "--state",
                state,
                "--json",
                "number,url,state,headRefName,baseRefName,isDraft,mergeStateStatus",
            ],
        )
        if lookup_result.returncode != 0:
            blockers.append("gh_pr_list_failed")
        else:
            try:
                raw = json.loads(lookup_result.stdout or "[]")
                if isinstance(raw, list):
                    prs = [item for item in raw if isinstance(item, dict)]
                else:
                    blockers.append("pr_lookup_output_not_list")
            except json.JSONDecodeError as exc:
                parse_error = str(exc)
                blockers.append("pr_lookup_json_invalid")

    if blockers:
        result_status = "FAIL" if "gh_pr_list_failed" in blockers else "BLOCKED"
        returncode = 1 if result_status == "FAIL" else 2
        pr_number = None
    elif len(prs) == 1:
        result_status = "PASS"
        returncode = 0
        pr_number = prs[0].get("number")
    elif len(prs) == 0:
        result_status = "MISS"
        returncode = 2
        pr_number = None
        blockers.append("existing_pr_not_found")
    else:
        result_status = "BLOCKED"
        returncode = 2
        pr_number = None
        blockers.append("multiple_existing_prs_found")

    blockers = list(dict.fromkeys(blockers))
    final_signal = "d" if result_status == "PASS" else "f"
    if result_status == "PASS":
        next_action = "Existing PR found; run transfer pr-status with the reported PR number if needed."
    elif result_status == "MISS":
        next_action = "No existing PR found for the requested branch."
    else:
        next_action = "Inspect pr-existing-for-branch lookup result before continuing: " + ", ".join(blockers)

    payload = {
        "schema_version": 1,
        "kind": "transfer_pr_existing_for_branch_result",
        "action": "pr-existing-for-branch",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "result_status": result_status,
        "final_signal": final_signal,
        "next_action": next_action,
        "base": base,
        "head": resolved_head,
        "state": state,
        "pr_number": pr_number,
        "prs": prs,
        "blockers": blockers,
        "parse_error": parse_error,
        "steps": steps,
    }

    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        _echo_transfer_payload_summary(
            title="TRANSFER_PR_EXISTING_FOR_BRANCH",
            result_status=result_status,
            final_signal=final_signal,
            next_action=next_action,
            fields={
                "HEAD": resolved_head,
                "BASE": base,
                "STATE_FILTER": state,
                "PR": pr_number if pr_number is not None else "none",
                "MATCHES": len(prs),
                "BLOCKERS": len(blockers),
            },
        )

    if returncode != 0:
        raise typer.Exit(code=returncode)

@transfer_app.command("pr-create-complete")
def pr_create_complete_command(
    title: str = typer.Option(..., "--title", help="Pull request title."),
    body: str = typer.Option("", "--body", help="Pull request body."),
    base: str = typer.Option("main", "--base", help="Base branch."),
    head: str = typer.Option(
        "current",
        "--head",
        help="Head branch. Use current to resolve git branch --show-current.",
    ),
    merge_method: str = typer.Option("squash", "--merge-method", help="GitHub merge method."),
    timeout_seconds: int = typer.Option(300, "--timeout-seconds", min=1, help="Maximum CI wait time."),
    poll_seconds: int = typer.Option(
        10,
        "--interval-seconds",
        "--poll-seconds",
        min=1,
        help="CI polling interval.",
    ),
    post_merge_complete: bool = typer.Option(
        False,
        "--post-merge-complete",
        help="After pr-complete, run visible post-merge closeout using the concrete PR number.",
    ),
    json_output: bool = typer.Option(False, "--json", help="Print JSON instead of text."),
    skip_llm_context_gate: bool = typer.Option(
        False,
        "--skip-llm-context-gate",
        help="Recovery-only: run PR create/complete without requiring fresh generated LLM context.",
    ),
) -> None:
    """Create a PR and complete it without requiring manual PR-number or SHA copying."""
    if not skip_llm_context_gate:
        _auto_preflight_pr_create_complete(root=Path("."))
        require_fresh = _public_transfer_attr("_require_fresh_llm_context_or_exit", _require_fresh_llm_context_or_exit)
        require_fresh(max_age_minutes=60, json_output=json_output)
    require_communication_context = _public_transfer_attr(
        "_require_current_communication_context_or_exit",
        _require_current_communication_context_or_exit,
    )
    require_communication_context(
        json_output=json_output,
        allow_rule_carrier_publish=True,
    )

    import os
    import re
    import subprocess
    from datetime import datetime, timezone

    require_capability = _public_transfer_attr("_require_transfer_capability", _require_transfer_capability)
    require_capability("rules_confirmed")

    agentic_kit = "./.venv/bin/agentic-kit"
    steps: list[dict[str, object]] = []
    blockers: list[str] = []
    resolved_head = "" if head == "current" else head
    expected_head_sha = ""
    pr_number: int | None = None

    def update_live_status(
        phase: wrapper_live_status.WrapperPhase,
        *,
        result_status: str = "RUNNING",
        step: str = "",
        message: str = "",
    ) -> None:
        wrapper_live_status.write_wrapper_live_status(
            Path("."),
            wrapper="pr-create-complete",
            phase=phase,
            result_status=result_status,
            base=base,
            head=resolved_head,
            expected_head_sha=expected_head_sha,
            pr_number=pr_number,
            blockers=blockers,
            step=step,
            message=message,
        )

    update_live_status("starting", step="start")

    def run_step(
        name: str,
        argv: list[str],
        *,
        env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        completed = subprocess.run(argv, text=True, capture_output=True, env=env)
        step_payload_status = ""
        try:
            from agentic_project_kit.release_process_guardrails import (
                is_transfer_result_payload,
                rc_from_result_payload,
            )

            parsed = json.loads(completed.stdout or "{}")
            if isinstance(parsed, dict) and is_transfer_result_payload(parsed):
                derived_rc = rc_from_result_payload(parsed)
                step_payload_status = str(parsed.get("result_status", parsed.get("status", "")))
                if completed.returncode == 0 and derived_rc != 0:
                    blockers.append(name + "_blocked_payload")
        except Exception as exc:  # noqa: BLE001 - diagnostic parsing must not hide the wrapped command result.
            step_payload_status = f"payload_parse_unavailable:{type(exc).__name__}"

        steps.append(
            {
                "name": name,
                "argv": argv,
                "returncode": completed.returncode,
                "stdout": completed.stdout,
                "stderr": completed.stderr,
                "ok": completed.returncode == 0,
                "payload_status": step_payload_status,
            }
        )
        if completed.returncode != 0:
            blockers.append(name + "_failed")
        return completed

    def post_merge_complete_verified_by_inner_pr_complete(stdout: str) -> bool:
        try:
            payload = json.loads(stdout or "{}")
        except json.JSONDecodeError:
            return False
        if not isinstance(payload, dict):
            return False
        return (
            payload.get("result_status") == "PASS"
            and payload.get("post_merge_complete_followup_required") is True
            and "created, completed, and verified" in str(payload.get("next_action", ""))
        )

    def pr_is_merged_for_outer_followup() -> bool:
        if pr_number is None:
            return False
        command = ["gh", "pr", "view", str(pr_number), "--json", "state,mergedAt,mergeCommit"]
        completed = subprocess.run(command, text=True, capture_output=True)
        steps.append(
            {
                "name": "outer-followup-pr-merged-check",
                "argv": command,
                "returncode": completed.returncode,
                "stdout": completed.stdout,
                "stderr": completed.stderr,
                "ok": completed.returncode == 0,
            }
        )
        if completed.returncode != 0:
            return False
        try:
            payload = json.loads(completed.stdout or "{}")
        except json.JSONDecodeError:
            return False
        if not isinstance(payload, dict):
            return False
        return bool(payload.get("mergedAt")) or str(payload.get("state", "")).upper() == "MERGED"

    def post_merge_check_is_green_for_outer_followup() -> bool:
        sync_command = [agentic_kit, "transfer", "sync-main"]
        sync = subprocess.run(sync_command, text=True, capture_output=True)
        steps.append(
            {
                "name": "outer-followup-sync-main-before-post-merge-check",
                "argv": sync_command,
                "returncode": sync.returncode,
                "stdout": sync.stdout,
                "stderr": sync.stderr,
                "ok": sync.returncode == 0,
            }
        )
        if sync.returncode != 0:
            return False

        command = [agentic_kit, "transfer", "post-merge-check"]
        completed = subprocess.run(command, text=True, capture_output=True)
        steps.append(
            {
                "name": "outer-followup-post-merge-check-green-check",
                "argv": command,
                "returncode": completed.returncode,
                "stdout": completed.stdout,
                "stderr": completed.stderr,
                "ok": completed.returncode == 0,
            }
        )
        combined = f"{completed.stdout}\n{completed.stderr}"
        if completed.returncode != 0:
            return False
        return any(
            marker in combined
            for marker in (
                "STATE:                  PASS",
                '"result_status": "PASS"',
                "result=NOOP",
                "STATE=PASS",
            )
        )

    def outer_followup_false_red_is_safe_to_clear() -> bool:
        return pr_is_merged_for_outer_followup() and post_merge_check_is_green_for_outer_followup()

    if head == "current":
        branch_result = run_step("resolve-current-branch", ["git", "branch", "--show-current"])
        resolved_head = branch_result.stdout.strip()
        if not resolved_head:
            blockers.append("current_branch_missing")
    else:
        resolved_head = head

    sha_result = run_step("resolve-current-head-sha", ["git", "rev-parse", "HEAD"])
    expected_head_sha = sha_result.stdout.strip()
    if not re.fullmatch(r"[0-9a-fA-F]{40}", expected_head_sha):
        blockers.append("current_head_sha_invalid")

    inner_post_merge_followup_verified = False
    if not blockers:
        update_live_status("creating_pr", step="pr-create")
        create_result = run_step(
            "pr-create",
            [
                agentic_kit,
                "transfer",
                "pr-create",
                "--title",
                title,
                "--body",
                body,
                "--base",
                base,
                "--head",
                resolved_head,
                "--skip-llm-context-gate",
                "--json",
            ],
        )

        if create_result.returncode == 0:
            match = re.search(r"/pull/(\d+)", create_result.stdout)
            if match:
                pr_number = int(match.group(1))
            else:
                blockers.append("pr_number_not_found_in_pr_create_output")
        else:
            existing = run_step(
                "pr-existing-for-branch",
                [
                    "gh",
                    "pr",
                    "view",
                    "--head",
                    resolved_head,
                    "--base",
                    base,
                    "--json",
                    "number",
                    "-q",
                    ".number",
                ],
            )
            if existing.returncode == 0 and existing.stdout.strip().isdigit():
                pr_number = int(existing.stdout.strip())
                blockers = [b for b in blockers if b != "pr-create_failed"]
            else:
                blockers.append("existing_pr_number_not_found")

    if pr_number is not None and not blockers:
        update_live_status("waiting_ci", step="pr-complete")
        complete_argv = [
            agentic_kit,
            "transfer",
            "pr-complete",
            str(pr_number),
            "--expected-head-sha",
            expected_head_sha,
            "--merge-method",
            merge_method,
            "--timeout-seconds",
            str(timeout_seconds),
            "--interval-seconds",
            str(poll_seconds),
        ]
        if skip_llm_context_gate:
            complete_argv.append("--skip-llm-context-gate")
        complete_argv.append("--json")
        child_env = os.environ.copy()
        child_env.update(
            {
                "AGENTIC_KIT_WRAPPER_LIVE_STATUS_PARENT": "pr-create-complete",
                "AGENTIC_KIT_WRAPPER_LIVE_STATUS_BASE": base,
                "AGENTIC_KIT_WRAPPER_LIVE_STATUS_HEAD": resolved_head,
                "AGENTIC_KIT_WRAPPER_LIVE_STATUS_EXPECTED_HEAD_SHA": expected_head_sha,
            }
        )
        complete_result = run_step("pr-complete", complete_argv, env=child_env)
        inner_post_merge_followup_verified = post_merge_complete_verified_by_inner_pr_complete(
            complete_result.stdout
        )
        if not blockers:
            run_step(
                "restore-known-volatile-after-pr-complete",
                [agentic_kit, "transfer", "restore-known-volatile", "--json"],
            )

    if (
        pr_number is not None
        and post_merge_complete
        and not blockers
        and not inner_post_merge_followup_verified
    ):
        # pr-complete already runs the concrete post-merge-complete lifecycle after
        # a successful merge. The outer pr-create-complete wrapper must not run it
        # a second time, because a successful admin-refresh PR can make the repeated
        # closeout look like a new failure even though the lifecycle is already done.
        update_live_status("post_merge", step="outer-post-merge-followup")
        post_merge_steps = [
            ("post-pr-sync-main-after-complete", [agentic_kit, "transfer", "sync-main"]),
            ("post-pr-post-merge-check", [agentic_kit, "transfer", "post-merge-check"]),
            ("post-pr-repo-status", [agentic_kit, "transfer", "repo-status"]),
        ]
        for name, argv in post_merge_steps:
            run_step(name, argv)
            if blockers:
                break
        if not blockers:
            run_step(
                "restore-known-volatile-after-post-merge-followup",
                [agentic_kit, "transfer", "restore-known-volatile", "--json"],
            )

    blockers = list(dict.fromkeys(blockers))
    outer_followup_false_red_cleared = False
    if blockers and post_merge_complete and outer_followup_false_red_is_safe_to_clear():
        blockers = []
        outer_followup_false_red_cleared = True

    result_status = "PASS" if not blockers else "BLOCKED"
    update_live_status(
        "done" if result_status == "PASS" else "blocked",
        result_status=result_status,
        step="complete",
    )
    final_signal = "d" if result_status == "PASS" else "f"
    if result_status == "PASS" and inner_post_merge_followup_verified:
        next_action = (
            "PR create-complete lifecycle is complete; inner pr-complete already "
            "created, completed, and verified the administrative handoff refresh."
        )
    elif result_status == "PASS" and outer_followup_false_red_cleared:
        next_action = (
            "PR create-complete lifecycle is complete; outer post-merge follow-up "
            "had a non-fatal sync/restore failure, but the PR is merged and "
            "post-merge-check is green."
        )
    else:
        next_action = (
            "PR create-complete lifecycle is complete."
            if result_status == "PASS"
            else "Inspect pr-create-complete step failure before continuing: " + ", ".join(blockers)
        )

    payload = {
        "schema_version": 1,
        "kind": "transfer_pr_create_complete_result",
        "action": "pr-create-complete",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "result_status": result_status,
        "final_signal": final_signal,
        "next_action": next_action,
        "base": base,
        "head": resolved_head,
        "expected_head_sha": expected_head_sha,
        "pr_number": pr_number,
        "post_merge_complete_verified_by_inner_pr_complete": inner_post_merge_followup_verified,
        "outer_followup_false_red_cleared": outer_followup_false_red_cleared,
        "blockers": blockers,
        "steps": steps,
    }

    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        _echo_transfer_payload_summary(
            title="TRANSFER_PR_CREATE_COMPLETE",
            result_status=result_status,
            final_signal=final_signal,
            next_action=next_action,
            fields={
                "PR": pr_number if pr_number is not None else "none",
                "HEAD": resolved_head,
                "BASE": base,
                "STEPS": len(steps),
                "BLOCKERS": len(blockers),
            },
        )

    if blockers:
        raise typer.Exit(code=2)

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


__all__ = [name for name in globals() if not name.startswith("__")]
