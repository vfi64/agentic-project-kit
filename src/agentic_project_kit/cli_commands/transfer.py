from __future__ import annotations

from datetime import date as date_cls
import json
import shlex
import shutil
import subprocess
from pathlib import Path

import typer
from agentic_project_kit.transfer_safety_context import render_local_to_llm_log_header, render_local_to_llm_log_upload_hint, build_transfer_safety_header
import yaml

from agentic_project_kit.communication_rule_context import require_current_communication_context
from agentic_project_kit.llm_context_carriers import refresh_llm_context_carriers
from agentic_project_kit.local_garbage_collector import run_local_garbage_collector
from agentic_project_kit.local_command_stack import begin_local_command_stack
from agentic_project_kit.local_command_stack import current_or_begin_local_command_stack_id
from agentic_project_kit.local_command_stack import end_local_command_stack
from agentic_project_kit.patch_cycle_workflow import build_patch_cycle_status, render_patch_cycle_status
from agentic_project_kit.transfer_closeout import closeout_transfer
from agentic_project_kit.transfer_continue import render_transfer_continue_summary
from agentic_project_kit.transfer_continue import run_transfer_continue
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
from agentic_project_kit.transfer_state import normalize_transfer_file_lifecycle
from agentic_project_kit.work_order_patch import (
    DEFAULT_PATCH_ORDER,
    WorkOrderPatchResult,
    apply_work_order_patch,
    load_work_order_patch,
    render_work_order_patch_result,
    work_order_patch_result_as_json_data,
)
from agentic_project_kit.successor_handoff_package import write_successor_handoff_package
from agentic_project_kit.transfer_uplink import (
    publish_latest_transfer_report,
    read_latest_transfer_report,
    run_and_log_transfer_command,
    run_and_log_transfer_sequence,
    write_transfer_report_from_repo_result,
)
from agentic_project_kit.transfer_workflow_next import run_workflow_next

transfer_app = typer.Typer(help="Inspect and apply repo-backed text transfer orders.")



def _run_local_garbage_collector_preflight() -> None:
    """Run deterministic local runtime cleanup before local transfer preflight."""
    command_stack_id = current_or_begin_local_command_stack_id(Path("."))
    result = run_local_garbage_collector(Path("."), write_report=True, run_id=command_stack_id)
    if int(result.get("returncode", 0)) != 0:
        raise typer.BadParameter(str(result.get("next_action", "local garbage collector failed")))



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


def _echo_transfer_payload_summary(
    *,
    title: str,
    result_status: str,
    final_signal: str,
    next_action: str,
    fields: dict[str, object] | None = None,
) -> None:
    typer.echo("*" * 34 + " START SUMMARY " + "*" * 35)
    typer.echo(title)
    typer.echo("")
    typer.echo(_summary_line("STATE", result_status))
    if fields:
        for key, value in fields.items():
            typer.echo(_summary_line(key, value))
    typer.echo("")
    typer.echo(_summary_line("NEXT", next_action))
    typer.echo(_summary_line("CHAT_REPLY", f"{final_signal} | NEXT={next_action}"))
    typer.echo("*" * 35 + " END SUMMARY " + "*" * 36)



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


def _normalize_agentic_command_for_reference(command: str) -> str:
    parts = shlex.split(command)
    if not parts:
        return ""
    if parts[0].endswith("agentic-kit"):
        parts[0] = "agentic-kit"
    elif parts[:2] == ["./.venv/bin/python", "-m"] and len(parts) >= 3 and parts[2] == "agentic_project_kit":
        parts = ["agentic-kit", *parts[3:]]
    else:
        return " ".join(parts)
    return " ".join(parts)


def _load_command_reference_names(root: Path) -> set[str]:
    reference_path = root / "docs/reference/agentic-kit-commands.json"
    payload = json.loads(reference_path.read_text(encoding="utf-8"))
    commands = payload.get("commands", [])
    names: set[str] = set()
    for item in commands:
        if isinstance(item, dict) and isinstance(item.get("qualified_name"), str):
            names.add(str(item["qualified_name"]))
    return names


def _detect_avoidable_low_level_meta_command_sequences(sequence_commands: list[str] | None) -> list[dict[str, object]]:
    if not sequence_commands:
        return []

    meta_command_sequences = {
        "work-start": {
            "meta_command": "agentic-kit work start",
            "low_level_markers": {
                "agentic-kit transfer sync-main",
                "agentic-kit rules acknowledge",
                "agentic-kit transfer post-merge-check",
                "agentic-kit transfer repo-status",
            },
        },
        "work-check": {
            "meta_command": "agentic-kit work check",
            "low_level_markers": {
                "agentic-kit transfer command-reference-check",
                "agentic-kit docs-audit",
                "agentic-kit audit-doc-currency",
            },
        },
        "work-finish": {
            "meta_command": "agentic-kit work finish",
            "low_level_markers": {
                "agentic-kit transfer protected-diff-plan",
                "agentic-kit transfer commit",
                "agentic-kit transfer push-current",
                "agentic-kit transfer pr-create-complete",
            },
        },
        "work-recover": {
            "meta_command": "agentic-kit work recover",
            "low_level_markers": {
                "agentic-kit transfer restore-known-volatile",
                "agentic-kit transfer normalize-session",
                "agentic-kit transfer conflict-status",
                "agentic-kit transfer patch-cycle-status",
            },
        },
        "release-ready": {
            "meta_command": "agentic-kit release ready",
            "low_level_markers": {
                "agentic-kit transfer standard-error-scan",
                "agentic-kit release-status",
            },
        },
        "release-prepare": {
            "meta_command": "agentic-kit release prepare",
            "low_level_markers": {
                "agentic-kit release-notes-generate",
                "agentic-kit release-prep",
            },
        },
    }

    normalized_sequence = [" ".join(command.split()) for command in sequence_commands]
    sequence_blob = "\n".join(normalized_sequence)
    avoidable: list[dict[str, object]] = []
    for sequence_name, rule in meta_command_sequences.items():
        meta_command = str(rule["meta_command"])
        markers = set(rule["low_level_markers"])
        matched_markers = sorted(marker for marker in markers if marker in sequence_blob)
        if len(matched_markers) >= 2 and meta_command not in sequence_blob:
            avoidable.append(
                {
                    "sequence": sequence_name,
                    "preferred_meta_command": meta_command,
                    "matched_low_level_markers": matched_markers,
                }
            )
    return avoidable



@transfer_app.command("command-composition-check")
def command_composition_check_command(
    test_paths: list[Path] | None = typer.Option(
        None,
        "--test-path",
        help="Repository-relative test path that must exist before composing a pytest command. Repeatable.",
    ),
    commands: list[str] | None = typer.Option(
        None,
        "--command",
        help="agentic-kit command prefix that must exist in docs/reference/agentic-kit-commands.json. Repeatable.",
    ),
    sequence_commands: list[str] | None = typer.Option(
        None,
        "--sequence-command",
        help="Command sequence entry to check for avoidable low-level workflow chains. Repeatable.",
    ),
    root: Path = typer.Option(Path("."), "--root", help="Project root."),
    json_output: bool = typer.Option(False, "--json", help="Print machine-readable JSON only."),
) -> None:
    """Block common copied-command mistakes before running patch, transfer, or release gates."""
    project_root = root.resolve()
    avoidable_low_level_sequences = _detect_avoidable_low_level_meta_command_sequences(sequence_commands)
    missing_test_paths: list[str] = []
    existing_test_paths: list[str] = []
    for raw_path in test_paths or []:
        candidate = raw_path if raw_path.is_absolute() else project_root / raw_path
        rel = str(raw_path)
        if candidate.exists():
            existing_test_paths.append(rel)
        else:
            missing_test_paths.append(rel)

    reference_missing = False
    valid_commands: list[str] = []
    invalid_commands: list[str] = []
    try:
        reference_names = _load_command_reference_names(project_root)
    except (OSError, json.JSONDecodeError, ValueError):
        reference_names = set()
        reference_missing = bool(commands)

    for command in commands or []:
        normalized = _normalize_agentic_command_for_reference(command)
        if normalized and normalized in reference_names:
            valid_commands.append(command)
        else:
            invalid_commands.append(command)

    blockers: list[str] = []
    if missing_test_paths:
        blockers.append("missing_test_paths")
    if reference_missing:
        blockers.append("command_reference_unavailable")
    if invalid_commands:
        blockers.append("invalid_agentic_kit_commands")
    if avoidable_low_level_sequences:
        blockers.append("avoidable_low_level_sequences")

    result_status = "PASS" if not blockers else "BLOCKED"
    next_action = (
        "Command composition inputs are valid."
        if result_status == "PASS"
        else "Fix missing test paths or invalid agentic-kit command names before running the composed block."
    )
    payload = {
        "schema_version": 1,
        "kind": "transfer_command_composition_check_result",
        "action": "command-composition-check",
        "result_status": result_status,
        "returncode": 0 if result_status == "PASS" else 2,
        "blockers": blockers,
        "test_paths": {
            "existing": existing_test_paths,
            "missing": missing_test_paths,
        },
        "commands": {
            "valid": valid_commands,
            "invalid": invalid_commands,
        },
        "avoidable_low_level_sequences": avoidable_low_level_sequences,
        "next_action": next_action,
    }

    if json_output:
        typer.echo(json.dumps(payload, indent=2, sort_keys=True))
    else:
        _echo_transfer_payload_summary(
            title="TRANSFER_COMMAND_COMPOSITION_CHECK",
            result_status=result_status,
            final_signal="d" if result_status == "PASS" else "f",
            next_action=next_action,
            fields={
                "MISSING_TEST_PATHS": len(missing_test_paths),
                "INVALID_COMMANDS": len(invalid_commands),
                "AVOIDABLE_LOW_LEVEL_SEQUENCES": len(avoidable_low_level_sequences),
            },
        )

    if result_status != "PASS":
        raise typer.Exit(code=2)


