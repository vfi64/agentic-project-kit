from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import yaml

from agentic_project_kit.transfer_runner import DEFAULT_INBOX
from agentic_project_kit.transfer_remote_next import run_remote_next_transfer


def _run(argv: list[str], root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(argv, cwd=root, text=True, capture_output=True, check=False)


def _read_order_from_ref(root: Path, ref: str) -> dict[str, Any] | None:
    completed = _run(["git", "show", f"{ref}:{DEFAULT_INBOX.as_posix()}"], root)
    if completed.returncode != 0:
        return None
    loaded = yaml.safe_load(completed.stdout) or {}
    if not isinstance(loaded, dict):
        return None
    return loaded


def _is_active_order(data: dict[str, Any] | None) -> bool:
    if not isinstance(data, dict):
        return False
    return str(data.get("status") or "active").strip().lower() == "active"


def _branch_from_order(data: dict[str, Any] | None, fallback: str) -> str:
    if isinstance(data, dict):
        value = str(data.get("branch") or "").strip()
        if value:
            return value
    if fallback.startswith("origin/"):
        return fallback.removeprefix("origin/")
    return fallback


def _current_order_is_active(root: Path) -> bool:
    path = root / DEFAULT_INBOX
    if not path.exists():
        return False
    loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return _is_active_order(loaded if isinstance(loaded, dict) else None)


def _active_order_branches(root: Path) -> list[str]:
    completed = _run(
        ["git", "for-each-ref", "--format=%(refname:short)", "refs/heads", "refs/remotes/origin"],
        root,
    )
    if completed.returncode != 0:
        return []
    found: list[str] = []
    seen: set[str] = set()
    for raw in completed.stdout.splitlines():
        ref = raw.strip()
        if not ref or ref == "origin/HEAD":
            continue
        data = _read_order_from_ref(root, ref)
        if not _is_active_order(data):
            continue
        branch = _branch_from_order(data, ref)
        if branch not in seen:
            found.append(branch)
            seen.add(branch)
    return found


def run_transfer_continue(root: Path | str = ".", branch: str | None = None) -> dict[str, Any]:
    root_path = Path(root)
    steps: list[dict[str, Any]] = []

    restore = _run(["./.venv/bin/agentic-kit", "transfer", "restore-known-volatile", "--json"], root_path)
    steps.append({
        "name": "restore-known-volatile",
        "argv": ["./.venv/bin/agentic-kit", "transfer", "restore-known-volatile", "--json"],
        "returncode": restore.returncode,
        "stdout": restore.stdout,
        "stderr": restore.stderr,
        "ok": restore.returncode == 0,
    })

    inferred_branch = branch
    inference_state = "explicit_branch" if branch else "not_needed_or_not_found"
    candidates: list[str] = []

    if inferred_branch is None and not _current_order_is_active(root_path):
        candidates = _active_order_branches(root_path)
        if len(candidates) == 1:
            inferred_branch = candidates[0]
            inference_state = "single_active_order_branch"
        elif len(candidates) > 1:
            return {
                "schema_version": 1,
                "kind": "transfer_continue_result",
                "result_status": "BLOCKED",
                "returncode": 2,
                "final_signal": "f",
                "reasons": ["multiple_active_transfer_orders"],
                "candidate_branches": candidates,
                "steps": steps,
                "next_action": "Specify the intended branch or queue exactly one active transfer order.",
                "chat_reply": "f",
            }

    result = run_remote_next_transfer(root_path, inferred_branch)
    payload = result.as_json_data()
    actions = payload.get("post_report_actions") if isinstance(payload, dict) else {}
    if not isinstance(actions, dict):
        actions = {}
    local_run = payload.get("local_run") if isinstance(payload, dict) else {}
    if not isinstance(local_run, dict):
        local_run = {}

    pushed = bool(actions.get("pushed"))
    local_returncode = int(local_run.get("returncode", payload.get("returncode", 2)) or 0)
    reasons = list(payload.get("reasons", ())) if isinstance(payload.get("reasons", ()), list) else []

    passed = local_returncode == 0 and pushed
    if passed:
        status = "PASS"
        returncode = 0
        final_signal = "g"
        next_action = "Fresh remote transfer report published; successor chat must inspect it before planning."
    else:
        status = "BLOCKED"
        returncode = 2
        final_signal = "f"
        if not pushed:
            reasons.append("remote_report_not_pushed")
        next_action = payload.get("next_action") or "Inspect transfer continue blockers before retrying."

    return {
        "schema_version": 1,
        "kind": "transfer_continue_result",
        "result_status": status,
        "returncode": returncode,
        "final_signal": final_signal,
        "branch_argument": branch,
        "inferred_branch": inferred_branch,
        "inference_state": inference_state,
        "candidate_branches": candidates,
        "reasons": list(dict.fromkeys(str(r) for r in reasons)),
        "remote_next": payload,
        "steps": steps,
        "next_action": next_action,
        "chat_reply": "g" if passed else "f",
    }


def render_transfer_continue_summary(result: dict[str, Any]) -> str:
    lines = [
        "*" * 36 + " START SUMMARY " + "*" * 36,
        "TRANSFER_CONTINUE",
        "",
        f"STATE:                  {result.get('result_status')}",
        f"RETURNCODE:             {result.get('returncode')}",
        f"BRANCH_ARGUMENT:        {result.get('branch_argument') or ''}",
        f"INFERRED_BRANCH:        {result.get('inferred_branch') or ''}",
        f"INFERENCE:              {result.get('inference_state') or ''}",
    ]
    reasons = result.get("reasons") or []
    if reasons:
        lines.append(f"REASONS:                {','.join(str(r) for r in reasons)}")
    candidates = result.get("candidate_branches") or []
    if candidates:
        lines.append(f"CANDIDATES:             {','.join(str(c) for c in candidates)}")
    remote_next = result.get("remote_next") or {}
    if isinstance(remote_next, dict):
        actions = remote_next.get("post_report_actions") or {}
        lines.extend([
            "",
            "REMOTE_REPORT:",
            f"  PUSHED:               {'yes' if actions.get('pushed') else 'no'}",
            f"  COMMITTED:            {'yes' if actions.get('committed') else 'no'}",
            f"  REPORT_PATH:          {remote_next.get('published_report_path') or ''}",
        ])
    lines.extend([
        "",
        f"NEXT:                   {result.get('next_action')}",
        f"CHAT_REPLY:             {result.get('chat_reply')}",
        "*" * 37 + " END SUMMARY " + "*" * 37,
    ])
    return "\n".join(lines)
