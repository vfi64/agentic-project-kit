"""KIT-GF-080: complete the release's own open release PR after a blocked B4.

Release 1.1.4: B4's `work finish` committed the release metadata and its handoff refresh, pushed
`codex/release-<v>` and opened the release PR, and then stopped before the merge (KIT-GF-079).
A new run met an already committed branch and blocked with `changed-paths-drift`; the release
had no route to finish its own PR.

The B4 gate turns into a resume only when the previous B4 attempt failed, exactly one open PR from
the release branch targets main, the branch holds exactly the two commits B4 writes on top of the
approved base (`Prepare release <v>` with exactly the approved paths, then `Refresh handoff for
Release <v>`), and main has not moved since that base. The resume gate names PR, head and base, so
its signature covers them; completing it runs `transfer pr-complete` with exact head checks.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from agentic_project_kit.release_run import ReleaseRun

RESUME_MODE = "resume-existing-release-pr"


def _approved_b4_base(run: "ReleaseRun") -> str:
    for approval in reversed(run.state.get("approvals") or []):
        if approval.get("step_id") == "B4":
            return str((approval.get("gate") or {}).get("target_commit") or "")
    return ""


def previous_b4_failed(run: "ReleaseRun") -> bool:
    path = run.step_dir / "B4.json"
    if not path.is_file():
        return False
    try:
        previous = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    return isinstance(previous, dict) and previous.get("returncode", 0) != 0


def plan(run: "ReleaseRun") -> dict[str, Any]:
    """{} keeps the ordinary B4; otherwise the resume fields or blockers for the gate."""
    if not previous_b4_failed(run):
        return {}
    base = _approved_b4_base(run)
    if not base:
        return {"blockers": ["release-resume-approval-missing"]}
    lookup = run._command("B4-resume-lookup", [run.executable, "transfer", "pr-existing-for-branch", "--head",
                                               run.branch, "--state", "open", "--json"])
    payload = lookup.get("json")
    if not isinstance(payload, dict):
        return {"blockers": ["release-resume-lookup-invalid-response"]}
    if lookup["returncode"] == 2 and payload.get("result_status") == "MISS":
        return {}
    number = payload.get("pr_number")
    if lookup["result_status"] != "PASS" or not isinstance(number, int) or number < 1:
        return {"blockers": ["release-resume-lookup-unavailable"]}
    view = run._command("B4-resume-view", ["gh", "pr", "view", str(number), "--json",
                                           "headRefOid,headRefName,baseRefName,state"])
    info = view.get("json")
    if view["result_status"] != "PASS" or not isinstance(info, dict):
        return {"blockers": ["release-resume-pr-view-unavailable"]}
    head = str(info.get("headRefOid") or "")
    if info.get("state") != "OPEN" or info.get("baseRefName") != "main" or info.get("headRefName") != run.branch or not head:
        return {"blockers": ["release-resume-pr-invalid"]}
    commits = run._command("B4-resume-commits", ["git", "rev-list", "--first-parent", "--reverse", f"{base}..{head}"])
    shas = commits["stdout"].split() if commits["result_status"] == "PASS" else []
    if len(shas) != 2:
        return {"blockers": ["release-resume-unexpected-commits"]}
    subjects = []
    for sha in shas:
        shown = run._command("B4-resume-subject", ["git", "log", "-1", "--format=%s", sha])
        subjects.append(shown["stdout"].strip() if shown["result_status"] == "PASS" else "")
    if subjects != [f"Prepare release {run.version}", f"Refresh handoff for Release {run.version}"]:
        return {"blockers": ["release-resume-unexpected-commits"]}
    changed = run._command("B4-resume-paths", ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", shas[0]])
    if changed["result_status"] != "PASS" or sorted(changed["stdout"].split()) != sorted(run.state.get("b_paths") or []):
        return {"blockers": ["release-resume-paths-differ"]}
    main = run._command("B4-resume-main", ["gh", "api", "repos/{owner}/{repo}/branches/main", "--jq", ".commit.sha"])
    if main["result_status"] != "PASS" or main["stdout"].strip() != base:
        return {"blockers": ["release-resume-base-moved"]}
    return {"mode": RESUME_MODE, "pr_number": number, "source_head": head, "target_commit": base,
            "action": "complete the existing release PR with exact-head CI checks and post-merge handoff"}


def complete(run: "ReleaseRun", gate: dict[str, Any]) -> dict[str, Any]:
    from agentic_project_kit.release_run import RELEASE_CI_TIMEOUT_SECONDS

    result = run._command(
        "B4-resume-complete",   # keeps B4.json, the evidence of the stopped attempt
        [run.executable, "transfer", "pr-complete", str(gate["pr_number"]), "--expected-head-sha", gate["source_head"],
         "--timeout-seconds", str(RELEASE_CI_TIMEOUT_SECONDS), "--interval-seconds", "30",
         "--post-merge-complete", "--json"],
        expected_status="PASS",
    )
    result["step_id"] = "B4"
    return result
