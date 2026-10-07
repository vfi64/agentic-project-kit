"""Signature-bound replacement of a failed DOI PR using existing Kit routes."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from agentic_project_kit.dpa_current_handoff_lifecycle import DEFAULT_ACCEPTANCE_STATE_PATH
from agentic_project_kit.post_release_closeout import doi_closeout_evidence_relative_path

if TYPE_CHECKING:
    from agentic_project_kit.release_run import ReleaseRun


class DoiRecovery:
    def __init__(self, run: ReleaseRun) -> None:
        self.run = run
        self.branch = run.doi_branch + "-recovery"

    def _command(self, name: str, args: list[str], *, kit: bool = True, status: str | None = "PASS") -> dict[str, Any]:
        argv = [self.run.executable, *args] if kit else args
        return self.run._command("D2R-" + name, argv, expected_status=status)

    def plan(self) -> dict[str, Any]:
        run = self.run
        progress = run.state.get("doi_recovery") or {}
        gate: dict[str, Any] = {
            "kind": "release_run_gate", "gate_id": "D2R", "version": run.version,
            "action": "regenerate DOI closeout on a replacement branch, merge it with handoff refresh, then close the superseded PR",
            "source_branch": run.doi_branch, "branch": self.branch,
            "finished_actions": list(progress.get("finished_actions") or []),
        }
        branch_result = self._command("branch", ["git", "branch", "--show-current"], kit=False, status=None)
        current_branch = branch_result["stdout"].strip()
        if branch_result["result_status"] != "PASS" or current_branch not in {"main", self.branch}:
            gate["blockers"] = ["recovery-requires-main-or-recovery-branch"]
            return gate
        status = self._command("status", ["git", "status", "--porcelain"], kit=False, status=None)
        if status["result_status"] != "PASS" or (status["stdout"].strip() and not progress):
            gate["blockers"] = ["recovery-requires-clean-start"]
            return gate
        if status["stdout"].strip() and "commit" in gate["finished_actions"]:
            gate["blockers"] = ["recovery-dirty-after-commit"]
            return gate
        lookup = self._command("source-pr", ["transfer", "pr-existing-for-branch", "--head", run.doi_branch, "--state", "all", "--json"])
        missing_pr = lookup["returncode"] == 2 and (lookup.get("json") or {}).get("result_status") == "MISS"
        if lookup["result_status"] != "PASS" and not missing_pr:
            gate["blockers"] = ["recovery-source-pr-not-unique"]
            return gate
        gate["pr_number"] = (lookup["json"] or {}).get("pr_number")
        if missing_pr:
            source = self._command("source-branch", ["git", "rev-parse", "--verify", f"refs/heads/{run.doi_branch}"], kit=False, status=None)
            info = {"headRefOid": source["stdout"].strip(), "headRefName": run.doi_branch, "baseRefName": "main", "state": "OPEN"}
        elif not isinstance(gate["pr_number"], int):
            gate["blockers"] = ["recovery-source-pr-number-missing"]
            return gate
        else:
            source = self._command("source-head", ["gh", "pr", "view", str(gate["pr_number"]), "--json", "headRefOid,headRefName,baseRefName,state"], kit=False, status=None)
            info = source.get("json") or {}
        if source["result_status"] != "PASS" or info.get("headRefName") != run.doi_branch or info.get("baseRefName") != "main" or info.get("state") not in {"OPEN", "CLOSED"} or not info.get("headRefOid"):
            gate["blockers"] = ["recovery-source-pr-invalid"]
            return gate
        if info.get("state") == "CLOSED" and not progress:
            gate["blockers"] = ["recovery-source-pr-already-closed"]
            return gate
        gate["source_head"] = info["headRefOid"]
        if progress and gate["source_head"] != progress["source_head"]:
            gate["blockers"] = ["recovery-source-head-drift"]
            return gate
        head = self._command("head", ["git", "rev-parse", "HEAD"], kit=False, status=None)
        if head["result_status"] != "PASS" or not head["stdout"].strip():
            gate["blockers"] = ["recovery-target-head-missing"]
            return gate
        gate["target_commit"] = head["stdout"].strip()
        if progress:
            for key in ("paths", "write_scope", "version_doi", "concept_doi"):
                gate[key] = progress[key]
            gate["replacement_pr"] = progress.get("replacement_pr")
        else:
            exists = self._command("replacement-exists", ["git", "show-ref", "--verify", "--quiet", f"refs/heads/{self.branch}"], kit=False, status=None)
            if exists["returncode"] != 1:
                gate["blockers"] = ["recovery-replacement-branch-already-exists"]
                return gate
            remote = self._command("replacement-remote", ["git", "ls-remote", "--heads", "origin", f"refs/heads/{self.branch}"], kit=False, status=None)
            if remote["result_status"] != "PASS" or remote["stdout"].strip():
                gate["blockers"] = ["recovery-replacement-remote-not-empty"]
                return gate
            preview = self._command("preview", ["post-release-doi-closeout", "--version", run.version, "--json"])
            if preview["result_status"] != "PASS":
                gate["blockers"] = ["recovery-closeout-preview-blocked"]
                return gate
            payload = preview["json"] or {}
            gate["paths"] = sorted(payload.get("changed_paths") or [])
            gate["write_scope"] = sorted(set(payload.get("expected_paths") or []) | {
                str(DEFAULT_ACCEPTANCE_STATE_PATH), doi_closeout_evidence_relative_path(run.version),
            })
            gate["version_doi"] = payload.get("version_doi", "")
            gate["concept_doi"] = payload.get("concept_doi", "")
            if not gate["paths"] or not gate["version_doi"] or not gate["concept_doi"]:
                gate["blockers"] = ["recovery-preview-has-no-verified-repair"]
        return gate

    def execute(self, gate: dict[str, Any]) -> dict[str, Any]:
        run = self.run
        progress = run.state.setdefault("doi_recovery", {**gate, "finished_actions": []})
        done = progress["finished_actions"]

        def step(name: str, args: list[str]) -> dict[str, Any] | None:
            if name in done:
                return None
            result = self._command(name, args)
            if result["result_status"] != "PASS":
                result["step_id"] = "D2R"
                result["next_action"] = f"Inspect the D2R log, then run agentic-kit release run --version {run.version} --json for a fresh recovery approval."
                return result
            if name == "finish":
                number = (result["json"] or {}).get("pr_number")
                if not isinstance(number, int):
                    return {"step_id": "D2R", "result_status": "BLOCKED", "blockers": ["replacement-pr-number-missing"]}
                progress["replacement_pr"] = number
            done.append(name)
            run._save_state()
            return None

        result = step("start", ["work", "start", "--branch", self.branch, "--from-ref", "main", "--json"])
        if result:
            return result
        result = step("write", ["post-release-doi-closeout", "--version", run.version, "--write", "--json"])
        if result:
            return result
        if "commit" not in done:
            paths = run._changed_paths()
            scope = gate["write_scope"]
            if not paths or any(not any(path == allowed or (allowed.endswith("/") and path.startswith(allowed)) for allowed in scope) for path in paths):
                return {"step_id": "D2R", "result_status": "BLOCKED", "blockers": ["recovery-changed-paths-outside-approved-scope"]}
            progress["commit_paths"] = paths
            run._save_state()
            # Acknowledgement must immediately precede the governed commit.
            ack = self._command("acknowledge", ["rules", "acknowledge", "--json"], status=None)
            if ack["result_status"] != "PASS" or not isinstance(ack.get("json"), dict) or ack["json"].get("written") is not True:
                return {**ack, "step_id": "D2R", "result_status": "BLOCKED", "blockers": ["rule-acknowledgement-not-written"]}
            args = ["transfer", "commit", "--branch", self.branch, "--message", f"Fix DOI closeout for release {run.version}"]
            for path in paths:
                args.extend(["--path", path])
            result = step("commit", [*args, "--json"])
            if result:
                return result
        for name, args in (
            ("push", ["transfer", "push-current", "--json"]),
            ("finish", ["transfer", "pr-create-complete", "--title", f"Fix DOI closeout for release {run.version}", "--body", "Regenerate verified DOI facts through Kit closeout.\n\nrelease-note-category: Fixed", "--head", self.branch, "--base", "main", "--timeout-seconds", "900", "--post-merge-complete", "--json"]),
        ):
            result = step(name, args)
            if result:
                return result
        if gate["pr_number"] is not None:
            result = step("close-source", ["transfer", "pr-close-superseded", str(gate["pr_number"]), "--replacement-pr", str(progress["replacement_pr"]), "--expected-head-sha", gate["source_head"], "--execute", "--json"])
            if result:
                return result
        return {"step_id": "D2R", "result_status": "PASS", "next_action": "Replacement DOI PR and handoff merged; superseded PR closed."}
