"""Signature-bound continuation of an existing DOI PR after an API read failure."""
from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from agentic_project_kit.release_run import ReleaseRun


def original_doi_subject(run: ReleaseRun) -> dict[str, Any] | None:
    """Read legacy failure evidence without changing or discarding that evidence."""
    if run.state.get("doi_recovery"):
        return None  # A started replacement must resume its own recorded actions.
    if run.state.get("doi_resume"):
        return run.state["doi_resume"]
    path = run.step_dir / "D4.json"
    if not path.exists():
        return None
    try:
        previous = json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return None
    pending = [(previous.get("json"), 0)] if isinstance(previous, dict) else []
    while pending:
        node, depth = pending.pop()
        if depth > 24 or not isinstance(node, dict):
            continue
        # Legacy pr-complete embeds the failed readiness result as text. GH_ERROR
        # denotes a read failure; real red CI and TIMEOUT do not select this path.
        if node.get("failed_step") == "pr-wait-ci" and "GH_ERROR" in json.dumps(node):
            number, head = node.get("pr_number"), node.get("expected_head_sha")
            if isinstance(number, int) and number > 0 and isinstance(head, str) and head:
                return {"pr_number": number, "source_head": head}
        for value in node.values():
            if isinstance(value, dict):
                pending.append((value, depth + 1))
            elif isinstance(value, list):
                pending.extend((item, depth + 1) for item in value if isinstance(item, dict))
            elif isinstance(value, str) and value.lstrip().startswith("{"):
                try:
                    pending.append((json.loads(value), depth + 1))
                except ValueError:
                    continue  # Ordinary non-JSON stdout is not nested step evidence.
    return None


class DoiResume:
    def __init__(self, run: ReleaseRun) -> None:
        self.run = run

    def plan(self, gate: dict[str, Any], info: dict[str, Any], subject: dict[str, Any]) -> dict[str, Any]:
        run = self.run
        gate.update({"mode": "resume-existing", "tag": run.tag, "branch": run.doi_branch,
                     "base": "main", "source_head": info.get("headRefOid"),
                     "action": "complete the existing DOI PR with exact-head CI checks and post-merge handoff; preserve tag and packages"})
        if gate["pr_number"] != subject["pr_number"] or gate["source_head"] != subject["source_head"]:
            gate["blockers"] = ["resume-source-pr-or-head-drift"]
            return gate
        state = info.get("state")
        if state not in {"OPEN", "MERGED"}:
            gate["blockers"] = ["resume-source-pr-not-open-or-merged"]
            return gate
        head = run._command("D2R-resume-head", ["git", "rev-parse", "HEAD"])
        gate["target_commit"] = head["stdout"].strip()
        if head["result_status"] != "PASS" or not gate["target_commit"]:
            gate["blockers"] = ["resume-target-head-missing"]
            return gate
        # For a previously merged original, explicitly finish its handoff instead
        # of inferring that its entire lifecycle completed from the merge alone.
        gate["source_state"] = state
        if state == "MERGED":
            merge_sha = (info.get("mergeCommit") or {}).get("oid")
            gate["merge_commit"] = merge_sha
            if not merge_sha or not info.get("mergedAt"):
                gate["blockers"] = ["resume-merge-evidence-missing"]
                return gate
            ancestor = run._command("D2R-resume-ancestor", ["git", "merge-base", "--is-ancestor", merge_sha, gate["target_commit"]])
            if ancestor["result_status"] != "PASS":
                gate["blockers"] = ["resume-merge-not-on-current-main"]
        return gate

    def execute(self, gate: dict[str, Any]) -> dict[str, Any]:
        run = self.run
        if run._current_head() != gate["target_commit"]:
            return {"step_id": "D2R", "result_status": "BLOCKED", "blockers": ["resume-target-head-drift"]}
        check = run._command("D2R-resume-recheck", ["gh", "pr", "view", str(gate["pr_number"]),
            "--json", "headRefOid,headRefName,baseRefName,state,mergeCommit"])
        info = check.get("json")
        if not isinstance(info, dict):
            return {"step_id": "D2R", "result_status": "BLOCKED", "blockers": ["resume-source-recheck-invalid-response"]}
        if check["result_status"] != "PASS":
            return {**check, "step_id": "D2R", "result_status": "BLOCKED", "blockers": ["resume-source-recheck-unavailable"]}
        if (info.get("headRefOid") != gate["source_head"] or info.get("headRefName") != gate["branch"]
                or info.get("baseRefName") != gate["base"] or info.get("state") != gate["source_state"]
                or (gate["source_state"] == "MERGED" and (info.get("mergeCommit") or {}).get("oid") != gate["merge_commit"])):
            return {"step_id": "D2R", "result_status": "BLOCKED", "blockers": ["resume-source-drift-before-completion"]}
        run.state["doi_resume"] = {"pr_number": gate["pr_number"], "source_head": gate["source_head"]}
        run._save_state()  # Persist identity before any possible remote effect.
        if gate["source_state"] == "OPEN":
            args = ["transfer", "pr-complete", str(gate["pr_number"]), "--expected-head-sha", gate["source_head"],
                    "--timeout-seconds", "900", "--interval-seconds", "30", "--post-merge-complete", "--json"]
        else:
            args = ["transfer", "post-merge-complete", "--after-pr", str(gate["pr_number"]),
                    "--ci-timeout-seconds", "900", "--ci-poll-seconds", "30", "--json"]
        result = run._command("D2R-resume-complete", [run.executable, *args], expected_status="PASS")
        result["step_id"] = "D2R"
        if not isinstance(result.get("json"), dict) or result["json"].get("result_status") != "PASS":
            result["result_status"] = "BLOCKED"
            result["blockers"] = list(result.get("blockers") or []) + ["resume-completion-not-pass"]
        if result["result_status"] != "PASS":
            result["next_action"] = f"Inspect the preserved DOI resume log, then run agentic-kit release run --version {run.version} --json for a fresh approval."
        return result
