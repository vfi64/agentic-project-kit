from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

DEFAULT_HANDOFF_STATE_PATH = Path(".agentic/handoff_state.yaml")
REQUIRED_TOP_LEVEL_FIELDS = [
    "schema_version",
    "updated",
    "repo",
    "safe_state",
    "release",
    "open_items",
    "completed_since_previous_handoff",
    "current_capabilities",
    "rules",
    "recent_failure_patterns",
    "next_allowed_tasks",
    "blocked_until_closeout",
    "first_instruction",
    "handoff_maintenance",
]
VALID_RULE_STATUSES = {"active", "superseded", "historical"}

def load_handoff_state(path: str | Path = DEFAULT_HANDOFF_STATE_PATH) -> dict[str, Any]:
    state_path = Path(path)
    if not state_path.exists():
        raise FileNotFoundError(f"handoff state file not found: {state_path}")
    data = yaml.safe_load(state_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("handoff state must be a YAML mapping")
    return data

def _is_empty(value: Any) -> bool:
    return value is None or value == "" or value == [] or value == {}

def validate_handoff_state(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in REQUIRED_TOP_LEVEL_FIELDS:
        if field not in data:
            errors.append(f"missing required field: {field}")
        elif _is_empty(data[field]) and field not in {"open_items", "blocked_until_closeout"}:
            errors.append(f"empty required field: {field}")
    rules = data.get("rules", [])
    if not isinstance(rules, list):
        errors.append("rules must be a list")
        rules = []
    active_ids: set[str] = set()
    for index, rule in enumerate(rules):
        if not isinstance(rule, dict):
            errors.append(f"rule {index} must be a mapping")
            continue
        rule_id = rule.get("id")
        status = rule.get("status")
        text = rule.get("text")
        if not rule_id:
            errors.append(f"rule {index} missing id")
        if status not in VALID_RULE_STATUSES:
            errors.append(f"rule {rule_id or index} has invalid status: {status}")
        if not text:
            errors.append(f"rule {rule_id or index} missing text")
        if status == "active" and rule_id:
            if rule_id in active_ids:
                errors.append(f"duplicate active rule id: {rule_id}")
            active_ids.add(rule_id)
        if status == "superseded" and not (rule.get("superseded_by") or rule.get("reason")):
            errors.append(f"superseded rule {rule_id or index} needs superseded_by or reason")
    for pattern in data.get("recent_failure_patterns", []) or []:
        if isinstance(pattern, dict) and not pattern.get("prevention"):
            pattern_id = pattern.get("id", "<unknown>")
            errors.append(f"failure pattern {pattern_id} missing prevention")
    blocked = set(data.get("blocked_until_closeout", []) or [])
    first_instruction = str(data.get("first_instruction", ""))
    for blocked_item in blocked:
        if blocked_item and blocked_item in first_instruction:
            errors.append(f"first_instruction mentions blocked work: {blocked_item}")
    return errors

def active_rules(data: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        rule
        for rule in data.get("rules", [])
        if isinstance(rule, dict) and rule.get("status") == "active"
    ]

def summarize_handoff_state(data: dict[str, Any]) -> str:
    repo = data.get("repo", {})
    release = data.get("release", {})
    safe_state = data.get("safe_state", {})
    lines = [
        f"Repo: {repo.get('name', '<unknown>')}",
        f"Path: {repo.get('local_path', '<unknown>')}",
        f"Remote: {repo.get('remote', '<unknown>')}",
        f"Version: {release.get('current_version', '<unknown>')}",
        f"Safe state: {safe_state.get('branch', '<unknown>')} @ {safe_state.get('commit', '<unknown>')}",
        f"Next: {data.get('first_instruction', '<none>')}",
    ]
    return "\n".join(lines)