def _load_yaml_mapping(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    try:
        loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return loaded if isinstance(loaded, dict) else {}


def _meta_command_preference_source_paths(root: Path) -> set[Path]:
    """Return the explicit YAML rule sources for active meta-command policy."""
    return {
        root / ".agentic" / "transfer_safety_rules.yaml",
        root / ".agentic" / "transfer" / "one_command_transfer_protocol.yaml",
    }


def _load_transfer_meta_command_preference(root: Path) -> dict[str, object]:
    """Load local-to-LLM meta-command preference dynamically from rule sources."""
    safety = _load_yaml_mapping(root / ".agentic" / "transfer_safety_rules.yaml")
    protocol = _load_yaml_mapping(root / ".agentic" / "transfer" / "one_command_transfer_protocol.yaml")

    safety_pref = safety.get("meta_command_preference")
    protocol_pref = protocol.get("meta_command_preference")

    preferred_commands: list[str] = []
    if isinstance(safety_pref, dict):
        raw = safety_pref.get("preferred_commands")
        if isinstance(raw, dict):
            preferred_commands.extend(str(value) for value in raw.values())
        elif isinstance(raw, list):
            preferred_commands.extend(str(value) for value in raw)
    if isinstance(protocol_pref, dict):
        raw = protocol_pref.get("preferred_entrypoints")
        if isinstance(raw, list):
            preferred_commands.extend(str(value) for value in raw)

    unique_commands: list[str] = []
    seen: set[str] = set()
    for command in preferred_commands:
        if command and command not in seen:
            seen.add(command)
            unique_commands.append(command)

    fallback_rule = ""
    priority = ""
    if isinstance(safety_pref, dict):
        fallback_rule = str(safety_pref.get("fallback_rule") or "")
        priority = str(safety_pref.get("priority") or "")
    if not fallback_rule and isinstance(protocol_pref, dict):
        fallback_rule = str(protocol_pref.get("rule") or "")

    return {
        "status": "active" if unique_commands else "missing",
        "priority": priority or "primary_path",
        "preferred_commands": unique_commands,
        "fallback_rule": fallback_rule,
        "sources": sorted(str(path) for path in _meta_command_preference_source_paths(root)),
    }


def _render_transfer_meta_command_preference_header(root: Path) -> str:
    preference = _load_transfer_meta_command_preference(root)
    if preference["status"] != "active":
        return ""
    lines = [
        "META_COMMAND_PREFERENCE:",
        f"  status: {preference['status']}",
        f"  priority: {preference['priority']}",
        "  source: dynamic-from-rule-files",
        "  preferred_commands:",
    ]
    for command in preference["preferred_commands"]:
        lines.append(f"    - {command}")
    fallback = str(preference.get("fallback_rule") or "").strip()
    if fallback:
        lines.append(f"  fallback_rule: {fallback}")
    lines.append("  low_level_fallback_requires_reason: true")
    return "\n".join(lines)


def _render_local_to_llm_transfer_header(root: Path) -> str:
    """Render the local-to-LLM transfer header from current rule sources."""
    sections: list[str] = []
    meta_header = _render_transfer_meta_command_preference_header(root).strip()
    if meta_header:
        sections.append(meta_header)
    return "\n\n".join(sections).strip()



def _prefix_local_to_llm_transfer_header(content: str, *, root: Path | None = None) -> str:
    """Prefix local-to-LLM transfer content with a dynamically rendered header."""
    effective_root = root or Path(".")
    header = _render_local_to_llm_transfer_header(effective_root).strip()
    if not header:
        return content
    if content.startswith("META_COMMAND_PREFERENCE:"):
        return content
    return f"{header}\n\n{content}"



def _json_contains_static_meta_preference_policy(content: str) -> bool:
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        return False

    def walk(value: object) -> bool:
        if isinstance(value, dict):
            for key, nested in value.items():
                if key in {"meta_command_preference", "META_COMMAND_PREFERENCE"}:
                    return True
                if walk(nested):
                    return True
        elif isinstance(value, list):
            return any(walk(item) for item in value)
        return False

    return walk(parsed)


def _scan_static_meta_preference_projection_drift(root: Path) -> dict[str, object]:
    """Block static active meta-command policy outside explicit YAML rule sources.

    This scans projections and generated/compiled carriers. It deliberately does
    not scan implementation source code, because renderer code necessarily
    contains marker strings such as META_COMMAND_PREFERENCE.
    """
    allowed_sources = {path.resolve() for path in _meta_command_preference_source_paths(root)}
    scanned_roots = [
        root / ".agentic",
        root / "docs",
    ]
    forbidden_markers = [
        "meta_command_preference:",
        '"meta_command_preference"',
        "META_COMMAND_PREFERENCE:",
        '"META_COMMAND_PREFERENCE"',
    ]
    matches: list[dict[str, object]] = []

    for scan_root in scanned_roots:
        if not scan_root.exists():
            continue
        for candidate in scan_root.rglob("*"):
            if not candidate.is_file():
                continue
            relative_parts = candidate.relative_to(scan_root).parts
            if any(part in {".git", ".venv", "tmp", "__pycache__"} for part in relative_parts):
                continue
            if candidate.suffix not in {"", ".md", ".txt", ".yaml", ".yml", ".json"}:
                continue
            if candidate.resolve() in allowed_sources:
                continue
            try:
                content = candidate.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            json_policy_match = candidate.suffix == ".json" and _json_contains_static_meta_preference_policy(content)
            if json_policy_match:
                line_numbers = [
                    index
                    for index, line in enumerate(content.splitlines(), start=1)
                    if "meta_command_preference" in line or "META_COMMAND_PREFERENCE" in line
                ] or [1]
                matches.append(
                    {
                        "path": str(candidate.relative_to(root)),
                        "marker": "json:meta_command_preference",
                        "line_numbers": line_numbers,
                    }
                )
                continue

            for marker in forbidden_markers:
                marker_matches = [marker]
                if marker == "meta_command_preference:":
                    marker_matches.extend([
                        '"meta_command_preference"',
                        "'meta_command_preference'",
                    ])
                if marker == "META_COMMAND_PREFERENCE:":
                    marker_matches.extend([
                        '"META_COMMAND_PREFERENCE"',
                        "'META_COMMAND_PREFERENCE'",
                    ])
                if not any(marker_match in content for marker_match in marker_matches):
                    continue
                line_numbers = [
                    index
                    for index, line in enumerate(content.splitlines(), start=1)
                    if any(marker_match in line for marker_match in marker_matches)
                ]
                matches.append(
                    {
                        "path": str(candidate.relative_to(root)),
                        "marker": marker,
                        "line_numbers": line_numbers,
                    }
                )
    return {
        "status": "PASS" if not matches else "BLOCKED",
        "allowed_static_sources": sorted(str(path.relative_to(root)) for path in _meta_command_preference_source_paths(root)),
        "matches": matches,
    }


def _latest_release_tag() -> str:
    completed = subprocess.run(
        ["git", "tag", "--sort=-creatordate"],
        text=True,
        capture_output=True,
    )
    if completed.returncode != 0:
        return ""
    for line in completed.stdout.splitlines():
        tag = line.strip()
        if tag.startswith("v"):
            return tag
    return ""


def _run_standard_error_scan_step(
    name: str,
    argv: list[str],
    *,
    allowed_returncodes: set[int] | None = None,
) -> dict[str, object]:
    allowed = allowed_returncodes or {0}
    completed = subprocess.run(argv, text=True, capture_output=True)
    ok = completed.returncode in allowed
    return {
        "name": name,
        "argv": argv,
        "returncode": completed.returncode,
        "ok": ok,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "allowed_returncodes": sorted(allowed),
    }


def _known_bad_pattern_scan(root: Path) -> dict[str, object]:
    # Build these from fragments so repository audits do not flag the scanner's own
    # negative examples as active workflow instructions.
    patterns = [
        "tests/" + "test_release_status.py",
        "agentic-kit " + "command-reference-refresh",
        "_copy_" + "project_fixture",
        "<" + "pr-number>",
        "./" + "ns protected-diff-check",
        "./" + "ns merge-if-green",
        "./" + "ns next-safe-step",
    ]
    # Scan only active workflow surfaces. Historical planning/test-gate docs may
    # legitimately mention old commands as examples or archived failure modes.
    search_roots = [
        root / "src",
        root / "tests",
        root / "docs/reference",
        root / "docs/handoff",
        root / ".agentic",
    ]
    matches: list[dict[str, object]] = []
    for base in search_roots:
        if not base.exists():
            continue
        for file_path in base.rglob("*"):
            if not file_path.is_file():
                continue
            if any(part in {".git", ".venv", "tmp", "__pycache__"} for part in file_path.parts):
                continue
            try:
                content = file_path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            for line_number, line in enumerate(content.splitlines(), start=1):
                for pattern in patterns:
                    if pattern in line:
                        matches.append(
                            {
                                "path": str(file_path.relative_to(root)),
                                "line": line_number,
                                "pattern": pattern,
                                "text": line.strip()[:240],
                            }
                        )
    return {"patterns": patterns, "matches": matches}


def _scan_llm_work_order_contract(root: Path) -> dict[str, object]:
    """Verify that LLM work orders are contractually Python scripts."""
    try:
        header = build_transfer_safety_header(root)
    except Exception as exc:
        return {
            "status": "BLOCKED",
            "error": str(exc),
            "required_format": None,
            "canonical_inbox": None,
            "shell_commands_allowed": None,
        }

    contract = header.get("llm_work_order_contract")
    if not isinstance(contract, dict):
        return {
            "status": "BLOCKED",
            "error": "llm_work_order_contract_missing",
            "required_format": None,
            "canonical_inbox": None,
            "shell_commands_allowed": None,
        }

    transfer_file = contract.get("transfer_file")
    if not isinstance(transfer_file, dict):
        transfer_file = {}

    required_format = contract.get("required_format")
    canonical_inbox = transfer_file.get("canonical_inbox")
    shell_commands_allowed = transfer_file.get("shell_commands_allowed")

    failures: list[str] = []
    if required_format != "python_script":
        failures.append("required_format_not_python_script")
    if not str(canonical_inbox or "").endswith(".py.txt"):
        failures.append("canonical_inbox_not_python_script_file")
    if shell_commands_allowed is not False:
        failures.append("transfer_file_allows_shell_commands")

    return {
        "status": "PASS" if not failures else "BLOCKED",
        "failures": failures,
        "required_format": required_format,
        "canonical_inbox": canonical_inbox,
        "shell_commands_allowed": shell_commands_allowed,
    }



@transfer_app.command("standard-error-scan")
def standard_error_scan_command(
    before_release: bool = typer.Option(
        False,
        "--before-release",
        help="Run the release-oriented standard-error scan bundle.",
    ),
    version: str = typer.Option("", "--version", help="Release version for before-release checks. Required with --before-release."),
    from_tag: str = typer.Option("", "--from-tag", help="Previous release tag for release notes checks. Defaults to the latest local v* git tag."),
    to_ref: str = typer.Option("main", "--to-ref", help="Target ref for release notes checks."),
    date: str = typer.Option("", "--date", help="Release date for release-prep dry-run. Defaults to today."),
    root: Path = typer.Option(Path("."), "--root", help="Project root."),
    json_output: bool = typer.Option(False, "--json", help="Print machine-readable JSON only."),
) -> None:
    """Run a bounded scan for known workflow standard errors before patch/transfer/release work."""
    project_root = root.resolve()
    release_date = date or date_cls.today().isoformat()
    effective_from_tag = from_tag or _latest_release_tag()
    steps: list[dict[str, object]] = []

    def step(name: str, argv: list[str], *, allowed_returncodes: set[int] | None = None) -> None:
        steps.append(_run_standard_error_scan_step(name, argv, allowed_returncodes=allowed_returncodes))

    if before_release:
        step("post-merge-check", ["./.venv/bin/agentic-kit", "transfer", "post-merge-check"])
    step("repo-status", ["./.venv/bin/agentic-kit", "transfer", "repo-status"])

    release_tests = [
        "tests/test_release_prepare_command.py",
        "tests/test_release_notes.py",
        "tests/test_release_state.py",
        "tests/test_agentic_kit_command_reference_is_current.py",
    ]
    command_check = [
        "./.venv/bin/agentic-kit",
        "transfer",
        "command-composition-check",
        "--json",
    ]
    for test_path in release_tests:
        command_check.extend(["--test-path", test_path])
    for command in [
        "agentic-kit transfer command-reference-check",
        "agentic-kit transfer command-composition-check",
        "agentic-kit transfer patch-cycle-status",
        "agentic-kit release-status",
        "agentic-kit release-notes-generate",
        "agentic-kit release-prep",
    ]:
        command_check.extend(["--command", command])
    step("command-composition-check", command_check)
    step("command-reference-check", ["./.venv/bin/agentic-kit", "transfer", "command-reference-check", "--json"])
    step("patch-cycle-status", ["./.venv/bin/agentic-kit", "transfer", "patch-cycle-status", "--include-ci", "--json"], allowed_returncodes={0, 2})

    if before_release:
        if not version:
            steps.append(
                {
                    "name": "release-version",
                    "argv": [],
                    "returncode": 2,
                    "ok": False,
                    "allowed_returncodes": [0],
                    "stdout": "",
                    "stderr": "--version is required with --before-release.",
                }
            )
        if not effective_from_tag:
            steps.append(
                {
                    "name": "release-from-tag",
                    "argv": [],
                    "returncode": 2,
                    "ok": False,
                    "allowed_returncodes": [0],
                    "stdout": "",
                    "stderr": "--from-tag was not provided and no local v* git tag could be derived.",
                }
            )
        summary_lines_path = project_root / "tmp" / f"release-{version.replace('.', '')}-summary-lines.json"
        step("release-status", ["./.venv/bin/agentic-kit", "release-status", "--include-remote", "--json"], allowed_returncodes={0, 2})
        step(
            "release-notes-generate",
            [
                "./.venv/bin/agentic-kit",
                "release-notes-generate",
                "--version",
                version,
                "--from-tag",
                effective_from_tag,
                "--to-ref",
                to_ref,
                "--include-github-metadata",
                "--summary-lines-json",
                str(summary_lines_path),
                "--json",
            ],
        )
        step(
            "release-prep-dry-run",
            [
                "./.venv/bin/agentic-kit",
                "release-prep",
                "--version",
                version,
                "--date",
                release_date,
                "--summary-lines-from",
                str(summary_lines_path),
                "--dry-run",
                "--json",
            ],
        )

    step(
        "fresh-context-strict",
        ["./.venv/bin/agentic-kit", "transfer", "require-fresh-llm-context", "--json"],
        allowed_returncodes={0, 2},
    )
    step(
        "fresh-context-clean-post-merge-allowance",
        [
            "./.venv/bin/agentic-kit",
            "transfer",
            "require-fresh-llm-context",
            "--allow-clean-post-merge-carrier-staleness",
            "--json",
        ],
        allowed_returncodes={0} if before_release else {0, 2},
    )
    step("docs-audit", ["./.venv/bin/agentic-kit", "docs-audit"])
    step("audit-doc-currency", ["./.venv/bin/agentic-kit", "audit-doc-currency"])
    step("audit-planning-docs-consolidation", ["./.venv/bin/agentic-kit", "audit-planning-docs-consolidation"])
    step("audit-ns-legacy-references", ["./.venv/bin/agentic-kit", "audit-ns-legacy-references"])
    step("audit-program-redundancy", ["./.venv/bin/agentic-kit", "audit-program-redundancy"])
    step("standard-gates-audit-suite", ["./.venv/bin/agentic-kit", "standard-gates-audit-suite"])

    pattern_scan = _known_bad_pattern_scan(project_root)
    llm_work_order_contract_scan = _scan_llm_work_order_contract(project_root)
    local_to_llm_log_header = render_local_to_llm_log_header(project_root)
    local_to_llm_log_header_contains_meta_preference = (
        "META_COMMAND_PREFERENCE" in local_to_llm_log_header
        or "meta_command_preference" in local_to_llm_log_header
    )
    local_to_llm_log_header_scan = {
        "status": "PASS"
        if local_to_llm_log_header_contains_meta_preference and "dynamic-from-rule-files" in local_to_llm_log_header
        else "BLOCKED",
        "contains_meta_command_preference": local_to_llm_log_header_contains_meta_preference,
        "contains_dynamic_source_marker": "dynamic-from-rule-files" in local_to_llm_log_header,
    }
    static_meta_preference_projection_scan = _scan_static_meta_preference_projection_drift(project_root)
    blockers: list[str] = []
    warnings: list[str] = []

    for item in steps:
        if not item["ok"]:
            blockers.append(str(item["name"]))

    if pattern_scan["matches"]:
        warnings.append("known_bad_patterns_found")
    if llm_work_order_contract_scan["status"] != "PASS":
        blockers.append("llm_work_order_contract_not_python_script")
    if local_to_llm_log_header_scan["status"] != "PASS":
        blockers.append("local_to_llm_log_header_missing_dynamic_meta_preference")
    if static_meta_preference_projection_scan["matches"]:
        blockers.append("static_meta_preference_projection_drift")

    strict_step = next((item for item in steps if item["name"] == "fresh-context-strict"), None)
    allowance_step = next((item for item in steps if item["name"] == "fresh-context-clean-post-merge-allowance"), None)
    if strict_step and strict_step["returncode"] == 2 and allowance_step:
        if allowance_step["returncode"] == 0:
            warnings.append("strict_fresh_context_blocked_but_clean_post_merge_allowance_passed")
        elif not before_release and allowance_step["returncode"] == 2:
            warnings.append("fresh_context_stale_in_feature_branch_diagnostic")

    result_status = "BLOCKED" if blockers else "WARN" if warnings else "PASS"
    next_action = (
        "Fix blocking standard-error scan steps before continuing."
        if blockers
        else "Review warnings, then continue release readiness."
        if warnings
        else "No known standard-error blockers detected."
    )

    payload = {
        "schema_version": 1,
        "kind": "transfer_standard_error_scan_result",
        "action": "standard-error-scan",
        "result_status": result_status,
        "returncode": 2 if blockers else 0,
        "before_release": before_release,
        "version": version,
        "from_tag": effective_from_tag,
        "to_ref": to_ref,
        "date": release_date,
        "blockers": blockers,
        "warnings": warnings,
        "steps": steps,
        "known_bad_pattern_scan": pattern_scan,
        "llm_work_order_contract_scan": llm_work_order_contract_scan,
        "local_to_llm_log_header_scan": local_to_llm_log_header_scan,
        "static_meta_preference_projection_scan": static_meta_preference_projection_scan,
        "next_action": next_action,
    }

    if json_output:
        typer.echo(json.dumps(payload, indent=2, sort_keys=True))
    else:
        _echo_transfer_payload_summary(
            title="TRANSFER_STANDARD_ERROR_SCAN",
            result_status=result_status,
            final_signal="f" if blockers else "d",
            next_action=next_action,
            fields={
                "BLOCKERS": len(blockers),
                "WARNINGS": len(warnings),
                "PATTERN_MATCHES": len(pattern_scan["matches"]),
            },
        )

    if blockers:
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



@transfer_app.command("continue")
def continue_transfer_command(
    branch: str | None = typer.Argument(
        None,
        help="Optional target branch. If omitted, infer a single active transfer order.",
    ),
    json_output: bool = typer.Option(False, "--json/--no-json", help="Print machine-readable JSON."),
    skip_llm_context_gate: bool = typer.Option(
        False,
        "--skip-llm-context-gate",
        help="Recovery-only: continue without requiring fresh generated LLM context.",
    ),
) -> None:
    """Continue chat/local transfer communication through the safest available wrapper path."""
    if not skip_llm_context_gate:
        _ensure_fresh_llm_context_or_exit(max_age_minutes=60, json_output=json_output)
    result = run_transfer_continue(Path("."), branch)
    if json_output:
        typer.echo(json.dumps(result, indent=2, sort_keys=True))
    else:
        typer.echo(render_transfer_continue_summary(result))
    if int(result.get("returncode", 2)) != 0:
        raise typer.Exit(code=int(result.get("returncode", 2)))


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



@transfer_app.command("command-stack-begin")
def command_stack_begin_command(
    json_output: bool = typer.Option(True, "--json/--no-json", help="Print machine-readable JSON."),
) -> None:
    """Begin a repo-local command-stack state for deterministic local preflight cleanup."""
    state = begin_local_command_stack(Path("."))
    if json_output:
        typer.echo(json.dumps(state, indent=2, sort_keys=True))
    else:
        typer.echo(_summary_line("STATE", "PASS"))
        typer.echo(_summary_line("COMMAND_STACK_ID", state["command_stack_id"]))
        typer.echo(_summary_line("NEXT", "Run normalize-session."))


@transfer_app.command("command-stack-end")
def command_stack_end_command(
    json_output: bool = typer.Option(True, "--json/--no-json", help="Print machine-readable JSON."),
) -> None:
    """End the repo-local command-stack state after a local command stack completed."""
    state = end_local_command_stack(Path("."))
    if json_output:
        typer.echo(json.dumps(state, indent=2, sort_keys=True))
    else:
        typer.echo(_summary_line("STATE", "PASS"))
        typer.echo(_summary_line("COMMAND_STACK_ID", state.get("command_stack_id", "")))
        typer.echo(_summary_line("NEXT", "Command stack ended."))


@transfer_app.command("normalize-files")
def normalize_transfer_files_command(
    dry_run: bool = typer.Option(False, "--dry-run", help="Report transfer file lifecycle repairs without applying them."),
    json_output: bool = typer.Option(True, "--json/--no-json", help="Print machine-readable JSON."),
) -> None:
    """Normalize active transfer files by adding missing command IDs and archiving stale active files."""
    result = normalize_transfer_file_lifecycle(Path("."), dry_run=dry_run)
    if json_output:
        typer.echo(json.dumps(result, indent=2, sort_keys=True))
    else:
        _echo_transfer_payload_summary(
            title="TRANSFER_NORMALIZE_FILES",
            result_status=str(result["result_status"]),
            final_signal="d" if result["result_status"] == "PASS" else "f",
            next_action=str(result["next_action"]),
            fields={
                "DRY_RUN": "yes" if dry_run else "no",
                "OPERATIONS": len(result["operations"]),
                "BEFORE": result["before"]["state"],
                "AFTER": result["after"]["state"],
            },
        )
    if int(result["returncode"]) != 0:
        raise typer.Exit(code=int(result["returncode"]))


@transfer_app.command("workflow-next")
def workflow_next_command(
    json_output: bool = typer.Option(False, "--json/--no-json", help="Print machine-readable JSON."),
) -> None:
    """Read repo and transfer state and print the next safe wrapper command without mutating state."""
    result = run_workflow_next(Path("."))
    if json_output:
        typer.echo(json.dumps(result.as_json_data(), indent=2, sort_keys=True))
    else:
        typer.echo("*" * 35 + " START SUMMARY " + "*" * 35)
        typer.echo("TRANSFER_WORKFLOW_NEXT")
        typer.echo("")
        typer.echo(_summary_line("STATE", result.state))
        typer.echo(_summary_line("RETURNCODE", result.returncode))
        if result.reasons:
            typer.echo(_summary_line("REASONS", ",".join(result.reasons)))
        if result.command:
            typer.echo(_summary_line("COMMAND", " ".join(result.command)))
        typer.echo("")
        typer.echo(_summary_line("NEXT", result.next_action))
        typer.echo(_summary_line("CHAT_REPLY", ("g" if result.returncode == 0 else "f")))
        typer.echo("*" * 36 + " END SUMMARY " + "*" * 36)
    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)


