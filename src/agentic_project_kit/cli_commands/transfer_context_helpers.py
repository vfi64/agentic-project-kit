from __future__ import annotations

# ruff: noqa: F403,F405

from agentic_project_kit.cli_commands.transfer_shared import *


def _clean_post_merge_status_is_noop() -> bool:
    status = repo_status(short=True)
    if status.returncode != 0 or str(status.stdout).strip():
        return False
    post_merge = post_merge_check()
    return post_merge.returncode == 0 and "result=NOOP" in post_merge.stdout

def _evaluate_llm_context_freshness(
    root: Path,
    *,
    max_age_minutes: int,
    allow_clean_post_merge_carrier_staleness: bool = False,
) -> dict[str, object]:
    from datetime import datetime, timezone

    from agentic_project_kit.llm_execution_context import build_llm_execution_context

    paths = {
        "outbox": root / ".agentic/transfer/outbox/last_result.txt",
        "latest_handoff_report": root / "docs/reports/terminal/transfer_handoff_reports/latest-transfer-handoff-report.json",
    }
    required_context_keys = [
        "source_hashes",
        "context_quality",
        "running_chat_refresh_contract",
        "shell_placeholder_policy",
        "terminal_resilience",
        "patch_generation_policy",
        "command_reference",
    ]
    required_markers = [
        "agentic-kit transfer pr-create-complete --post-merge-complete",
        "verify-llm-context-refresh",
    ]
    forbidden_fragments = ["<PR_NUMMER>", "<PR_NUMBER>"]
    now = datetime.now(timezone.utc)
    blockers: list[str] = []
    checked: dict[str, dict[str, object]] = {}
    valid_contexts: list[str] = []

    try:
        current_context = build_llm_execution_context(root)
        current_source_hashes = current_context.get("source_hashes", {})
    except Exception as exc:  # noqa: BLE001
        current_source_hashes = {}
        blockers.append("current_context_generation_failed")
        checked["current_context"] = {"ok": False, "error": str(exc)}

    for name, path in paths.items():
        status: dict[str, object] = {"path": str(path), "exists": path.exists()}
        checked[name] = status
        local_blockers: list[str] = []
        if not path.exists():
            local_blockers.append("missing")
            status["blockers"] = local_blockers
            blockers.append(name + "_missing")
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            status["json_error"] = str(exc)
            local_blockers.append("json_invalid")
            status["blockers"] = local_blockers
            blockers.append(name + "_json_invalid")
            continue
        if not isinstance(data, dict):
            local_blockers.append("not_object")
            status["blockers"] = local_blockers
            blockers.append(name + "_not_object")
            continue
        ctx = data.get("llm_execution_context")
        status["llm_execution_context_present"] = isinstance(ctx, dict)
        if not isinstance(ctx, dict):
            local_blockers.append("llm_execution_context_missing")
            status["blockers"] = local_blockers
            blockers.append(name + "_llm_execution_context_missing")
            continue
        ctx_text = json.dumps(ctx, sort_keys=True, ensure_ascii=False)
        missing_keys = [key for key in required_context_keys if key not in ctx]
        missing_markers = [marker for marker in required_markers if marker not in ctx_text]
        forbidden_hits = [fragment for fragment in forbidden_fragments if fragment in ctx_text]
        context_quality = ctx.get("context_quality") if isinstance(ctx.get("context_quality"), dict) else {}
        refresh_contract = ctx.get("running_chat_refresh_contract") if isinstance(ctx.get("running_chat_refresh_contract"), dict) else {}
        source_hashes = ctx.get("source_hashes") if isinstance(ctx.get("source_hashes"), dict) else {}
        status["missing_context_keys"] = missing_keys
        status["missing_markers"] = missing_markers
        status["forbidden_fragments"] = forbidden_hits
        status["source_hashes_complete"] = bool(context_quality.get("source_hashes_complete"))
        status["refresh_required_for_running_chats"] = bool(refresh_contract.get("refresh_required_for_running_chats"))
        status["source_hashes_match_current_repo"] = bool(source_hashes) and source_hashes == current_source_hashes
        generated_at = ctx.get("generated_at_utc")
        status["generated_at_utc"] = generated_at
        if isinstance(generated_at, str) and generated_at:
            try:
                generated_time = datetime.fromisoformat(generated_at.replace("Z", "+00:00"))
                age_seconds = (now - generated_time).total_seconds()
                status["age_seconds"] = age_seconds
                status["fresh"] = age_seconds <= max_age_minutes * 60
            except ValueError:
                status["fresh"] = False
                local_blockers.append("generated_at_invalid")
        else:
            status["fresh"] = False
            local_blockers.append("generated_at_missing")
        if missing_keys:
            local_blockers.append("context_keys_missing")
        if missing_markers:
            local_blockers.append("markers_missing")
        if forbidden_hits:
            local_blockers.append("forbidden_placeholder_present")
        if not status["source_hashes_complete"]:
            local_blockers.append("source_hashes_incomplete")
        if not status["source_hashes_match_current_repo"]:
            local_blockers.append("source_hashes_mismatch")
        if not status["refresh_required_for_running_chats"]:
            local_blockers.append("running_chat_refresh_contract_missing")
        if not status["fresh"]:
            local_blockers.append("stale_or_not_fresh")
        status["blockers"] = local_blockers
        if local_blockers:
            blockers.extend(name + "_" + item for item in local_blockers)
        else:
            valid_contexts.append(name)

    blockers = list(dict.fromkeys(blockers))
    # A single fresh, hash-consistent carrier is sufficient. Other stale or
    # missing carriers remain diagnostic findings, but must not block when at
    # least one authoritative local handoff context is valid.
    clean_post_merge_carrier_staleness_allowed = (
        allow_clean_post_merge_carrier_staleness
        and not valid_contexts
        and set(blockers).issubset(
            {
                "outbox_missing",
                "latest_handoff_report_source_hashes_mismatch",
                "latest_handoff_report_stale_or_not_fresh",
            }
        )
        and _clean_post_merge_status_is_noop()
    )
    result_status = (
        "PASS"
        if valid_contexts
        else "WARN"
        if clean_post_merge_carrier_staleness_allowed
        else "BLOCKED"
    )
    return {
        "schema_version": 1,
        "kind": "transfer_require_fresh_llm_context_result",
        "action": "require-fresh-llm-context",
        "result_status": result_status,
        "final_signal": "d" if result_status in {"PASS", "WARN"} else "f",
        "next_action": (
            "Fresh LLM context gate passed; planning may continue."
            if result_status == "PASS"
            else "Clean post-merge state detected; stale volatile LLM-context carriers are a warning, not a product blocker."
            if result_status == "WARN"
            else "Regenerate and publish fresh LLM context before planning: " + ", ".join(blockers)
        ),
        "max_age_minutes": max_age_minutes,
        "valid_contexts": valid_contexts,
        "blockers": blockers,
        "checked": checked,
        "allow_clean_post_merge_carrier_staleness": allow_clean_post_merge_carrier_staleness,
        "clean_post_merge_carrier_staleness_allowed": clean_post_merge_carrier_staleness_allowed,
    }

