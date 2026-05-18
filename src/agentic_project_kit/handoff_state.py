from __future__ import annotations

from pathlib import Path
import subprocess
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
VALID_SAFE_STATE_SEMANTICS = {"last_substantive_work_state", "current_main_head"}

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
    safe_state = data.get("safe_state", {})
    if isinstance(safe_state, dict):
        semantics = safe_state.get("semantics", "last_substantive_work_state")
        if semantics not in VALID_SAFE_STATE_SEMANTICS:
            errors.append(f"safe_state.semantics must be one of: {sorted(VALID_SAFE_STATE_SEMANTICS)}")
        refresh_prs = safe_state.get("administrative_refresh_prs", [])
        if refresh_prs is None:
            refresh_prs = []
        if not isinstance(refresh_prs, list):
            errors.append("safe_state.administrative_refresh_prs must be a list when present")
        else:
            for pr in refresh_prs:
                if not isinstance(pr, int):
                    errors.append("safe_state.administrative_refresh_prs entries must be integers")
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


def current_git_safe_state() -> dict[str, str]:
    commit = subprocess.check_output([
        "git",
        "rev-parse",
        "--short",
        "HEAD",
    ], text=True).strip()
    subject = subprocess.check_output([
        "git",
        "log",
        "-1",
        "--pretty=%s",
    ], text=True).strip()
    return {"commit": commit, "commit_subject": subject}

def is_administrative_refresh_subject(commit_subject: str) -> bool:
    return commit_subject.lower().startswith("refresh handoff state")


def refresh_handoff_safe_state(
    data: dict[str, Any],
    commit: str,
    commit_subject: str,
    reason: str = "Refresh handoff state to last substantive work commit",
) -> dict[str, Any]:
    refreshed = dict(data)
    safe_state = dict(refreshed.get("safe_state", {}))
    safe_state.setdefault("semantics", "last_substantive_work_state")
    if is_administrative_refresh_subject(commit_subject):
        refreshed["safe_state"] = safe_state
        refreshed["updated"] = {
            "date": "2026-05-18",
            "reason": "Current HEAD is an administrative handoff refresh; safe_state remains on last substantive work commit",
            "source": "agentic-kit handoff refresh",
        }
        return refreshed
    safe_state["branch"] = "main"
    safe_state["commit"] = commit
    safe_state["commit_subject"] = commit_subject
    refreshed["safe_state"] = safe_state
    refreshed["updated"] = {
        "date": "2026-05-18",
        "reason": reason,
        "source": "agentic-kit handoff refresh",
    }
    return refreshed

def save_handoff_state(data: dict[str, Any], path: str | Path = DEFAULT_HANDOFF_STATE_PATH) -> None:
    state_path = Path(path)
    state_path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")