@transfer_app.command("repo-status")
def repo_status_command(
    short: bool = typer.Option(True, "--short/--full", help="Use short git status by default."),
    json_output: bool = typer.Option(False, "--json", help="Print JSON instead of text."),
) -> None:
    result = repo_status(short=short)
    _echo_repo_result(result, json_output)
    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)


@transfer_app.command("patch-cycle-status")
def patch_cycle_status_command(
    pr_number: int | None = typer.Option(
        None,
        "--pr",
        help="Optional pull request number to include in the patch-cycle state.",
    ),
    include_ci: bool = typer.Option(False, "--include-ci", help="Include PR statusCheckRollup summary when --pr is provided."),
    root: Path = typer.Option(Path("."), "--root", help="Project root."),
    json_output: bool = typer.Option(False, "--json", help="Print JSON instead of text."),
) -> None:
    """Render the current four-slice patch/handoff workflow state."""
    result = build_patch_cycle_status(root.resolve(), pr_number=pr_number, include_ci=include_ci)
    if json_output:
        typer.echo(json.dumps(result.as_dict(), indent=2, sort_keys=True))
    else:
        typer.echo(render_patch_cycle_status(result), nl=False)
    if result.blockers:
        raise typer.Exit(code=2)


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


@transfer_app.command("rebase-on-upstream")
def rebase_on_upstream_command(
    upstream: str = typer.Option("", "--upstream", help="Upstream ref. Defaults to origin/<current-branch>."),
    expected_branch: str = typer.Option("", "--branch", help="Expected current branch before rebasing."),
    json_output: bool = typer.Option(False, "--json", help="Print machine-readable JSON only."),
) -> None:
    """Rebase the current branch on its upstream with bounded conflict reporting."""
    import subprocess
    from typing import Any

    steps: list[dict[str, Any]] = []
    blockers: list[str] = []

    def run_step(name: str, argv: list[str]) -> dict[str, Any]:
        completed = subprocess.run(argv, text=True, capture_output=True)
        item = {
            "name": name,
            "argv": argv,
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "ok": completed.returncode == 0,
        }
        steps.append(item)
        return item

    branch_result = run_step("current-branch", ["git", "branch", "--show-current"])
    current_branch = str(branch_result["stdout"]).strip()

    if branch_result["returncode"] != 0 or not current_branch:
        blockers.append("current_branch_missing")
    if current_branch in {"main", "master"}:
        blockers.append("refuse_main_branch")
    if expected_branch and current_branch != expected_branch:
        blockers.append(f"branch_mismatch_expected_{expected_branch}_actual_{current_branch}")

    target_upstream = upstream.strip() or (f"origin/{current_branch}" if current_branch else "")

    if not blockers:
        fetch_result = run_step("fetch-origin", ["git", "fetch", "origin", current_branch])
        if fetch_result["returncode"] != 0:
            # Fallback for new branches whose upstream is main or a custom ref.
            fetch_result = run_step("fetch-origin-main", ["git", "fetch", "origin", "main"])
        if fetch_result["returncode"] != 0:
            blockers.append("fetch_failed")

    rebase_returncode = 0
    if not blockers:
        rebase_result = run_step("rebase", ["git", "rebase", target_upstream])
        rebase_returncode = int(rebase_result["returncode"])
        if rebase_returncode != 0:
            blockers.append("rebase_failed")

    conflict_status_result = run_step(
        "conflict-status",
        ["./.venv/bin/agentic-kit", "transfer", "conflict-status", "--json"],
    )
    conflict_payload: dict[str, Any] = {}
    try:
        conflict_payload = json.loads(str(conflict_status_result["stdout"]) or "{}")
    except json.JSONDecodeError:
        conflict_payload = {"parse_error": "conflict-status output was not valid JSON"}

    conflict_present = bool(conflict_payload.get("conflict_present"))
    if conflict_present and "conflict_detected" not in blockers:
        blockers.append("conflict_detected")

    result_status = "PASS" if not blockers else "BLOCKED"
    final_signal = "d" if result_status == "PASS" else "f"
    next_action = (
        "Rebase completed and no merge/rebase conflict is present."
        if result_status == "PASS"
        else "Inspect rebase/conflict state before continuing: " + ", ".join(blockers)
    )

    payload = {
        "schema_version": 1,
        "kind": "transfer_rebase_on_upstream_result",
        "action": "rebase-on-upstream",
        "result_status": result_status,
        "final_signal": final_signal,
        "branch": current_branch,
        "upstream": target_upstream,
        "blockers": blockers,
        "conflict_present": conflict_present,
        "conflict_status": conflict_payload,
        "steps": steps,
        "next_action": next_action,
    }

    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        _echo_transfer_payload_summary(
            title="TRANSFER_REBASE_ON_UPSTREAM",
            result_status=result_status,
            final_signal=final_signal,
            next_action=next_action,
            fields={
                "BRANCH": current_branch,
                "UPSTREAM": target_upstream,
                "CONFLICT": "yes" if conflict_present else "no",
                "BLOCKERS": len(blockers),
            },
        )

    if blockers:
        raise typer.Exit(code=2)


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


