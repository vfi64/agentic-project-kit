"""Bounded recovery of an already requested package-index dispatch."""
from __future__ import annotations

from datetime import datetime, timezone
import time
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from agentic_project_kit.release_run import ReleaseRun


def list_runs(run: ReleaseRun, workflow: str, step_id: str) -> dict[str, Any]:
    return run._command(step_id, [
        "gh", "run", "list", "--workflow", workflow,
        "--event", "workflow_dispatch", "--limit", "100",
        "--json", "databaseId,createdAt,event,headSha",
    ])


def find_dispatched_run(run: ReleaseRun, dispatch: dict[str, Any]) -> str:
    from agentic_project_kit.release_run import _parse_github_datetime

    after = _parse_github_datetime(str(dispatch.get("dispatch_after_utc") or ""))
    sha = str(dispatch.get("head_sha") or "")
    workflow = dispatch.get("workflow") or {}
    if not after or not sha or not workflow.get("file"):
        return ""
    baseline = dispatch.get("existing_run_ids")
    # GitHub rounds creation times to seconds. A pre-dispatch inventory excludes
    # older runs in that same second. Legacy states keep the strict time cutoff.
    cutoff = after.replace(microsecond=0) if isinstance(baseline, list) else after
    for attempt in range(6):
        result = list_runs(run, workflow["file"], "C3-identify")
        payload = result.get("json")
        if result["result_status"] != "PASS" or not isinstance(payload, list):
            return ""
        matches: set[str] = set()
        for item in payload:
            if not isinstance(item, dict):
                continue
            created = _parse_github_datetime(str(item.get("createdAt") or ""))
            if (item.get("event") == "workflow_dispatch" and item.get("headSha") == sha
                    and created is not None and created >= cutoff
                    and str(item.get("databaseId")) not in (baseline or [])
                    and item.get("databaseId")):
                matches.add(str(item["databaseId"]))
        if len(matches) > 1:
            return ""
        if matches:
            return matches.pop()
        if attempt < 5:
            time.sleep(2)
    return ""


def package_index_step(run: ReleaseRun) -> dict[str, Any]:
    dispatch = dict(run.state.get("c3_dispatch") or {})
    workflow = run._package_index_workflow()
    if workflow.get("blockers"):
        return {"step_id": "C3", "result_status": "BLOCKED", "blockers": workflow["blockers"]}
    if dispatch and dispatch.get("workflow") != workflow:
        return {"step_id": "C3", "result_status": "BLOCKED", "blockers": ["package-index-workflow-drift"]}
    if not dispatch:
        head = run._current_head()
        if not head:
            return {"step_id": "C3", "result_status": "BLOCKED", "blockers": ["package-index-head-missing"]}
        before = list_runs(run, workflow["file"], "C3-before-dispatch")
        if before["result_status"] != "PASS" or not isinstance(before.get("json"), list):
            return {"step_id": "C3", "result_status": "BLOCKED", "blockers": ["package-index-dispatch-inventory-failed"]}
        # Persist intent before calling the remote API. A crash or uncertain
        # response must never turn a retry into a second dispatch.
        dispatch = {"dispatched": True, "run_id": "", "workflow": workflow,
                    "dispatch_after_utc": datetime.now(timezone.utc).isoformat(), "head_sha": head,
                    "existing_run_ids": [str(item["databaseId"]) for item in before["json"]
                                         if isinstance(item, dict) and item.get("databaseId")]}
        run.state["c3_dispatch"] = dispatch
        run._save_state()
        argv = ["gh", "workflow", "run", workflow["file"], "--ref", run.tag]
        for value in workflow["inputs"]:
            argv.extend(["-f", value])
        result = run._command("C3-dispatch", argv)
        if result["result_status"] != "PASS":
            return result
    if not dispatch.get("run_id"):
        dispatch["run_id"] = find_dispatched_run(run, dispatch)
        run.state["c3_dispatch"] = dispatch
        run._save_state()
    if not dispatch.get("run_id"):
        return {"step_id": "C3", "result_status": "BLOCKED",
                "blockers": ["package-index-dispatch-run-id-missing"],
                "next_action": f"Inspect the C3 log; rerun agentic-kit release run --version {run.version} --json to identify the existing dispatch. No redispatch occurs."}
    return run._command("C3-watch", ["gh", "run", "watch", str(dispatch["run_id"]), "--exit-status"])
