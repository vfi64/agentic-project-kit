from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agentic_project_kit.workspace import LEGACY_DEFAULTS, load_workspace

try:
    import yaml
except Exception:  # pragma: no cover - PyYAML is expected in the project env.
    yaml = None  # type: ignore[assignment]


COMMAND_REFERENCE_JSON = Path(LEGACY_DEFAULTS.reference_root) / "agentic-kit-commands.json"
COMMAND_REFERENCE_MD = Path(LEGACY_DEFAULTS.reference_root) / "AGENTIC_KIT_COMMANDS.md"
COMPILED_CONTEXT = Path(".agentic/compiled_agent_context.yaml")
TRANSFER_SAFETY_RULES = Path(".agentic/transfer_safety_rules.yaml")
ONE_COMMAND_PROTOCOL = Path(".agentic/transfer/one_command_transfer_protocol.yaml")

CANONICAL_SOURCES = (
    COMPILED_CONTEXT,
    TRANSFER_SAFETY_RULES,
    ONE_COMMAND_PROTOCOL,
    COMMAND_REFERENCE_JSON,
    COMMAND_REFERENCE_MD,
)

IMPORTANT_WRAPPERS = (
    "agentic-kit transfer continue",
    "agentic-kit transfer remote-next",
    "agentic-kit transfer chat-switch-complete",
    "agentic-kit transfer command-reference-refresh",
    "agentic-kit transfer command-reference-check",
    "agentic-kit transfer sync-main",
    "agentic-kit transfer remote-work-start",
    "agentic-kit transfer protected-diff-plan",
    "agentic-kit transfer pr-create-complete",
    "agentic-kit transfer pr-create-complete --post-merge-complete",
    "agentic-kit transfer pr-complete",
    "agentic-kit transfer post-merge-complete",
    "agentic-kit transfer post-merge-check",
    "agentic-kit transfer repo-status",
    "agentic-kit transfer run-and-log",
    "agentic-kit transfer publish-last-report",
    "agentic-kit transfer show-last-report",
)


def build_llm_execution_context(root: str | Path = ".") -> dict[str, Any]:
    """Build a fresh machine-readable context capsule for LLM-facing reports.

    The capsule is a generated projection. It is not a new source of truth.
    It points back to canonical rule files, current command reference files, and
    current git state so a successor chat can avoid reconstructing commands or
    workflow policy from memory.
    """

    root_path = Path(root)
    command_reference = _load_command_reference(root_path)
    transfer_rules = _load_yaml(root_path / TRANSFER_SAFETY_RULES)
    protocol = _load_yaml(root_path / ONE_COMMAND_PROTOCOL)

    return {
        "schema_version": 1,
        "kind": "llm_execution_context",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "generated_from_current_repo": True,
        "projection_only_not_source_of_truth": True,
        "source_files": [str(path) for path in CANONICAL_SOURCES],
        "source_hashes": _source_hashes(root_path),
        "command_reference": {
            "json": str(COMMAND_REFERENCE_JSON),
            "markdown": str(COMMAND_REFERENCE_MD),
            "command_count": _command_count(command_reference),
            "generated_by": _command_reference_meta(command_reference).get("generated_by", ""),
            "must_not_reconstruct_commands_from_memory": True,
            "important_wrappers": _important_wrappers(command_reference),
        },
        "execution_policy": _execution_policy(transfer_rules, protocol),
        "llm_to_local_transfer_policy": transfer_rules.get("llm_to_local_transfer_policy", {}),
        "command_integration_governance": transfer_rules.get("command_integration_governance", {}),
        "context_quality": {
            "generated_from_current_repo_sources": True,
            "source_hashes_present": True,
            "source_hashes_complete": all(_source_hashes(root_path).values()),
            "machine_readable": True,
            "projection_only_not_source_of_truth": True,
            "must_be_regenerated_from_rules_not_cached": True,
        },
        "running_chat_refresh_contract": transfer_rules.get("running_chat_refresh_contract", {}),
        "shell_placeholder_policy": transfer_rules.get("shell_placeholder_policy", {}),
        "canonical_lifecycle": {
            "new_pr_single_command_text": "agentic-kit transfer pr-create-complete --post-merge-complete",
            "verify_context_refresh_command": "agentic-kit transfer verify-llm-context-refresh",
            "feature_branch_pre_pr_gate": "agentic-kit transfer repo-status",
            "forbidden_feature_branch_pre_pr_gate": "agentic-kit transfer post-merge-check",
            "fresh_llm_context_before_pr": [
                "./.venv/bin/agentic-kit transfer prepare-successor-handoff --render-prompt",
                "./.venv/bin/agentic-kit transfer publish-last-report",
                "./.venv/bin/agentic-kit transfer require-fresh-llm-context --json",
            ],
            "post_merge_checks_belong_to_main": True,
            "post_merge_check_after_merge_only": True,
            "do_not_use_stale_prompt_text_as_handoff_source": True,
            "new_pr_single_command": [
                "./.venv/bin/agentic-kit",
                "transfer",
                "pr-create-complete",
                "--post-merge-complete",
                "--base",
                "main",
                "--head",
                "current",
                "--merge-method",
                "squash",
            ],
            "existing_pr_requires_concrete_number": [
                "./.venv/bin/agentic-kit",
                "transfer",
                "pr-complete",
                "use-the-concrete-pr-number-from-wrapper-output",
                "--expected-head-sha",
                "current",
                "--merge-method",
                "squash",
            ],
            "post_merge_requires_concrete_number": [
                "./.venv/bin/agentic-kit transfer sync-main",
                "./.venv/bin/agentic-kit transfer post-merge-complete --after-pr use-the-concrete-pr-number-from-wrapper-output",
                "./.venv/bin/agentic-kit transfer sync-main",
                "./.venv/bin/agentic-kit transfer post-merge-check",
                "./.venv/bin/agentic-kit transfer repo-status",
            ],
            "shell_placeholder_policy": {
                "no_angle_bracket_placeholders_in_executable_blocks": True,
                "if_pr_number_unknown_first_run_diagnostic_not_shell_placeholder": True,
                "known_failure_example": "zsh parses angle-bracket placeholders as redirection",
            },
        },
        "terminal_resilience": {
            "avoid_process_ended_terminal_dead_end": True,
            "do_not_require_terminal_restart_after_script_errors": True,
            "patch_scripts_should_report_status_and_return_to_shell": True,
            "avoid_unnecessary_raise_system_exit_in_diagnostics": True,
            "avoid_set_euo_pipefail_in_exploratory_patch_blocks": True,
        },
        "patch_generation_policy": {
            "avoid_heredoc_quote_escape_drift": True,
            "avoid_long_shell_mutation_blocks": True,
            "avoid_fragile_multiline_inline_python_anchors": True,
            "avoid_raw_newlines_inside_generated_python_string_literals": True,
            "prefer_small_python_patch_scripts_with_stable_checks": True,
        },
        "volatile_cleanup": {
            "known_paths": [
                ".agentic/transfer/inbox/next_command.py.txt",
                ".agentic/transfer/outbox/last_result.txt",
                "docs/reports/terminal/transfer_handoff_reports/latest-transfer-handoff-report.json",
                "docs/reports/terminal/transfer_handoff_reports/latest-transfer-handoff-report.log",
            ],
            "only_when_not_target_changes": True,
            "must_not_discard_substantive_changes": True,
        },
        "git_state": _git_state(root_path),
    }