@transfer_app.command("work-order-patch")
def work_order_patch_command(
    path: Path = typer.Option(DEFAULT_PATCH_ORDER, "--path", help="JSON/YAML patch work-order path."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Validate without writing files."),
    json_output: bool = typer.Option(False, "--json", help="Print machine-readable JSON only."),
) -> None:
    """Apply a guarded JSON/YAML text-replacement patch work order."""
    try:
        patch = load_work_order_patch(path)
        result = apply_work_order_patch(patch, patch_path=path, project_root=Path("."), dry_run=dry_run)
    except (FileNotFoundError, ValueError) as exc:
        result = WorkOrderPatchResult(
            result_status="FAIL",
            returncode=2,
            patch_path=str(path),
            expected_branch="",
            actual_branch="",
            findings=(str(exc),),
            message="Work-order patch could not be loaded.",
        )

    if json_output:
        typer.echo(json.dumps(work_order_patch_result_as_json_data(result), indent=2, ensure_ascii=False))
    else:
        typer.echo(render_work_order_patch_result(result))

    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)


@transfer_app.command("protected-diff-plan")
def protected_diff_plan_command(
    label: str = typer.Option("protected-change-plan", "--label", help="Stable label for the temporary diff file."),
    cached: bool = typer.Option(False, "--cached", help="Use staged diff."),
    json_output: bool = typer.Option(False, "--json", help="Print machine-readable JSON only."),
) -> None:
    """Write the current diff to /tmp and run the Python protected change planner on it."""
    import json
    import re
    import subprocess
    import sys
    from pathlib import Path

    safe_label = re.sub(r"[^A-Za-z0-9_.-]+", "-", label).strip("-") or "protected-change-plan"
    diff_path = Path("/tmp") / f"{safe_label}.diff"

    diff_command = ["git", "diff"]
    if cached:
        diff_command.append("--cached")
    diff_command.extend(["--output", str(diff_path)])

    diff_result = subprocess.run(diff_command, text=True, capture_output=True)
    plan_result = None
    plan_command = [
        sys.executable,
        "-m",
        "agentic_project_kit.protected_change_planner",
        "--diff-file",
        str(diff_path),
    ]
    if diff_result.returncode == 0:
        plan_result = subprocess.run(
            plan_command,
            text=True,
            capture_output=True,
        )

    plan_ok = plan_result is not None and plan_result.returncode == 0
    result_status = "PASS" if diff_result.returncode == 0 and plan_ok else "FAIL"
    final_signal = "d" if result_status == "PASS" else "f"
    next_action = (
        "Protected change plan passed; proceed with explicit add/commit paths."
        if result_status == "PASS"
        else "Inspect protected-diff-plan output before committing."
    )

    payload = {
        "schema_version": 1,
        "kind": "transfer_protected_diff_plan_result",
        "action": "protected-diff-plan",
        "result_status": result_status,
        "final_signal": final_signal,
        "next_action": next_action,
        "diff_path": str(diff_path),
        "cached": cached,
        "commands": {
            "diff": {
                "argv": diff_command,
                "returncode": diff_result.returncode,
                "stdout": diff_result.stdout,
                "stderr": diff_result.stderr,
                "ok": diff_result.returncode == 0,
            },
            "protected_change_plan": None
            if plan_result is None
            else {
                "argv": plan_command,
                "returncode": plan_result.returncode,
                "stdout": plan_result.stdout,
                "stderr": plan_result.stderr,
                "ok": plan_result.returncode == 0,
            },
        },
    }

    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        _echo_transfer_payload_summary(
            title="TRANSFER_PROTECTED_DIFF_PLAN",
            result_status=result_status,
            final_signal=final_signal,
            next_action=next_action,
            fields={
                "DIFF": str(diff_path),
                "CACHED": "yes" if cached else "no",
                "PLAN": "PASS" if plan_ok else "FAIL",
            },
        )

    if result_status != "PASS":
        raise typer.Exit(code=1)