def _emit_llm_context_gate_result(payload: dict[str, object], *, json_output: bool) -> None:
    if json_output:
        typer.echo(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False))
        return
    _echo_transfer_payload_summary(
        title="TRANSFER_REQUIRE_FRESH_LLM_CONTEXT",
        result_status=str(payload.get("result_status", "BLOCKED")),
        final_signal=str(payload.get("final_signal", "f")),
        next_action=str(payload.get("next_action", "Regenerate fresh LLM context before planning.")),
        fields={
            "VALID_CONTEXTS": len(payload.get("valid_contexts", [])),
            "BLOCKERS": len(payload.get("blockers", [])),
            "MAX_AGE_MINUTES": payload.get("max_age_minutes", 0),
        },
    )

def _require_fresh_llm_context_or_exit(*, max_age_minutes: int, json_output: bool) -> None:
    evaluate = _public_transfer_attr("_evaluate_llm_context_freshness", _evaluate_llm_context_freshness)
    payload = evaluate(Path("."), max_age_minutes=max_age_minutes)
    if payload.get("result_status") == "PASS":
        return
    _emit_llm_context_gate_result(payload, json_output=json_output)
    raise typer.Exit(code=2)

def _branch_publishes_communication_rule_carrier() -> bool:
    completed = subprocess.run(
        ["git", "diff", "--name-only", "origin/main...HEAD"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        return False
    return "docs/reports/communication_rules/CURRENT_COMMUNICATION_RULES.md" in set(
        completed.stdout.splitlines()
    )

def _require_current_communication_context_or_exit(
    *,
    json_output: bool,
    allow_rule_carrier_publish: bool = False,
) -> None:
    result = require_current_communication_context(Path("."))
    if result.result_status == "PASS":
        return
    if allow_rule_carrier_publish and _branch_publishes_communication_rule_carrier():
        return
    payload = result.as_json_data()
    if json_output:
        typer.echo(json.dumps(payload, indent=2, sort_keys=True))
    else:
        typer.echo("COMMUNICATION_CONTEXT_GATE")
        typer.echo(f"result_status={result.result_status}")
        typer.echo(f"reason={result.reason}")
        typer.echo(f"required_next_reply={result.required_next_reply or '<none>'}")
        typer.echo(f"remote_path={result.remote_path}")
        typer.echo(f"next_action={result.next_action}")
    raise typer.Exit(code=2)

def _ensure_fresh_llm_context_or_exit(*, max_age_minutes: int, json_output: bool) -> None:
    evaluate = _public_transfer_attr("_evaluate_llm_context_freshness", _evaluate_llm_context_freshness)
    payload = evaluate(Path("."), max_age_minutes=max_age_minutes)
    if payload.get("result_status") == "PASS":
        return

    initial_blockers = list(payload.get("blockers", []))
    try:
        refresh = _public_transfer_attr("refresh_llm_context_carriers", refresh_llm_context_carriers)
        refresh_result = refresh(Path("."))
    except (FileNotFoundError, ValueError, OSError) as exc:
        payload["auto_refresh_attempted"] = True
        payload["auto_refresh_result_status"] = "BLOCKED"
        payload["auto_refresh_error"] = str(exc)
        payload["next_action"] = "Inspect LLM context carrier refresh failure before planning: " + str(exc)
        _emit_llm_context_gate_result(payload, json_output=json_output)
        raise typer.Exit(code=2) from exc

    evaluate = _public_transfer_attr("_evaluate_llm_context_freshness", _evaluate_llm_context_freshness)
    payload = evaluate(Path("."), max_age_minutes=max_age_minutes)
    payload["auto_refresh_attempted"] = True
    payload["auto_refresh_result_status"] = refresh_result.get("result_status")
    payload["initial_blockers"] = initial_blockers
    if payload.get("result_status") == "PASS":
        return

    _emit_llm_context_gate_result(payload, json_output=json_output)
    raise typer.Exit(code=2)

KNOWN_VOLATILE_TRANSFER_PATHS = [
    ".agentic/transfer/inbox/next_command.py.txt",
    ".agentic/transfer/outbox/last_result.txt",
    "docs/reports/terminal/transfer_handoff_reports/latest-transfer-handoff-report.json",
    "docs/reports/terminal/transfer_handoff_reports/latest-transfer-handoff-report.log",
]


def _completed_process_payload(completed: subprocess.CompletedProcess[str]) -> dict[str, object]:
    return {
        "argv": list(completed.args),
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "ok": completed.returncode == 0,
    }

def _restore_known_volatile_paths(root: Path | str = ".") -> dict[str, object]:
    root_path = Path(root)
    tracked_paths: list[str] = []
    removed_untracked: list[str] = []
    skipped_missing: list[str] = []
    checks: list[dict[str, object]] = []
    errors: list[str] = []

    for relative_path in KNOWN_VOLATILE_TRANSFER_PATHS:
        check = subprocess.run(
            ["git", "ls-files", "--error-unmatch", relative_path],
            cwd=root_path,
            text=True,
            capture_output=True,
            check=False,
        )
        checks.append(_completed_process_payload(check))
        target = root_path / relative_path
        if check.returncode == 0:
            tracked_paths.append(relative_path)
            continue
        if target.exists():
            try:
                if target.is_dir():
                    shutil.rmtree(target)
                else:
                    target.unlink()
                removed_untracked.append(relative_path)
            except OSError as exc:
                errors.append(f"remove_untracked_failed:{relative_path}:{exc}")
        else:
            skipped_missing.append(relative_path)

    restore_result: dict[str, object] | None = None
    if tracked_paths:
        restore = subprocess.run(
            ["git", "restore", "--", *tracked_paths],
            cwd=root_path,
            text=True,
            capture_output=True,
            check=False,
        )
        restore_result = _completed_process_payload(restore)
        if restore.returncode != 0:
            errors.append("git_restore_failed")

    return {
        "ok": not errors,
        "tracked_paths": tracked_paths,
        "removed_untracked": removed_untracked,
        "skipped_missing": skipped_missing,
        "checks": checks,
        "restore": restore_result,
        "errors": errors,
    }

def _run_transfer_subprocess(argv: list[str], *, cwd: Path | None = None) -> dict[str, object]:
    completed = subprocess.run(argv, cwd=cwd or Path("."), text=True, capture_output=True, check=False)
    return _completed_process_payload(completed)

def _echo_transfer_payload_terminal_summary(payload: dict[str, object], *, title: str | None = None) -> None:
    action = str(payload.get("action") or "transfer")
    summary_title = title or f"TRANSFER_{action.upper().replace('-', '_')}"
    result_status = str(payload.get("result_status") or "UNKNOWN")
    final_signal = str(payload.get("final_signal") or ("d" if result_status == "PASS" else "f"))
    next_action = str(payload.get("next_action") or "Inspect command result before continuing.")

    fields: dict[str, object] = {}
    for key, label in (
        ("kind", "KIND"),
        ("changed_files", "CHANGED_FILES"),
        ("blockers", "BLOCKERS"),
        ("missing_sources", "MISSING_SOURCES"),
        ("outbox_written", "OUTBOX_WRITTEN"),
    ):
        if key not in payload:
            continue
        value = payload.get(key)
        if isinstance(value, list):
            value = len(value)
        fields[label] = value

    _echo_transfer_payload_summary(
        title=summary_title,
        result_status=result_status,
        final_signal=final_signal,
        fields=fields,
        next_action=next_action,
    )

def _echo_transfer_payload_json_or_summary(
    payload: dict[str, object],
    *,
    json_output: bool,
    title: str | None = None,
) -> None:
    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        _echo_transfer_payload_terminal_summary(payload, title=title)


__all__ = [name for name in globals() if not name.startswith("__")]