def attach_llm_execution_context(payload: dict[str, Any], root: str | Path = ".") -> dict[str, Any]:
    payload["llm_execution_context"] = build_llm_execution_context(root)
    return payload


def _source_hashes(root: Path) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for relative in CANONICAL_SOURCES:
        path = root / relative
        if not path.exists():
            hashes[str(relative)] = "missing"
            continue
        hashes[str(relative)] = hashlib.sha256(path.read_bytes()).hexdigest()
    return hashes


def _load_yaml(path: Path) -> dict[str, Any]:
    if yaml is None or not path.exists():
        return {}
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    return raw if isinstance(raw, dict) else {}


def _load_command_reference(root: Path) -> dict[str, Any]:
    path = load_workspace(root).reference_file("agentic-kit-commands.json")
    if not path.exists():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return raw if isinstance(raw, dict) else {}


def _command_reference_meta(command_reference: dict[str, Any]) -> dict[str, Any]:
    meta = command_reference.get("metadata")
    if isinstance(meta, dict):
        return meta
    return {key: command_reference.get(key, "") for key in ("generated_by", "kind")}


def _iter_commands(command_reference: dict[str, Any]) -> list[dict[str, Any]]:
    for key in ("commands", "items"):
        value = command_reference.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    return []


def _command_count(command_reference: dict[str, Any]) -> int:
    return len(_iter_commands(command_reference))


def _important_wrappers(command_reference: dict[str, Any]) -> list[dict[str, Any]]:
    commands = _iter_commands(command_reference)
    by_name = {
        str(item.get("qualified_name", "")): item
        for item in commands
        if isinstance(item.get("qualified_name", ""), str)
    }
    wrappers: list[dict[str, Any]] = []
    for qualified in IMPORTANT_WRAPPERS:
        item = by_name.get(qualified)
        wrappers.append(
            {
                "qualified_name": qualified,
                "present": item is not None,
                "help": str(item.get("help", "")) if item else "",
                "options": _option_names(item or {}),
            }
        )
    return wrappers


def _option_names(command: dict[str, Any]) -> list[str]:
    options: list[str] = []
    for param in command.get("params", []) or command.get("parameters", []) or []:
        if not isinstance(param, dict):
            continue
        for field in ("opts", "option_strings", "names"):
            raw = param.get(field)
            if isinstance(raw, list):
                options.extend(str(item) for item in raw if str(item).startswith("-"))
        raw_name = param.get("opts")
        if isinstance(raw_name, str) and raw_name.startswith("-"):
            options.append(raw_name)
    return sorted(dict.fromkeys(options))


def _execution_policy(transfer_rules: dict[str, Any], protocol: dict[str, Any]) -> dict[str, Any]:
    encoded = json.dumps([transfer_rules, protocol], sort_keys=True, ensure_ascii=False)
    return {
        "wrapper_first": "wrapper-first" in encoded or "wrapper_first" in encoded,
        "transfer_file_second": "transfer-file second" in encoded or "transfer_file_second" in encoded,
        "copy_paste_last": "copy/paste shell only as fallback" in encoded or "copy_paste" in encoded,
        "post_merge_complete_required_after_merge": "post-merge-complete --after-pr" in encoded,
        "run_and_log_is_diagnostic_only": "run-and-log only for diagnostics" in encoded or "not as replacement for post-merge-complete" in encoded,
        "read_remote_report_before_planning_after_g": "continue_from_chat_memory" in encoded and "read_latest_remote_transfer_report_first" in encoded,
    }


def _git_state(root: Path) -> dict[str, Any]:
    return {
        "branch": _git(root, ["git", "branch", "--show-current"]),
        "head": _git(root, ["git", "rev-parse", "HEAD"]),
        "status_short": _git(root, ["git", "status", "--short"]),
    }


def _git(root: Path, cmd: list[str]) -> str:
    completed = subprocess.run(cmd, cwd=root, text=True, capture_output=True)
    if completed.returncode != 0:
        return ""
    return completed.stdout.strip()