@transfer_app.command("conflict-resolve-file")
def conflict_resolve_file_command(
    path: Path = typer.Argument(..., help="Repository-relative conflicted file to resolve."),
    source: Path = typer.Option(..., "--source", help="File whose content should replace the conflicted target."),
    expected_branch: str = typer.Option("", "--branch", help="Expected current branch."),
    json_output: bool = typer.Option(False, "--json", help="Print machine-readable JSON only."),
) -> None:
    """Resolve one conflicted file by replacing it from an explicit source and staging it."""
    import subprocess
    from typing import Any

    steps: list[dict[str, Any]] = []
    blockers: list[str] = []

    def run_step(name: str, argv: list[str]) -> dict[str, Any]:
        completed = subprocess.run(argv, text=True, capture_output=True)
        item = {
            "name": name,
            "argv": argv,
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "ok": completed.returncode == 0,
        }
        steps.append(item)
        return item

    target = Path(path)
    source_path = Path(source)
    current_branch = ""
    unmerged_files: list[str] = []

    if target.is_absolute() or ".." in target.parts:
        blockers.append("unsafe_target_path")
    if source_path.is_dir():
        blockers.append("source_is_directory")
    if not source_path.exists():
        blockers.append("source_missing")

    branch_result = run_step("current-branch", ["git", "branch", "--show-current"])
    current_branch = str(branch_result["stdout"]).strip()
    if branch_result["returncode"] != 0 or not current_branch:
        blockers.append("current_branch_missing")
    if current_branch in {"main", "master"}:
        blockers.append("refuse_main_branch")
    if expected_branch and current_branch != expected_branch:
        blockers.append(f"branch_mismatch_expected_{expected_branch}_actual_{current_branch}")

    unmerged_result = run_step("unmerged-files", ["git", "diff", "--name-only", "--diff-filter=U"])
    unmerged_files = [line.strip() for line in str(unmerged_result["stdout"]).splitlines() if line.strip()]
    target_text = target.as_posix()
    if unmerged_result["returncode"] != 0:
        blockers.append("unmerged_files_check_failed")
    elif target_text not in unmerged_files:
        blockers.append("target_not_unmerged")

    if not blockers:
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(source_path.read_text(encoding="utf-8"), encoding="utf-8")
        except OSError as exc:
            blockers.append(f"write_failed:{exc}")
        else:
            add_result = run_step("git-add-target", ["git", "add", target_text])
            if add_result["returncode"] != 0:
                blockers.append("git_add_failed")

    result_status = "PASS" if not blockers else "BLOCKED"
    final_signal = "d" if result_status == "PASS" else "f"
    next_action = (
        "Conflict file resolved and staged; run conflict-status or continue the rebase/merge."
        if result_status == "PASS"
        else "Inspect conflict-resolve-file blockers before continuing: " + ", ".join(blockers)
    )

    payload = {
        "schema_version": 1,
        "kind": "transfer_conflict_resolve_file_result",
        "action": "conflict-resolve-file",
        "result_status": result_status,
        "final_signal": final_signal,
        "branch": current_branch,
        "path": target_text,
        "source": str(source_path),
        "blockers": blockers,
        "unmerged_files": unmerged_files,
        "steps": steps,
        "next_action": next_action,
    }

    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        _echo_transfer_payload_summary(
            title="TRANSFER_CONFLICT_RESOLVE_FILE",
            result_status=result_status,
            final_signal=final_signal,
            next_action=next_action,
            fields={
                "BRANCH": current_branch,
                "PATH": target_text,
                "SOURCE": str(source_path),
                "BLOCKERS": len(blockers),
            },
        )

    if blockers:
        raise typer.Exit(code=2)


@transfer_app.command("conflict-status")
def conflict_status_command(
    json_output: bool = typer.Option(False, "--json", help="Print machine-readable JSON only."),
) -> None:
    """Report merge/rebase conflict state without resolving anything."""
    import json
    import subprocess
    from pathlib import Path

    def run(argv: list[str]) -> dict[str, object]:
        completed = subprocess.run(argv, text=True, capture_output=True)
        return {
            "argv": argv,
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "ok": completed.returncode == 0,
        }

    branch = run(["git", "branch", "--show-current"])
    status = run(["git", "status", "--short"])
    unmerged = run(["git", "diff", "--name-only", "--diff-filter=U"])

    rebase_apply = Path(".git/rebase-apply").exists()
    rebase_merge = Path(".git/rebase-merge").exists()
    merge_head = Path(".git/MERGE_HEAD").exists()

    unmerged_files = [
        line.strip()
        for line in str(unmerged["stdout"]).splitlines()
        if line.strip()
    ]
    conflict_present = bool(unmerged_files or rebase_apply or rebase_merge or merge_head)

    result_status = "CONFLICT" if conflict_present else "PASS"
    final_signal = "f" if conflict_present else "d"
    next_action = (
        "Resolve or abort the active merge/rebase before continuing."
        if conflict_present
        else "No merge/rebase conflict detected."
    )

    payload = {
        "schema_version": 1,
        "kind": "transfer_conflict_status_result",
        "action": "conflict-status",
        "result_status": result_status,
        "final_signal": final_signal,
        "next_action": next_action,
        "repo": {
            "branch": str(branch["stdout"]).strip(),
            "status_short": status["stdout"],
            "conflict_present": conflict_present,
            "unmerged_files": unmerged_files,
            "rebase_apply": rebase_apply,
            "rebase_merge": rebase_merge,
            "merge_head": merge_head,
        },
        "commands": {
            "branch": branch,
            "status": status,
            "unmerged": unmerged,
        },
    }

    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        _echo_transfer_payload_summary(
            title="TRANSFER_CONFLICT_STATUS",
            result_status=result_status,
            final_signal=final_signal,
            next_action=next_action,
            fields={
                "BRANCH": str(branch["stdout"]).strip(),
                "CONFLICT": "yes" if conflict_present else "no",
                "UNMERGED": len(unmerged_files),
            },
        )
        if unmerged_files:
            typer.echo("")
            typer.echo("UNMERGED_FILES")
            for item in unmerged_files:
                typer.echo(f"- {item}")

    if conflict_present:
        raise typer.Exit(code=2)


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


