"""Bounded PR result projections with complete, local evidence."""
from __future__ import annotations

import json
import uuid
from pathlib import Path

from agentic_project_kit.workspace import load_workspace

CI_STATES = {"FAILED", "NOT_RUN", "PENDING"}


def _clip(value: object, limit: int) -> str:
    return str(value).encode("utf-8")[-limit:].decode("utf-8", errors="ignore")


def _step_ci_state(step: dict) -> str:
    output = str(step.get("stdout") or "")
    try:
        child = json.loads(output)
    except (ValueError, TypeError):
        child = {}
    if isinstance(child, dict) and child.get("ci_state") in CI_STATES:
        return child["ci_state"]
    if "wait-ci" not in str(step.get("name", "")):
        return ""
    if "PR readiness outcome: BLOCKED" in output and "- check failed:" in output:
        return "NOT_RUN" if "CI state: NOT_RUN" in output else "FAILED"
    if any(f"PR readiness outcome: {state}" in output for state in ("TIMEOUT", "WAITING")):
        return "PENDING"
    return ""


def prepare_pr_output(payload: dict, *, root: Path, summary: bool) -> tuple[dict, int]:
    data = dict(payload)
    failures = [s for s in data.get("steps", []) if s.get("returncode", 0) != 0
                or s.get("result_status", s.get("payload_status")) in {"BLOCKED", "FAIL", "PENDING"}]
    # Advisory probes and recovered predecessor failures are retained as evidence,
    # but only the wrapper's active blockers determine the terminal CI finding.
    blockers = data.get("blockers")
    failed_step = data.get("failed_step")
    if isinstance(blockers, list) and blockers:
        failures = [step for step in failures if any(
            str(blocker) == str(step.get("name")) or str(blocker).startswith(str(step.get("name")) + "_")
            for blocker in blockers)]
    elif failed_step:
        failures = [step for step in failures if step.get("name") == failed_step]
    states = [_step_ci_state(step) for step in failures]
    finding = data.get("result_status") in {"BLOCKED", "PENDING"} and bool(states) and all(states)
    if finding:
        state = "FAILED" if "FAILED" in states else ("NOT_RUN" if "NOT_RUN" in states else "PENDING")
        pr = data.get("pr_number", data.get("after_pr"))
        data.update(ci_state=state, execution_status="COMPLETED", returncode=0)
        data["next_action"] = (f"agentic-kit pr rerun-checks --pr {pr} --json" if state == "NOT_RUN" else
                               f"Repair the failed CI for PR #{pr}, then resume its Kit closeout." if state == "FAILED" else
                               f"agentic-kit pr wait-ci {pr}")
    else:
        data["execution_status"] = "COMPLETED" if data.get("result_status") == "PASS" else "BLOCKED"
    rc = 0 if finding or data.get("result_status") in {"PASS", "PENDING"} else int(data.get("returncode") or 2)
    data["returncode"] = rc
    if not summary:
        return data, rc
    try:
        tmp = load_workspace(root, suppress_legacy_profile_warning=True).tmp()
        tmp.mkdir(parents=True, exist_ok=True)
        evidence = tmp / f"pr-orchestration-{uuid.uuid4().hex}.json"
        evidence.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    except (OSError, ValueError) as exc:
        return {"result_status": "BLOCKED", "execution_status": "BLOCKED", "returncode": 2,
                "pr_number": data.get("pr_number", data.get("after_pr")),
                "next_action": "Restore writable local evidence storage before resuming closeout.",
                "blocker": str(exc)[:600]}, 2
    # Success steps keep their identity, but logs belong only in the evidence file.
    projected = {k: v for k, v in data.items() if k != "steps"}
    projected["evidence_path"] = str(evidence)
    projected["step_count"] = len(data.get("steps", []))
    projected["steps"] = [{"name": s.get("name"), "returncode": s.get("returncode", 0),
                            "result_status": s.get("result_status", s.get("payload_status", ""))}
                           for s in data.get("steps", [])]
    projected["failed_steps"] = [{"name": _clip(s.get("name"), 100), "stdout": _clip(s.get("stdout", ""), 600),
                                  "stderr": _clip(s.get("stderr", ""), 300)} for s in failures[:2]]
    # Keep output bounded even for unusually long paths, messages or step lists.
    if len(json.dumps(projected, ensure_ascii=False).encode()) > 3800:
        keep = ("schema_version", "kind", "result_status", "returncode", "ci_state", "execution_status",
                "pr_number", "after_pr", "refresh_pr", "merged_pr", "lifecycle_state", "final_signal",
                "evidence_path", "step_count", "failed_steps")
        projected = {k: projected[k] for k in keep if k in projected}
        projected["next_action"] = _clip(data.get("next_action", ""), 320)
    return projected, rc
