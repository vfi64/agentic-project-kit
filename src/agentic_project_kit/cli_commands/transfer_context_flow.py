from __future__ import annotations

# ruff: noqa: F403,F405

from agentic_project_kit.cli_commands.transfer_shared import *
from agentic_project_kit.cli_commands.transfer_context_helpers import *


@transfer_app.command("require-fresh-llm-context")
def require_fresh_llm_context(
    max_age_minutes: int = typer.Option(
        60,
        "--max-age-minutes",
        min=1,
        help="Maximum acceptable age of generated LLM context.",
    ),
    allow_clean_post_merge_carrier_staleness: bool = typer.Option(
        False,
        "--allow-clean-post-merge-carrier-staleness",
        help="Downgrade stale volatile LLM-context carrier state to WARN when post-merge-check is NOOP and the worktree is clean.",
    ),
    json_output: bool = typer.Option(False, "--json", help="Print JSON instead of text."),
) -> None:
    """Require fresh generated LLM context before transfer planning."""
    evaluate = _public_transfer_attr("_evaluate_llm_context_freshness", _evaluate_llm_context_freshness)
    payload = evaluate(
        Path("."),
        max_age_minutes=max_age_minutes,
        allow_clean_post_merge_carrier_staleness=allow_clean_post_merge_carrier_staleness,
    )
    _emit_llm_context_gate_result(payload, json_output=json_output)
    if payload.get("result_status") == "BLOCKED":
        raise typer.Exit(code=2)

@transfer_app.command("verify-llm-context-refresh")
def verify_llm_context_refresh(
    json_output: bool = typer.Option(False, "--json", help="Print JSON instead of text."),
) -> None:
    blockers: list[str] = []
    checked: dict[str, dict[str, object]] = {}

    paths = {
        "outbox": Path(".agentic/transfer/outbox/last_result.txt"),
        "latest_handoff_report": Path("docs/reports/terminal/transfer_handoff_reports/latest-transfer-handoff-report.json"),
    }
    required_context_keys = [
        "source_hashes",
        "context_quality",
        "running_chat_refresh_contract",
        "shell_placeholder_policy",
        "terminal_resilience",
        "patch_generation_policy",
        "llm_to_local_transfer_policy",
        "command_integration_governance",
    ]
    required_markers = [
        "agentic-kit transfer pr-create-complete --post-merge-complete",
        "verify-llm-context-refresh",
    ]
    forbidden_fragments = ["<PR_NUMMER>", "<PR_NUMBER>"]

    for name, path in paths.items():
        status: dict[str, object] = {"path": str(path), "exists": path.exists()}
        checked[name] = status
        if not path.exists():
            blockers.append(name + "_missing")
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            status["json_error"] = str(exc)
            blockers.append(name + "_json_invalid")
            continue
        if not isinstance(data, dict):
            blockers.append(name + "_not_object")
            continue
        ctx = data.get("llm_execution_context")
        status["llm_execution_context_present"] = isinstance(ctx, dict)
        if not isinstance(ctx, dict):
            blockers.append(name + "_llm_execution_context_missing")
            continue
        ctx_text = json.dumps(ctx, sort_keys=True, ensure_ascii=False)
        missing_keys = [key for key in required_context_keys if key not in ctx]
        missing_markers = [marker for marker in required_markers if marker not in ctx_text]
        forbidden_hits = [fragment for fragment in forbidden_fragments if fragment in ctx_text]
        status["missing_context_keys"] = missing_keys
        status["missing_markers"] = missing_markers
        status["forbidden_fragments"] = forbidden_hits
        if missing_keys:
            blockers.append(name + "_context_keys_missing")
        if missing_markers:
            blockers.append(name + "_markers_missing")
        if forbidden_hits:
            blockers.append(name + "_forbidden_placeholder_present")

    blockers = list(dict.fromkeys(blockers))
    result_status = "PASS" if not blockers else "BLOCKED"
    final_signal = "d" if result_status == "PASS" else "f"
    next_action = (
        "LLM context refresh is current for running-chat and successor-chat drift control."
        if result_status == "PASS"
        else "Regenerate transfer outbox/latest handoff report before planning: " + ", ".join(blockers)
    )
    payload = {
        "schema_version": 1,
        "kind": "transfer_verify_llm_context_refresh_result",
        "action": "verify-llm-context-refresh",
        "result_status": result_status,
        "final_signal": final_signal,
        "next_action": next_action,
        "blockers": blockers,
        "checked": checked,
    }

    if json_output:
        typer.echo(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False))
    else:
        _echo_transfer_payload_summary(
            title="TRANSFER_VERIFY_LLM_CONTEXT_REFRESH",
            result_status=result_status,
            final_signal=final_signal,
            next_action=next_action,
            fields={
                "OUTBOX_CONTEXT": checked.get("outbox", {}).get("llm_execution_context_present", False),
                "LATEST_CONTEXT": checked.get("latest_handoff_report", {}).get("llm_execution_context_present", False),
                "BLOCKERS": len(blockers),
            },
        )

    if blockers:
        raise typer.Exit(code=2)

