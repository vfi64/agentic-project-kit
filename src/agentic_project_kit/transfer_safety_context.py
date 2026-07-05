from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from agentic_project_kit.llm_execution_context import build_llm_execution_context

import yaml

TRANSFER_SAFETY_RULES = Path(".agentic/transfer_safety_rules.yaml")
ONE_COMMAND_TRANSFER_PROTOCOL = Path(".agentic/transfer/one_command_transfer_protocol.yaml")
OUTBOX_LAST_RESULT = Path(".agentic/transfer/outbox/last_result.txt")
META_COMMAND_PREFERENCE_SOURCES = (
    ".agentic/transfer_safety_rules.yaml",
    ".agentic/transfer/one_command_transfer_protocol.yaml",
)


LLM_WORK_ORDER_CONTRACT_SOURCES = (
    ".agentic/transfer_safety_rules.yaml",
    ".agentic/transfer/one_command_transfer_protocol.yaml",
)


CANONICAL_SOURCE_PATHS = (
    ".agentic/transfer_safety_rules.yaml",
    ".agentic/transfer/one_command_transfer_protocol.yaml",
    ".agentic/rule_mechanism_inventory.yaml",
    ".agentic/rule_preservation.yaml",
    "docs/DOCUMENTATION_REGISTRY.yaml",
    "docs/planning/PROJECT_DIRECTION.yaml",
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git(root: Path, args: list[str]) -> str:
    completed = subprocess.run(["git", *args], cwd=root, text=True, capture_output=True, check=False)
    if completed.returncode != 0:
        return ""
    return completed.stdout.strip()


def load_transfer_safety_rules(root: Path | str = ".") -> dict[str, Any]:
    root_path = Path(root)
    candidates = [
        root_path / TRANSFER_SAFETY_RULES,
        Path(__file__).resolve().parents[2] / TRANSFER_SAFETY_RULES,
    ]
    for path in candidates:
        if path.exists():
            loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
            if not isinstance(loaded, dict):
                raise ValueError(f"transfer safety rules must be a mapping: {path}")
            return loaded
    searched = ", ".join(str(path) for path in candidates)
    raise FileNotFoundError(f"transfer safety rules not found; searched: {searched}")


def load_one_command_transfer_protocol(root: Path | str = ".") -> dict[str, Any]:
    root_path = Path(root)
    candidates = [
        root_path / ONE_COMMAND_TRANSFER_PROTOCOL,
        Path(__file__).resolve().parents[2] / ONE_COMMAND_TRANSFER_PROTOCOL,
    ]
    for path in candidates:
        if path.exists():
            loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
            if not isinstance(loaded, dict):
                raise ValueError(f"one-command transfer protocol must be a mapping: {path}")
            return loaded
    searched = ", ".join(str(path) for path in candidates)
    raise FileNotFoundError(f"one-command transfer protocol not found; searched: {searched}")


def _load_meta_command_preference(rules: dict[str, Any], protocol: dict[str, Any]) -> dict[str, Any]:
    """Load meta-command preference dynamically from authoritative YAML rule payloads."""
    safety_pref = rules.get("meta_command_preference")
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
    priority = "primary_path"
    if isinstance(safety_pref, dict):
        fallback_rule = str(safety_pref.get("fallback_rule") or "")
        priority = str(safety_pref.get("priority") or priority)
    if not fallback_rule and isinstance(protocol_pref, dict):
        fallback_rule = str(protocol_pref.get("rule") or "")

    return {
        "status": "active" if unique_commands else "missing",
        "priority": priority,
        "source": "dynamic-from-rule-files",
        "preferred_commands": unique_commands,
        "fallback_rule": fallback_rule,
        "low_level_fallback_requires_reason": True,
        "authoritative_sources": list(META_COMMAND_PREFERENCE_SOURCES),
    }



def _load_llm_work_order_contract(rules: dict[str, Any], protocol: dict[str, Any]) -> dict[str, Any]:
    """Load the LLM work-order contract dynamically from authoritative YAML rule payloads."""
    safety_contract = rules.get("llm_work_order_contract")
    protocol_contract = protocol.get("llm_work_order_contract")

    required_format = "missing"
    shell_usage = ""
    transfer_file = {}

    if isinstance(safety_contract, dict):
        required_format = str(safety_contract.get("required_format") or required_format)
        shell_usage = str(safety_contract.get("shell_usage") or shell_usage)
    if isinstance(protocol_contract, dict):
        required_format = str(protocol_contract.get("required_format") or required_format)
        raw_transfer_file = protocol_contract.get("transfer_file")
        if isinstance(raw_transfer_file, dict):
            transfer_file = raw_transfer_file

    canonical_inbox = str(transfer_file.get("canonical_inbox") or ".agentic/transfer/inbox/next_command.py.txt")
    shell_commands_allowed = bool(transfer_file.get("shell_commands_allowed", False))

    return {
        "status": "active" if required_format == "python_script" and canonical_inbox.endswith(".py.txt") and not shell_commands_allowed else "missing_or_invalid",
        "source": "dynamic-from-rule-files",
        "required_format": required_format,
        "applies_to": ["copy_paste_blocks", "transfer_file_next_command"],
        "shell_usage": shell_usage or "outer_logging_wrapper_only",
        "transfer_file": {
            "canonical_inbox": canonical_inbox,
            "shell_commands_allowed": shell_commands_allowed,
        },
        "authoritative_sources": list(LLM_WORK_ORDER_CONTRACT_SOURCES),
    }



def build_transfer_safety_header(root: Path | str = ".") -> dict[str, Any]:
    root_path = Path(root)
    rules = load_transfer_safety_rules(root_path)
    protocol = load_one_command_transfer_protocol(root_path)
    sources: list[dict[str, str]] = []
    for relative in CANONICAL_SOURCE_PATHS:
        path = root_path / relative
        if path.exists():
            sources.append({"path": relative, "sha256": _sha256(path)})
        else:
            sources.append({"path": relative, "sha256": "missing"})
    branch = _git(root_path, ["branch", "--show-current"])
    head = _git(root_path, ["rev-parse", "HEAD"])
    upstream = _git(root_path, ["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"])
    upstream_head = _git(root_path, ["rev-parse", "@{u}"]) if upstream else ""
    return {
        "schema_version": 1,
        "kind": "transfer_protocol_header",
        "derived_projection": True,
        "authoritative_sources": sources,
        "one_command_transfer_protocol": protocol,
        "meta_command_preference": _load_meta_command_preference(rules, protocol),
        "llm_work_order_contract": _load_llm_work_order_contract(rules, protocol),
        "canonical_transfer_files": rules.get("canonical_transfer_files", {
            "inbox": ".agentic/transfer/inbox/next_command.py.txt",
            "outbox": ".agentic/transfer/outbox/last_result.txt",
        }),
        "canonical_runner": rules.get("canonical_runner", {}),
        "decision_tree": rules.get("decision_tree", {}),
        "transfer_lanes": rules.get("transfer_lanes", {}),
        "transfer_priorities": rules["transfer_priorities"],
        "known_failure_classes": rules["known_failure_classes"],
        "preflight_rules": rules["preflight_rules"],
        "post_patch_rules": rules["post_patch_rules"],
        "canonical_cli_usage": rules.get("canonical_cli_usage", {}),
        "terminal_block_rules": rules.get("terminal_block_rules", {}),
        "repo_state": {
            "branch": branch,
            "head": head,
            "upstream": upstream,
            "upstream_head": upstream_head,
            "head_matches_upstream": bool(head and upstream_head and head == upstream_head),
            "dirty_status": _git(root_path, ["status", "--short"]),
        },
    }


def _without_static_meta_command_preference(value: Any) -> Any:
    """Return a JSON-safe projection without embedded meta-command policy snapshots."""
    if isinstance(value, dict):
        return {
            str(key): _without_static_meta_command_preference(nested)
            for key, nested in value.items()
            if key != "meta_command_preference"
        }
    if isinstance(value, list):
        return [_without_static_meta_command_preference(item) for item in value]
    return value


def build_local_to_llm_payload(
    root: Path | str,
    last_result: dict[str, Any],
    *,
    kind: str = "local_to_llm_last_result",
) -> dict[str, Any]:
    protocol_header = build_transfer_safety_header(root)
    payload_header = _without_static_meta_command_preference(protocol_header)
    return {
        "schema_version": 1,
        "kind": kind,
        "derived_projection": True,
        "protocol_header": payload_header,
        "safety_header": payload_header,
        "llm_execution_context": build_llm_execution_context(root),
        "last_result": last_result,
    }


def write_transfer_outbox(root: Path | str, last_result: dict[str, Any]) -> Path:
    root_path = Path(root)
    payload = build_local_to_llm_payload(root_path, last_result)
    target = root_path / OUTBOX_LAST_RESULT
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return target
def render_local_to_llm_log_header(root: Path | str = ".", *, log_path: str | None = None) -> str:
    """Render a dynamic local-to-LLM copy/paste log header from rule sources."""
    header = build_transfer_safety_header(root)
    lines = [
        "### LOCAL_TO_LLM_COPY_PASTE_LOG_HEADER",
        "### source: dynamic-from-rule-files",
    ]
    if log_path:
        lines.append(f"### log_path: {log_path}")
    lines.append(json.dumps(header, indent=2, sort_keys=True))
    lines.append("### END LOCAL_TO_LLM_COPY_PASTE_LOG_HEADER")
    return "\n".join(lines)


def describe_return_code(return_code: int) -> str:
    if return_code == 0:
        return "success / command completed"
    if return_code == 1:
        return "error / command failed; inspect the log before continuing"
    if return_code == 2:
        return "controlled block / safety gate blocked the workflow; do not continue blindly"
    return "unexpected or tool-specific exit code; inspect the log before continuing"


def render_local_to_llm_log_upload_hint(log_path: str, *, return_code: int | None = None) -> str:
    """Render the terminal hint for copy/paste communication with the LLM."""
    rc_line = ""
    if return_code is not None:
        rc_line = f"""
RC   =  {return_code}        Legend:

        - RC=0   success / command completed
        - RC=1   error / command failed; inspect the log before continuing
        - RC=2   controlled block / safety gate blocked the workflow; do not continue blindly
        - RC>2   unexpected or tool-specific exit code; inspect the log before continuing
"""
    return f"""############# ACTION REQUIRED FOR COPY-AND-PASTE COMMUNICATION #############

Please upload or copy this log file to the LLM chat:
--------------------------------------------------

LOG  =  {log_path}
{rc_line}
##########################################################################"""