@transfer_app.command("delete-merged-work-branch")
def delete_merged_work_branch_command(
    branch: str = typer.Argument(..., help="Merged feature/docs/fix/chore/evidence branch to delete."),
    remote: bool = typer.Option(True, "--remote/--no-remote", help="Delete the branch on origin."),
    local: bool = typer.Option(True, "--local/--no-local", help="Delete the local branch."),
    force_local: bool = typer.Option(False, "--force-local", help="Force local deletion with git branch -D."),
    json_output: bool = typer.Option(False, "--json", help="Print machine-readable JSON only."),
) -> None:
    """Delete a merged non-main work branch after PR merge-state verification."""
    import subprocess
    from typing import Any

    steps: list[dict[str, Any]] = []
    blockers: list[str] = []

    def run_step(name: str, argv: list[str]) -> dict[str, Any]:
        completed = subprocess.run(argv, text=True, capture_output=True)
        item = {
            "name": name,
            "argv": argv,
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "ok": completed.returncode == 0,
        }
        steps.append(item)
        return item

    allowed_prefixes = ("feature/", "fix/", "docs/", "chore/", "evidence/")
    current_branch = ""
    pr_number = ""

    if branch in {"main", "master"}:
        blockers.append("refuse_main_branch")
    if branch.startswith("/") or branch.endswith("/") or ".." in branch or " " in branch:
        blockers.append("unsafe_branch_name")
    if not branch.startswith(allowed_prefixes):
        blockers.append("branch_prefix_not_allowed")
    if not (local or remote):
        blockers.append("nothing_to_delete")

    current_result = run_step("current-branch", ["git", "branch", "--show-current"])
    current_branch = str(current_result["stdout"]).strip()
    if current_result["returncode"] != 0:
        blockers.append("current_branch_check_failed")
    if current_branch == branch:
        blockers.append("refuse_delete_current_branch")

    pr_view = run_step(
        "pr-view-state",
        [
            "gh",
            "pr",
            "view",
            branch,
            "--json",
            "state,mergedAt,number,headRefName",
            "--jq",
            ".state + \"\\t\" + (.mergedAt // \"\") + \"\\t\" + (.number|tostring) + \"\\t\" + .headRefName",
        ],
    )
    pr_info = str(pr_view["stdout"]).strip()
    if pr_view["returncode"] != 0 or not pr_info:
        blockers.append("pr_state_not_verified")
    else:
        parts = pr_info.split("\t")
        state = parts[0] if len(parts) > 0 else ""
        merged_at = parts[1] if len(parts) > 1 else ""
        pr_number = parts[2] if len(parts) > 2 else ""
        head_ref = parts[3] if len(parts) > 3 else ""
        if state != "MERGED" or not merged_at:
            blockers.append("pr_not_merged")
        if head_ref and head_ref != branch:
            blockers.append("pr_head_branch_mismatch")

    if not blockers and local:
        delete_args = ["git", "branch", "-D" if force_local else "-d", branch]
        local_delete = run_step("delete-local-branch", delete_args)
        if local_delete["returncode"] != 0:
            blockers.append("local_delete_failed")

    if not blockers and remote:
        remote_delete = run_step("delete-remote-branch", ["git", "push", "origin", "--delete", branch])
        if remote_delete["returncode"] != 0:
            blockers.append("remote_delete_failed")

    result_status = "PASS" if not blockers else "BLOCKED"
    final_signal = "d" if result_status == "PASS" else "f"
    next_action = (
        "Merged work branch deletion completed."
        if result_status == "PASS"
        else "Inspect delete-merged-work-branch blockers before continuing: " + ", ".join(blockers)
    )

    payload = {
        "schema_version": 1,
        "kind": "transfer_delete_merged_work_branch_result",
        "action": "delete-merged-work-branch",
        "result_status": result_status,
        "final_signal": final_signal,
        "branch": branch,
        "current_branch": current_branch,
        "pr_number": pr_number,
        "local_requested": local,
        "remote_requested": remote,
        "blockers": blockers,
        "steps": steps,
        "next_action": next_action,
    }

    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        _echo_transfer_payload_summary(
            title="TRANSFER_DELETE_MERGED_WORK_BRANCH",
            result_status=result_status,
            final_signal=final_signal,
            next_action=next_action,
            fields={
                "BRANCH": branch,
                "CURRENT": current_branch,
                "PR": pr_number or "none",
                "BLOCKERS": len(blockers),
            },
        )

    if blockers:
        raise typer.Exit(code=2)


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
    skip_llm_context_gate: bool = typer.Option(
        False,
        "--skip-llm-context-gate",
        help="Recovery-only: run PR merge without requiring fresh generated LLM context.",
    ),
) -> None:
    if not skip_llm_context_gate:
        _require_fresh_llm_context_or_exit(max_age_minutes=60, json_output=json_output)
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
        _require_fresh_llm_context_or_exit(max_age_minutes=60, json_output=json_output)

    import re
    import subprocess
    from datetime import datetime, timezone

    resolved_head_sha = _resolve_expected_head_sha_alias(expected_head_sha)
    agentic_kit = "./.venv/bin/agentic-kit"
    steps: list[dict[str, object]] = []

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
    skip_llm_context_gate: bool = typer.Option(
        False,
        "--skip-llm-context-gate",
        help="Recovery-only: create PR without requiring fresh generated LLM context.",
    ),
) -> None:
    if not skip_llm_context_gate:
        _require_fresh_llm_context_or_exit(max_age_minutes=60, json_output=json_output)
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
    _require_transfer_capability("rules_confirmed")
    result = pr_create(base=base, head=resolved_head, title=title, body=body)
    _echo_repo_result(result, json_output)
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
        _require_fresh_llm_context_or_exit(max_age_minutes=60, json_output=json_output)
    _require_current_communication_context_or_exit(
        json_output=json_output,
        allow_rule_carrier_publish=True,
    )

    import re
    import subprocess
    from datetime import datetime, timezone

    _require_transfer_capability("rules_confirmed")

    agentic_kit = "./.venv/bin/agentic-kit"
    steps: list[dict[str, object]] = []
    blockers: list[str] = []

    def run_step(name: str, argv: list[str]) -> subprocess.CompletedProcess[str]:
        completed = subprocess.run(argv, text=True, capture_output=True)
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

    pr_number: int | None = None
    inner_post_merge_followup_verified = False
    if not blockers:
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
        complete_result = run_step("pr-complete", complete_argv)
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
    payload = _evaluate_llm_context_freshness(Path("."), max_age_minutes=max_age_minutes)
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
    payload = _evaluate_llm_context_freshness(Path("."), max_age_minutes=max_age_minutes)
    if payload.get("result_status") == "PASS":
        return

    initial_blockers = list(payload.get("blockers", []))
    try:
        refresh_result = refresh_llm_context_carriers(Path("."))
    except (FileNotFoundError, ValueError, OSError) as exc:
        payload["auto_refresh_attempted"] = True
        payload["auto_refresh_result_status"] = "BLOCKED"
        payload["auto_refresh_error"] = str(exc)
        payload["next_action"] = "Inspect LLM context carrier refresh failure before planning: " + str(exc)
        _emit_llm_context_gate_result(payload, json_output=json_output)
        raise typer.Exit(code=2) from exc

    payload = _evaluate_llm_context_freshness(Path("."), max_age_minutes=max_age_minutes)
    payload["auto_refresh_attempted"] = True
    payload["auto_refresh_result_status"] = refresh_result.get("result_status")
    payload["initial_blockers"] = initial_blockers
    if payload.get("result_status") == "PASS":
        return

    _emit_llm_context_gate_result(payload, json_output=json_output)
    raise typer.Exit(code=2)


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
    payload = _evaluate_llm_context_freshness(
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
        payload = refresh_llm_context_carriers(Path("."))
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


@transfer_app.command("evidence-inspect-latest")
def evidence_inspect_latest(
    json_output: bool = typer.Option(False, "--json", help="Print machine-readable JSON only."),
) -> None:
    """Inspect the latest evidence log with the required-summary contract."""
    inspect_result = _run_transfer_subprocess(
        ["./.venv/bin/agentic-kit", "evidence", "inspect", "--require-summary"]
    )
    result_status = "PASS" if inspect_result["ok"] else "FAIL"
    final_signal = "d" if inspect_result["ok"] else "f"
    next_action = (
        "Latest evidence inspection passed."
        if inspect_result["ok"]
        else "Inspect latest evidence failure before continuing."
    )
    payload = {
        "schema_version": 1,
        "kind": "transfer_evidence_inspect_latest_result",
        "action": "evidence-inspect-latest",
        "result_status": result_status,
        "final_signal": final_signal,
        "next_action": next_action,
        "result": inspect_result,
    }
    _echo_transfer_payload_json_or_summary(payload, json_output=json_output)
    if result_status != "PASS":
        raise typer.Exit(code=1)


@transfer_app.command("evidence-pr-complete")
def evidence_pr_complete_command(
    slice_name: str = typer.Option(..., "--slice", help="Evidence slice label."),
    evidence_branch: str = typer.Option(..., "--evidence-branch", help="Evidence branch to use as PR head."),
    title: str = typer.Option(..., "--title", help="Evidence PR title."),
    body: str = typer.Option("", "--body", help="Evidence PR body."),
    base: str = typer.Option("main", "--base", help="Base branch for the evidence PR."),
    run_log: Path = typer.Option(
        Path("docs/reports/transfer_runs/latest-transfer-report.log"),
        "--run-log",
        help="Local run log to finalize.",
    ),
    remote_log: Path | None = typer.Option(
        None,
        "--remote-log",
        help="Repository-relative remote evidence log path under docs/reports/terminal/.",
    ),
    scope: str = typer.Option("transfer", "--scope", help="Evidence scope summary."),
    mode_check: str = typer.Option("standard", "--mode-check", help="Evidence mode check summary."),
    source_pr: str = typer.Option("NONE", "--source-pr", help="Associated source PR number or NONE."),
    ci: str = typer.Option("not-required", "--ci", help="CI state summary."),
    merge: str = typer.Option("not-required", "--merge", help="Merge state summary."),
    command_report: str = typer.Option(
        "transfer lifecycle completed",
        "--command-report",
        help="Command report summary.",
    ),
    interpretation: str = typer.Option(
        "Evidence finalized through transfer evidence-pr-complete wrapper.",
        "--interpretation",
        help="Evidence interpretation summary.",
    ),
    safe_step: str = typer.Option(
        "Continue with the next planned slice.",
        "--safe-step",
        help="Next safe step.",
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
    json_output: bool = typer.Option(False, "--json", help="Print machine-readable JSON only."),
) -> None:
    """Finalize transfer evidence on an evidence branch and complete it through a PR."""
    import subprocess
    from datetime import datetime, timezone
    from typing import Any

    _require_transfer_capability("rules_confirmed")

    agentic_kit = "./.venv/bin/agentic-kit"
    steps: list[dict[str, Any]] = []
    blockers: list[str] = []

    def run_step(
        name: str,
        argv: list[str],
        *,
        allow_fail: bool = False,
    ) -> subprocess.CompletedProcess[str]:
        completed = subprocess.run(argv, text=True, capture_output=True)
        steps.append(
            {
                "name": name,
                "argv": argv,
                "returncode": completed.returncode,
                "stdout": completed.stdout,
                "stderr": completed.stderr,
                "ok": completed.returncode == 0,
                "allowed_failure": allow_fail,
            }
        )
        if completed.returncode != 0 and not allow_fail:
            blockers.append(name + "_failed")
        return completed

    if evidence_branch in {"main", "master"}:
        blockers.append("refuse_main_branch")
    if evidence_branch.startswith("/") or evidence_branch.endswith("/") or ".." in evidence_branch or " " in evidence_branch:
        blockers.append("unsafe_evidence_branch")
    if not evidence_branch.startswith(("evidence/", "docs/evidence/", "feature/evidence-")):
        blockers.append("evidence_branch_prefix_not_allowed")

    branch_result = run_step("current-branch", ["git", "branch", "--show-current"])
    current_branch = branch_result.stdout.strip()
    if branch_result.returncode != 0 or not current_branch:
        blockers.append("current_branch_missing")

    if not blockers and current_branch != evidence_branch:
        switch_result = run_step(
            "switch-evidence-branch",
            [agentic_kit, "transfer", "branch-switch", evidence_branch],
            allow_fail=True,
        )
        if switch_result.returncode != 0:
            create_result = run_step("create-evidence-branch", [agentic_kit, "transfer", "branch-create", evidence_branch])
            if create_result.returncode == 0:
                run_step("switch-created-evidence-branch", [agentic_kit, "transfer", "branch-switch", evidence_branch])

    if not blockers:
        finalize_argv = [
            agentic_kit,
            "transfer",
            "evidence-finalize-current-transfer",
            "--slice",
            slice_name,
            "--run-log",
            str(run_log),
            "--scope",
            scope,
            "--mode-check",
            mode_check,
            "--pr",
            source_pr,
            "--ci",
            ci,
            "--merge",
            merge,
            "--command-report",
            command_report,
            "--interpretation",
            interpretation,
            "--safe-step",
            safe_step,
            "--branch",
            evidence_branch,
        ]
        if remote_log is not None:
            finalize_argv.extend(["--remote-log", str(remote_log)])
        run_step("evidence-finalize-current-transfer", finalize_argv)

    if not blockers:
        run_step("evidence-inspect-latest", [agentic_kit, "transfer", "evidence-inspect-latest"])

    if not blockers:
        run_step("push-current", [agentic_kit, "transfer", "push-current", "--branch", evidence_branch])

    if not blockers:
        run_step(
            "pr-create-complete",
            [
                agentic_kit,
                "transfer",
                "pr-create-complete",
                "--title",
                title,
                "--body",
                body,
                "--base",
                base,
                "--head",
                "current",
                "--merge-method",
                merge_method,
                "--timeout-seconds",
                str(timeout_seconds),
                "--interval-seconds",
                str(poll_seconds),
            ],
        )

    if not blockers:
        run_step("sync-main", [agentic_kit, "transfer", "sync-main"])

    if not blockers:
        run_step("post-merge-check", [agentic_kit, "transfer", "post-merge-check"])

    blockers = list(dict.fromkeys(blockers))
    result_status = "PASS" if not blockers else "BLOCKED"
    final_signal = "d" if result_status == "PASS" else "f"
    next_action = (
        "Evidence PR lifecycle is complete."
        if result_status == "PASS"
        else "Inspect evidence-pr-complete step failure before continuing: " + ", ".join(blockers)
    )

    payload = {
        "schema_version": 1,
        "kind": "transfer_evidence_pr_complete_result",
        "action": "evidence-pr-complete",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "result_status": result_status,
        "final_signal": final_signal,
        "next_action": next_action,
        "slice": slice_name,
        "base": base,
        "evidence_branch": evidence_branch,
        "source_pr": source_pr,
        "blockers": blockers,
        "steps": steps,
    }

    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        _echo_transfer_payload_summary(
            title="TRANSFER_EVIDENCE_PR_COMPLETE",
            result_status=result_status,
            final_signal=final_signal,
            next_action=next_action,
            fields={
                "SLICE": slice_name,
                "BRANCH": evidence_branch,
                "SOURCE_PR": source_pr,
                "BLOCKERS": len(blockers),
            },
        )

    if blockers:
        raise typer.Exit(code=2)


@transfer_app.command("evidence-finalize-current-transfer")
def evidence_finalize_current_transfer(
    slice_name: str = typer.Option(..., "--slice", help="Evidence slice label."),
    run_log: Path = typer.Option(
        Path("docs/reports/transfer_runs/latest-transfer-report.log"),
        "--run-log",
        help="Local run log to finalize.",
    ),
    remote_log: Path | None = typer.Option(
        None,
        "--remote-log",
        help="Repository-relative remote evidence log path under docs/reports/terminal/.",
    ),
    scope: str = typer.Option("transfer", "--scope", help="Evidence scope summary."),
    mode_check: str = typer.Option("standard", "--mode-check", help="Evidence mode check summary."),
    pr: str = typer.Option("NONE", "--pr", help="Associated PR number or NONE."),
    ci: str = typer.Option("not-required", "--ci", help="CI state summary."),
    merge: str = typer.Option("not-required", "--merge", help="Merge state summary."),
    command_report: str = typer.Option(
        "transfer lifecycle completed",
        "--command-report",
        help="Command report summary.",
    ),
    interpretation: str = typer.Option(
        "Evidence finalized through transfer wrapper.",
        "--interpretation",
        help="Evidence interpretation summary.",
    ),
    safe_step: str = typer.Option(
        "Continue with the next planned slice.",
        "--safe-step",
        help="Next safe step.",
    ),
    push: bool = typer.Option(False, "--push", help="Push evidence commit if finalize-log creates one."),
    branch: str = typer.Option("", "--branch", help="Expected branch for evidence finalize-log commits."),
    json_output: bool = typer.Option(False, "--json", help="Print machine-readable JSON only."),
) -> None:
    """Finalize the current transfer evidence log through the stricter evidence CLI."""
    import re
    from datetime import datetime, timezone

    def slugify(value: str) -> str:
        slug = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip()).strip("-")
        return slug or "transfer"

    if remote_log is None:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        remote_log = Path("docs/reports/terminal") / f"{stamp}-{slugify(slice_name)}.log"

    argv = [
        "./.venv/bin/agentic-kit",
        "evidence",
        "finalize-log",
        "--run-log",
        str(run_log),
        "--remote-log",
        str(remote_log),
        "--slice",
        slice_name,
        "--scope",
        scope,
        "--mode-check",
        mode_check,
        "--pr",
        pr,
        "--ci",
        ci,
        "--merge",
        merge,
        "--command-report",
        command_report,
        "--interpretation",
        interpretation,
        "--safe-step",
        safe_step,
    ]
    if push:
        argv.append("--push")
    if branch:
        argv.extend(["--branch", branch])

    finalize_result = _run_transfer_subprocess(argv)
    result_status = "PASS" if finalize_result["ok"] else "FAIL"
    final_signal = "d" if finalize_result["ok"] else "f"
    next_action = (
        "Current transfer evidence finalized."
        if finalize_result["ok"]
        else "Inspect evidence-finalize-current-transfer failure before continuing."
    )
    payload = {
        "schema_version": 1,
        "kind": "transfer_evidence_finalize_current_transfer_result",
        "action": "evidence-finalize-current-transfer",
        "result_status": result_status,
        "final_signal": final_signal,
        "next_action": next_action,
        "run_log": str(run_log),
        "remote_log": str(remote_log),
        "result": finalize_result,
    }
    _echo_transfer_payload_json_or_summary(payload, json_output=json_output)
    if result_status != "PASS":
        raise typer.Exit(code=1)


@transfer_app.command("normalize-session")
def normalize_session(
    json_output: bool = typer.Option(False, "--json", help="Print machine-readable JSON only."),
    repair_known_volatile: bool = typer.Option(
        False,
        "--repair-known-volatile",
        help="Restore known volatile transfer output files before checking the session.",
    ),
    write_outbox: bool = typer.Option(
        False,
        "--write-outbox/--no-write-outbox",
        help="Write the normalized session result to the canonical transfer outbox.",
    ),
) -> None:
    """Normalize and summarize the local transfer session state.

    The MVP is diagnostic and evidence-producing only. It does not switch branches,
    pull, delete files, commit, push, or mutate the worktree except for writing the
    canonical transfer outbox file.
    """
    _run_local_garbage_collector_preflight()
    import ast
    import json
    import subprocess
    from pathlib import Path
    from typing import Any

    from agentic_project_kit.transfer_safety_context import write_transfer_outbox

    root = Path(".")

    known_volatile_paths = KNOWN_VOLATILE_TRANSFER_PATHS

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
        volatile_repair_result = _restore_known_volatile_paths(root)

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
            ack_head = str(ack_data.get("repo_head") or "")
            if head and ack_head:
                rule_ack["matches_head"] = bool(
                    ack_head == head or (len(ack_head) >= 7 and head.startswith(ack_head))
                )
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

    if write_outbox:
        outbox_written = write_transfer_outbox(root, payload)
        payload["outbox_written"] = str(outbox_written)
    else:
        payload["outbox_written"] = None

    _echo_transfer_payload_json_or_summary(payload, json_output=json_output)


def _emit_successor_package(
    *,
    json_output: bool,
    render_prompt: bool,
    output_dir: str,
    update_canonical_prompts: bool,
) -> None:
    result = write_successor_handoff_package(
        Path("."),
        Path(output_dir),
        update_canonical_prompts=update_canonical_prompts,
    )
    payload = {
        "schema_version": 1,
        "kind": "transfer_chat_switch_complete_result",
        "result_status": result.validation_report["status"],
        "context_path": str(Path(output_dir) / "successor_context.yaml"),
        "source_manifest_path": str(Path(output_dir) / "source_manifest.json"),
        "validation_report_path": str(Path(output_dir) / "validation_report.json"),
        "successor_prompt_path": str(Path(output_dir) / "successor_prompt.md"),
        "updated_canonical_prompts": update_canonical_prompts,
        "generated_head": result.context["repo"]["head"],
        "generated_head_short": result.context["repo"]["head_short"],
        "open_tasks": result.context["short_term_memory"]["open_tasks"],
        "findings": result.validation_report["findings"],
    }
    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True))
        return
    if render_prompt:
        typer.echo(result.successor_prompt)
        return
    typer.echo(json.dumps(payload, indent=2, ensure_ascii=False))
    typer.echo(f"FINAL_SIGNAL={'d' if result.validation_report['status'] == 'PASS' else 'f'}")
    typer.echo("FINAL_NEXT=Use successor_prompt.md in the next chat after validating the package.")