@transfer_app.command("refresh-llm-context-carriers")
def refresh_llm_context_carriers_command(
    json_output: bool = typer.Option(False, "--json", help="Print JSON instead of text."),
) -> None:
    """Refresh outbox and latest handoff report with fresh generated LLM context."""
    try:
        refresh = _public_transfer_attr("refresh_llm_context_carriers", refresh_llm_context_carriers)
        payload = refresh(Path("."))
    except (FileNotFoundError, ValueError, OSError) as exc:
        payload = {
            "schema_version": 1,
            "kind": "llm_context_carriers_refresh_result",
            "action": "refresh-llm-context-carriers",
            "result_status": "BLOCKED",
            "final_signal": "f",
            "next_action": f"Inspect LLM context carrier refresh failure: {exc}",
            "error": str(exc),
        }
        typer.echo(json.dumps(payload, indent=2, sort_keys=True) if json_output else f"REFRESH_LLM_CONTEXT_CARRIERS_BLOCKED\nerror={exc}")
        raise typer.Exit(code=2) from exc

    if json_output:
        typer.echo(json.dumps(payload, indent=2, sort_keys=True))
    else:
        _echo_transfer_payload_summary(
            title="TRANSFER_REFRESH_LLM_CONTEXT_CARRIERS",
            result_status=str(payload["result_status"]),
            final_signal=str(payload["final_signal"]),
            next_action=str(payload["next_action"]),
            fields={
                "OUTBOX": payload["outbox_path"],
                "LATEST": payload["latest_handoff_report_path"],
            },
        )

@transfer_app.command("restore-known-volatile")
def restore_known_volatile(
    json_output: bool = typer.Option(False, "--json", help="Print machine-readable JSON only."),
) -> None:
    """Restore the canonical known volatile transfer files."""
    result = _restore_known_volatile_paths(Path("."))
    status = "PASS" if result["ok"] else "FAIL"
    final_signal = "d" if result["ok"] else "f"
    next_action = (
        "Known volatile transfer files restored."
        if result["ok"]
        else "Inspect restore-known-volatile failure before continuing."
    )
    payload = {
        "schema_version": 1,
        "kind": "transfer_restore_known_volatile_result",
        "action": "restore-known-volatile",
        "result_status": status,
        "final_signal": final_signal,
        "next_action": next_action,
        "known_paths": KNOWN_VOLATILE_TRANSFER_PATHS,
        "result": result,
    }
    _echo_transfer_payload_json_or_summary(
        payload,
        json_output=json_output,
        title="TRANSFER_RESTORE_KNOWN_VOLATILE",
    )
    if not result["ok"]:
        raise typer.Exit(code=1)

@transfer_app.command("divergence-status")
def divergence_status(
    json_output: bool = typer.Option(False, "--json", help="Print machine-readable JSON only."),
) -> None:
    """Report local/upstream divergence without mutating repository state."""
    branch_result = _run_transfer_subprocess(["git", "branch", "--show-current"])
    head_result = _run_transfer_subprocess(["git", "rev-parse", "HEAD"])
    upstream_result = _run_transfer_subprocess(["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"])
    upstream_head_result = (
        _run_transfer_subprocess(["git", "rev-parse", "@{u}"])
        if upstream_result["ok"]
        else {"argv": ["git", "rev-parse", "@{u}"], "returncode": 1, "stdout": "", "stderr": "no upstream", "ok": False}
    )
    counts_result = (
        _run_transfer_subprocess(["git", "rev-list", "--left-right", "--count", "HEAD...@{u}"])
        if upstream_result["ok"]
        else {"argv": ["git", "rev-list", "--left-right", "--count", "HEAD...@{u}"], "returncode": 1, "stdout": "", "stderr": "no upstream", "ok": False}
    )
    ahead = behind = None
    if counts_result["ok"]:
        parts = str(counts_result["stdout"]).strip().split()
        if len(parts) == 2:
            ahead = int(parts[0])
            behind = int(parts[1])
    head = str(head_result["stdout"]).strip()
    upstream_head = str(upstream_head_result["stdout"]).strip() if upstream_head_result["ok"] else ""
    status = "PASS" if branch_result["ok"] and head_result["ok"] else "FAIL"
    final_signal = "d" if status == "PASS" else "f"
    next_action = "Divergence status reported; inspect ahead/behind before mutating branches."
    payload = {
        "schema_version": 1,
        "kind": "transfer_divergence_status_result",
        "action": "divergence-status",
        "result_status": status,
        "final_signal": final_signal,
        "next_action": next_action,
        "repo": {
            "branch": str(branch_result["stdout"]).strip(),
            "head": head,
            "upstream": str(upstream_result["stdout"]).strip() if upstream_result["ok"] else "",
            "upstream_head": upstream_head,
            "head_matches_upstream": bool(head and upstream_head and head == upstream_head),
            "ahead": ahead,
            "behind": behind,
        },
        "commands": {
            "branch": branch_result,
            "head": head_result,
            "upstream": upstream_result,
            "upstream_head": upstream_head_result,
            "ahead_behind": counts_result,
        },
    }
    _echo_transfer_payload_json_or_summary(payload, json_output=json_output)
    if status != "PASS":
        raise typer.Exit(code=1)

