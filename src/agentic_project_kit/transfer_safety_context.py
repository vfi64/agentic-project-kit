from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

import yaml

TRANSFER_SAFETY_RULES = Path(".agentic/transfer_safety_rules.yaml")
ONE_COMMAND_TRANSFER_PROTOCOL = Path(".agentic/transfer/one_command_transfer_protocol.yaml")
OUTBOX_LAST_RESULT = Path(".agentic/transfer/outbox/last_result.txt")
CANONICAL_SOURCE_PATHS = (
    ".agentic/transfer_safety_rules.yaml",
    ".agentic/transfer/one_command_transfer_protocol.yaml",
    ".agentic/rule_mechanism_inventory.yaml",
    ".agentic/rule_preservation.yaml",
    "docs/planning/RULE_REFRESH_HANDSHAKE_PLAN.md",
    "docs/planning/WORKFLOW_REDUCTION_FOCUS.md",
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
        "canonical_transfer_files": rules["canonical_transfer_files"],
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


def build_local_to_llm_payload(
    root: Path | str,
    last_result: dict[str, Any],
    *,
    kind: str = "local_to_llm_last_result",
) -> dict[str, Any]:
    protocol_header = build_transfer_safety_header(root)
    return {
        "schema_version": 1,
        "kind": kind,
        "derived_projection": True,
        "protocol_header": protocol_header,
        "safety_header": protocol_header,
        "last_result": last_result,
    }


def write_transfer_outbox(root: Path | str, last_result: dict[str, Any]) -> Path:
    root_path = Path(root)
    payload = build_local_to_llm_payload(root_path, last_result)
    target = root_path / OUTBOX_LAST_RESULT
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return target