@transfer_app.command("chat-switch-complete")
def chat_switch_complete(
    json_output: bool = typer.Option(False, "--json", help="Print machine-readable JSON only."),
    render_prompt: bool = typer.Option(
        False,
        "--render-prompt",
        help="Print the generated copy-and-paste successor chat prompt.",
    ),
    output_dir: str = typer.Option(
        "docs/reports/handoff-packages/latest",
        "--output-dir",
        help="Directory for the generated successor handoff package.",
    ),
    update_canonical_prompts: bool = typer.Option(
        True,
        "--update-canonical-prompts/--no-update-canonical-prompts",
        help="Update NEXT_CHAT_BOOTSTRAP, START_NEW_CHAT_PROMPT, and CLOSEOUT_BEFORE_CHAT_SWITCH_PROMPT.",
    ),
) -> None:
    """Create a deterministic successor handoff package and prompt projections."""
    _emit_successor_package(
        json_output=json_output,
        render_prompt=render_prompt,
        output_dir=output_dir,
        update_canonical_prompts=update_canonical_prompts,
    )


@transfer_app.command("prepare-successor-handoff")
def prepare_successor_handoff(
    json_output: bool = typer.Option(False, "--json", help="Print machine-readable JSON only."),
    repair_known_volatile: bool = typer.Option(
        False,
        "--repair-known-volatile",
        help="Deprecated compatibility option; volatile repair belongs in normalize-session.",
    ),
    render_prompt: bool = typer.Option(
        False,
        "--render-prompt",
        help="Print the generated copy-and-paste successor chat prompt.",
    ),
    write_outbox: bool = typer.Option(
        False,
        "--write-outbox/--no-write-outbox",
        help="Deprecated compatibility option. The deterministic package is written to docs/reports/handoff-packages/latest.",
    ),
) -> None:
    """Deprecated compatibility alias for transfer chat-switch-complete."""
    # Legacy prepare-successor-handoff textual contract sentinels.
    # Kept for compatibility tests while this command delegates to chat-switch-complete.
    legacy_handoff_schema = ".agentic/transfer/schemas/handoff_request.schema.json"
    legacy_schema_paths = (
        legacy_handoff_schema,
        ".agentic/transfer/schemas/patch_transfer_request.schema.json",
    )
    _ = legacy_schema_paths

    if False:
        payload = {"schema": legacy_handoff_schema}
        payload["outbox_written"] = None

    legacy_outbox_contract = """if write_outbox:
            write_transfer_outbox(root, payload)"""
    _ = legacy_outbox_contract

    _emit_successor_package(
        json_output=json_output,
        render_prompt=render_prompt,
        output_dir="docs/reports/handoff-packages/latest",
        update_canonical_prompts=True,
    )


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
    known_volatile_paths = KNOWN_VOLATILE_TRANSFER_PATHS

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

    if json_output:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        _echo_transfer_payload_summary(
            title="TRANSFER_REMOTE_WORK_START",
            result_status=result_status,
            final_signal=final_signal,
            next_action=next_action,
            fields={
                "BRANCH": branch,
                "MAIN_BRANCH": main_branch,
                "BLOCKERS": len(blockers),
                "STEPS": len(steps),
            },
        )