@transfer_app.command("sync-main")
def sync_main(
    main_branch: str = typer.Option("main", "--main-branch", help="Main branch to synchronize."),
    json_output: bool = typer.Option(False, "--json", help="Print machine-readable JSON only."),
) -> None:
    """Synchronize main, acknowledge rules, and normalize the session."""
    steps: list[dict[str, object]] = []

    def step(name: str, argv: list[str]) -> dict[str, object]:
        item = _run_transfer_subprocess(argv)
        item["name"] = name
        steps.append(item)
        return item

    step("restore-before-sync", ["./.venv/bin/agentic-kit", "transfer", "restore-known-volatile", "--json"])
    step("rules-acknowledge-before-sync", ["./.venv/bin/agentic-kit", "rules", "acknowledge"])
    step("switch-and-pull-main", ["./.venv/bin/agentic-kit", "transfer", "branch-switch", main_branch, "--pull"])
    step("rules-acknowledge-after-pull", ["./.venv/bin/agentic-kit", "rules", "acknowledge"])
    step("normalize-session", ["./.venv/bin/agentic-kit", "transfer", "normalize-session", "--repair-known-volatile"])

    blockers = [str(item["name"]) + "_failed" for item in steps if item["returncode"] != 0]
    status = "PASS" if not blockers else "FAIL"
    final_signal = "d" if status == "PASS" else "f"
    next_action = (
        "Main synchronized and session normalized."
        if status == "PASS"
        else "Inspect sync-main blockers before continuing: " + ", ".join(blockers)
    )
    payload = {
        "schema_version": 1,
        "kind": "transfer_sync_main_result",
        "action": "sync-main",
        "main_branch": main_branch,
        "result_status": status,
        "final_signal": final_signal,
        "next_action": next_action,
        "blockers": blockers,
        "steps": steps,
    }
    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        _echo_transfer_payload_summary(
            title="TRANSFER_SYNC_MAIN",
            result_status=status,
            final_signal=final_signal,
            next_action=next_action,
            fields={
                "MAIN_BRANCH": main_branch,
                "BLOCKERS": len(blockers),
                "STEPS": len(steps),
            },
        )
    if blockers:
        raise typer.Exit(code=1)

@transfer_app.command("command-reference-refresh")
def command_reference_refresh(
    json_output: bool = typer.Option(False, "--json", help="Print machine-readable JSON only."),
) -> None:
    """Regenerate the agentic-kit command reference without committing changes."""
    script_result = _run_transfer_subprocess(
        ["./.venv/bin/python", "scripts/generate_agentic_kit_command_reference.py"]
    )
    status_result = _run_transfer_subprocess(["git", "status", "--short"])
    diff_result = _run_transfer_subprocess(
        [
            "git",
            "diff",
            "--name-only",
            "--",
            "docs/reference/agentic-kit-commands.json",
            "docs/reference/AGENTIC_KIT_COMMANDS.md",
        ]
    )
    changed_files = [
        line.strip()
        for line in str(diff_result["stdout"]).splitlines()
        if line.strip()
    ]
    result_status = "PASS" if script_result["ok"] and status_result["ok"] and diff_result["ok"] else "FAIL"
    final_signal = "d" if result_status == "PASS" else "f"
    next_action = (
        "Command reference regenerated; inspect changed reference files."
        if result_status == "PASS"
        else "Inspect command-reference-refresh failure before continuing."
    )
    payload = {
        "schema_version": 1,
        "kind": "transfer_command_reference_refresh_result",
        "action": "command-reference-refresh",
        "result_status": result_status,
        "final_signal": final_signal,
        "next_action": next_action,
        "changed_files": changed_files,
        "commands": {
            "generate": script_result,
            "status": status_result,
            "diff_name_only": diff_result,
        },
    }
    _echo_transfer_payload_json_or_summary(payload, json_output=json_output)
    if result_status != "PASS":
        raise typer.Exit(code=1)

@transfer_app.command("command-reference-check")
def command_reference_check(
    json_output: bool = typer.Option(False, "--json", help="Print machine-readable JSON only."),
) -> None:
    """Check whether the committed agentic-kit command reference is current."""
    check_result = _run_transfer_subprocess(
        [
            "./.venv/bin/python",
            "-m",
            "pytest",
            "-q",
            "tests/test_agentic_kit_command_reference_is_current.py",
        ]
    )
    result_status = "PASS" if check_result["ok"] else "FAIL"
    final_signal = "d" if check_result["ok"] else "f"
    next_action = (
        "Command reference is current."
        if check_result["ok"]
        else "Regenerate command reference or inspect command-reference-check failure."
    )
    payload = {
        "schema_version": 1,
        "kind": "transfer_command_reference_check_result",
        "action": "command-reference-check",
        "result_status": result_status,
        "final_signal": final_signal,
        "next_action": next_action,
        "result": check_result,
    }
    _echo_transfer_payload_json_or_summary(payload, json_output=json_output)
    if not check_result["ok"]:
        raise typer.Exit(code=1)


__all__ = [name for name in globals() if not name.startswith("__")]
