from __future__ import annotations

from datetime import date
from pathlib import Path
import re
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
HANDOFF_STATE_PRESERVATION_ANCHORS = (
    "# preservation-anchor: use d for log-backed PASS and f for log-backed FAIL",
    "# preservation-anchor: nested shell/Python quote layers",
)
ADMINISTRATIVE_EVIDENCE_SUBJECT_PREFIXES = (
    "record ",
    "refresh handoff state",
    "align handoff state",
    "finalize handoff state",
    "finalize post-pr",
    "recover post-pr",
    "record final post-pr",
    "recover post-",
)

PR_REFERENCE_RE = re.compile(r"post-PR(?P<number>\d+)|after-pr(?P<after_number>\d+)", re.IGNORECASE)


def _referenced_pr_numbers(text: str) -> set[str]:
    numbers: set[str] = set()
    for match in PR_REFERENCE_RE.finditer(text):
        number = match.group("number") or match.group("after_number")
        if number:
            numbers.add(number)
    return numbers


def _validate_handoff_next_reference_consistency(data: dict[str, Any]) -> list[str]:
    first_instruction = str(data.get("first_instruction", ""))
    maintenance = data.get("handoff_maintenance", {})
    if not isinstance(maintenance, dict):
        return []
    latest_prompt = str(maintenance.get("latest_successor_prompt", ""))
    instruction_refs = _referenced_pr_numbers(first_instruction)
    prompt_refs = _referenced_pr_numbers(latest_prompt)
    if not instruction_refs or not prompt_refs:
        return []
    if instruction_refs == prompt_refs:
        return []
    return [
        "first_instruction successor prompt reference does not match "
        "handoff_maintenance.latest_successor_prompt: "
        f"first_instruction PRs={sorted(instruction_refs)}, "
        f"latest_successor_prompt PRs={sorted(prompt_refs)}"
    ]

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
    admin_state = data.get("administrative_evidence_state")
    if admin_state is not None:
        if not isinstance(admin_state, dict):
            errors.append("administrative_evidence_state must be a mapping")
        elif admin_state.get("allowed_after_safe_state") is not True:
            errors.append("administrative_evidence_state.allowed_after_safe_state must be true")
    for pattern in data.get("recent_failure_patterns", []) or []:
        if isinstance(pattern, dict) and not pattern.get("prevention"):
            pattern_id = pattern.get("id", "<unknown>")
            errors.append(f"failure pattern {pattern_id} missing prevention")
    blocked = set(data.get("blocked_until_closeout", []) or [])
    first_instruction = str(data.get("first_instruction", ""))
    for blocked_item in blocked:
        if blocked_item and blocked_item in first_instruction:
            errors.append(f"first_instruction mentions blocked work: {blocked_item}")
    errors.extend(_validate_handoff_next_reference_consistency(data))
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

def is_administrative_evidence_subject(commit_subject: str) -> bool:
    lowered = commit_subject.lower().strip()
    return lowered.startswith(ADMINISTRATIVE_EVIDENCE_SUBJECT_PREFIXES)


def is_administrative_refresh_subject(commit_subject: str) -> bool:
    return is_administrative_evidence_subject(commit_subject)


def build_administrative_evidence_state(commit: str, commit_subject: str) -> dict[str, Any]:
    return {
        "current_head": commit,
        "current_head_subject": commit_subject,
        "allowed_after_safe_state": True,
        "reason": "administrative evidence/log/handoff commit after substantive safe_state",
    }


def refresh_handoff_safe_state(
    data: dict[str, Any],
    commit: str,
    commit_subject: str,
    reason: str = "Refresh handoff state to last substantive work commit",
    updated_date: str | None = None,
) -> dict[str, Any]:
    refreshed = dict(data)
    safe_state = dict(refreshed.get("safe_state", {}))
    safe_state.setdefault("semantics", "last_substantive_work_state")
    refresh_date = updated_date or date.today().isoformat()
    if is_administrative_evidence_subject(commit_subject):
        safe_state["semantics"] = "last_substantive_work_state"
        refreshed["safe_state"] = safe_state
        refreshed["administrative_evidence_state"] = build_administrative_evidence_state(commit, commit_subject)
        refreshed["updated"] = {
            "date": refresh_date,
            "reason": "administrative handoff refresh: Current HEAD is administrative evidence; safe_state remains on last substantive work state",
            "source": "agentic-kit handoff refresh",
        }
        return refreshed
    safe_state["branch"] = "main"
    safe_state["commit"] = commit
    safe_state["commit_subject"] = commit_subject
    refreshed["safe_state"] = safe_state
    refreshed.pop("administrative_evidence_state", None)
    refreshed["updated"] = {
        "date": refresh_date,
        "reason": reason,
        "source": "agentic-kit handoff refresh",
    }
    return refreshed

def save_handoff_state(data: dict[str, Any], path: str | Path = DEFAULT_HANDOFF_STATE_PATH) -> None:
    state_path = Path(path)
    text = yaml.safe_dump(data, sort_keys=False, allow_unicode=True)
    missing_anchors = [anchor for anchor in HANDOFF_STATE_PRESERVATION_ANCHORS if anchor not in text]
    if missing_anchors:
        text = text.rstrip() + "\n" + "\n".join(missing_anchors) + "\n"
    state_path.write_text(text, encoding="utf-8")