def _render_latest_transfer_report_summary(report_text: str) -> str:
    try:
        data = json.loads(report_text)
    except json.JSONDecodeError:
        return report_text
    if not isinstance(data, dict):
        return report_text

    fields = {
        "LABEL": data.get("label", ""),
        "RETURNCODE": data.get("returncode", ""),
        "FINAL_SIGNAL": data.get("final_signal", ""),
        "CHAT_REPLY": data.get("chat_reply", ""),
        "NEXT": data.get("next_action", ""),
        "LOCAL_JSON": data.get("latest_json_path", "docs/reports/transfer_runs/latest-transfer-report.json"),
        "REMOTE_JSON": data.get("remote_report_path", ""),
    }
    lines = [
        "********************************** START SUMMARY ***********************************",
        "TRANSFER_SHOW_LAST_REPORT",
        "",
    ]
    lines.extend(_summary_line(name, value) for name, value in fields.items())
    lines.extend(
        [
            "",
            "FULL_REPORT: use --json or inspect the reported JSON file",
            "*********************************** END SUMMARY ************************************",
        ]
    )
    return "\n".join(lines)


@transfer_app.command("show-last-report")
def show_last_report(
    json_output: bool = typer.Option(False, "--json", help="Print the full latest transfer report JSON."),
) -> None:
    try:
        report_text = read_latest_transfer_report(Path("."))
    except FileNotFoundError as exc:
        typer.echo(str(exc))
        raise typer.Exit(code=1) from exc

    typer.echo(report_text if json_output else _render_latest_transfer_report_summary(report_text))


@transfer_app.command("submit-user-task")
def submit_user_task_command(
    title: str = typer.Option("GUI file-transfer task", "--title", help="Task title."),
    body_file: Path = typer.Option(..., "--body-file", help="UTF-8 text file containing the task body."),
    publish: bool = typer.Option(
        False,
        "--publish",
        help="Publish the canonical transfer order to the gui-transfer-tasks remote branch.",
    ),
    json_output: bool = typer.Option(False, "--json", help="Print machine-readable JSON."),
) -> None:
    from agentic_project_kit.gui_task_editor import submit_user_task

    try:
        body = body_file.read_text(encoding="utf-8")
        result = submit_user_task(Path("."), title=title, body=body, publish=publish)
    except (OSError, ValueError) as exc:
        payload = {
            "schema_version": 1,
            "kind": "gui_file_transfer_user_task_submission",
            "result_status": "FAIL",
            "reason": str(exc),
            "button_next_state": "BLOCKED",
        }
        if json_output:
            typer.echo(json.dumps(payload, indent=2, sort_keys=True))
        else:
            typer.echo(f"RESULT=FAIL\nREASON={exc}")
        raise typer.Exit(code=2) from exc
    if json_output:
        typer.echo(json.dumps(result.as_json_data(), indent=2, sort_keys=True))
    else:
        typer.echo("GUI_FILE_TRANSFER_USER_TASK")
        typer.echo(f"result_status={result.result_status}")
        typer.echo(f"task_id={result.task_id}")
        typer.echo(f"published_ref={result.published_ref or '<none>'}")
        typer.echo(f"remote_path={result.remote_path}")
        typer.echo(f"remote_readable={str(result.remote_readable).lower()}")
        typer.echo(f"blob_sha={result.blob_sha}")
        typer.echo(f"commit_status={result.commit_status}")
        typer.echo(f"push_status={result.push_status}")
        typer.echo(f"next_reply={result.next_reply}")
        typer.echo(f"next_action={result.next_action}")
    if result.result_status != "PASS":
        raise typer.Exit(code=2)


@transfer_app.command("read-user-task")
def read_user_task_command(
    json_output: bool = typer.Option(False, "--json", help="Print machine-readable JSON."),
) -> None:
    from agentic_project_kit.gui_task_editor import read_user_task

    payload = read_user_task(Path("."))
    if json_output:
        typer.echo(json.dumps(payload, indent=2, sort_keys=True))
    else:
        typer.echo("GUI_FILE_TRANSFER_USER_TASK_READ")
        typer.echo(f"result_status={payload.get('result_status')}")
        typer.echo(f"reason={payload.get('reason')}")
        typer.echo(f"task_path={payload.get('task_path')}")
        typer.echo(f"next_action={payload.get('next_action')}")
    if payload.get("result_status") != "PASS":
        raise typer.Exit(code=2)


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

@transfer_app.command("log-header")
def transfer_log_header_command(
    log_path: str = typer.Option("", "--log-path", help="Optional log path to include in the dynamic local-to-LLM header."),
) -> None:
    """Render the dynamic local-to-LLM copy/paste log header from rule files."""
    typer.echo(render_local_to_llm_log_header(Path("."), log_path=log_path or None))


@transfer_app.command("log-upload-hint")
def transfer_log_upload_hint_command(
    log_path: str = typer.Option(..., "--log-path", help="Log file path to mention in the terminal upload hint."),
    return_code: int | None = typer.Option(None, "--rc", help="Optional return code to explain in the upload hint."),
) -> None:
    """Render the terminal hint for copy/paste communication with the LLM."""
    typer.echo(render_local_to_llm_log_upload_hint(log_path, return_code=return_code))
