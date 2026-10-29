"""Rebase orchestration and bounded conflict-observation handling."""
from __future__ import annotations

from agentic_project_kit.git_tag_sync import run_with_tag_sync

import json
from pathlib import Path
from typing import Any

from agentic_project_kit.cli_executable import default_agentic_kit


def _conflict_present(payload: object, returncode: int) -> bool | None:
    if not isinstance(payload, dict):
        return None
    # conflict-status emits its observation under repo. Accept the legacy flat
    # shape as well, but never turn missing or failed observations into "no".
    repo = payload.get("repo", payload)
    if not isinstance(repo, dict):
        return None
    if payload.get("result_status") == "CONFLICT" or any(
        repo.get(key) for key in ("unmerged_files", "rebase_apply", "rebase_merge", "merge_head")
    ) or repo.get("conflict_present") is True:
        return True
    commands = payload.get("commands", {})
    if not isinstance(commands, dict) or any(
        not isinstance(command, dict) or command.get("returncode") != 0
        for command in commands.values()
    ):
        return None
    if returncode == 0 and repo.get("conflict_present") is False:
        return False
    return None


def rebase_on_upstream(*, upstream: str = "", expected_branch: str = "") -> dict[str, Any]:
    steps: list[dict[str, Any]] = []
    blockers: list[str] = []

    def run_step(name: str, argv: list[str]) -> dict[str, Any]:
        completed = run_with_tag_sync(argv, text=True, capture_output=True)
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
        fetch = run_step("fetch-origin", ["git", "fetch", "origin", current_branch])
        if fetch["returncode"] != 0 and "TAG_SYNC_BLOCKED" not in str(fetch["stderr"]) + str(fetch["stdout"]):
            fetch = run_step("fetch-origin-main", ["git", "fetch", "origin", "main"])
        if fetch["returncode"] != 0:
            blockers.append("fetch_failed")
    if not blockers:
        rebased = run_step("rebase", ["git", "rebase", target_upstream])
        if rebased["returncode"] != 0:
            blockers.append("rebase_failed")

    observed = run_step(
        "conflict-status",
        [default_agentic_kit(Path.cwd()), "transfer", "conflict-status", "--json"],
    )
    try:
        conflict_payload = json.loads(str(observed["stdout"]) or "{}")
    except json.JSONDecodeError:
        conflict_payload = {"parse_error": "conflict-status output was not valid JSON"}
    conflict_present = _conflict_present(conflict_payload, int(observed["returncode"]))
    if conflict_present is True:
        blockers.append("conflict_detected")
    elif conflict_present is None:
        blockers.append("conflict_status_unavailable")

    result_status = "PASS" if not blockers else "BLOCKED"
    return {
        "schema_version": 1,
        "kind": "transfer_rebase_on_upstream_result",
        "action": "rebase-on-upstream",
        "result_status": result_status,
        "final_signal": "d" if result_status == "PASS" else "f",
        "branch": current_branch,
        "upstream": target_upstream,
        "blockers": blockers,
        "conflict_present": conflict_present,
        "conflict_status": conflict_payload,
        "steps": steps,
        "next_action": (
            "Rebase completed and no merge/rebase conflict is present."
            if result_status == "PASS"
            else "Inspect rebase/conflict state before continuing: " + ", ".join(blockers)
        ),
    }
