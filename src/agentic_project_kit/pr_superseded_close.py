"""Close an unchanged PR only after its replacement has merged."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
from typing import Callable, Sequence

Runner = Callable[[Sequence[str], Path], subprocess.CompletedProcess[str]]


def close_superseded_pr(root: Path, *, pr_number: int, replacement_pr: int, expected_head_sha: str, execute: bool, runner: Runner | None = None) -> dict:
    def default_runner(argv, cwd):
        return subprocess.run(argv, cwd=cwd, capture_output=True, text=True, check=False)

    run = runner or default_runner
    steps = []
    payload = {"result_status": "BLOCKED", "pr_number": pr_number, "replacement_pr": replacement_pr, "blockers": [], "steps": steps}
    if pr_number == replacement_pr or not expected_head_sha:
        payload["blockers"] = ["invalid-replacement-pr-or-head"]
        return payload
    views = []
    for number in (pr_number, replacement_pr):
        argv = ["gh", "pr", "view", str(number), "--json", "state,headRefOid,baseRefName"]
        completed = run(argv, root)
        steps.append({"argv": argv, "returncode": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr})
        try:
            value = json.loads(completed.stdout)
        except (TypeError, ValueError):
            value = None
        if completed.returncode != 0 or not isinstance(value, dict):
            payload["blockers"] = ["pr-verification-failed"]
            return payload
        views.append(value)
    source, replacement = views
    if source.get("headRefOid") != expected_head_sha or source.get("state") not in {"OPEN", "CLOSED"}:
        payload["blockers"] = ["superseded-pr-head-or-state-changed"]
        return payload
    if replacement.get("state") != "MERGED" or not source.get("baseRefName") or source.get("baseRefName") != replacement.get("baseRefName"):
        payload["blockers"] = ["replacement-pr-not-merged-into-same-base"]
        return payload
    if source["state"] == "CLOSED":
        payload.update(result_status="PASS", already_closed=True)
        return payload
    if not execute:
        payload["result_status"] = "PLANNED"
        return payload
    argv = ["gh", "pr", "close", str(pr_number)]
    completed = run(argv, root)
    steps.append({"argv": argv, "returncode": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr})
    payload["result_status"] = "PASS" if completed.returncode == 0 else "BLOCKED"
    if completed.returncode != 0:
        payload["blockers"] = ["pr-close-failed"]
    return payload
