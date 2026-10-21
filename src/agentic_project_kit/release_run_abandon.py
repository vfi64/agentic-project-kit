"""KIT-GF-081: abandon a stopped release run after the owner's decision.

Release 1.1.4 (first attempt) stopped in B4 with an open, unmerged release PR. Nothing had been
published, but the Kit had no route to give the attempt up: the release branch had to be deleted
with `transfer branch-delete` and the run state under the tmp root moved aside by hand, a hand step
on Kit-written state.

`release abandon` plans first and executes only with the plan's signature and an attributed
consent. It refuses whenever anything may already be public: a local or remote tag, a GitHub
Release, an approval of any gate after B4, a finished publication step, or a merged release PR.
Otherwise it deletes the release branch on origin (GitHub closes its unmerged PR), checks that the
PR is closed and unmerged, deletes the local branch, and archives the run state, log and step
files under `<tmp>/release-run-archive/<version>-<state digest>/` with an `abandon.json` record,
so the next `release run` starts fresh.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
from typing import Any, Callable

from agentic_project_kit.release_run import ReleaseRun, ReleaseRunOptions, Runner, _approval_signature

KIND = "release_run_abandon_result"
GATE_KIND = "release_run_abandon_gate"
# Approving any of these gates may already have published something (tag, GitHub Release,
# package, DOI) or merged a follow-up PR; an abandon is then never safe.
PUBLISHING_GATES = ("C2", "C3", "D4", "D2R", "E1")
PUBLISHING_STEPS = ("C2", "C3", "C4", "D1", "D2", "D2R", "D3", "D4", "D5")
PR_CLOSE_CHECKS = 5


class ReleaseAbandon:
    def __init__(self, options: ReleaseRunOptions, *, runner: Runner | None = None,
                 sleep: Callable[[float], None] = time.sleep) -> None:
        self.run = ReleaseRun(options, runner=runner)
        self.options = options
        self.sleep = sleep

    # --- facts -----------------------------------------------------------------------------------

    def _git(self, *args: str) -> tuple[int, str, str]:
        completed = self.run.runner(["git", *args], self.run.root)
        return completed.returncode, completed.stdout.strip(), completed.stderr.strip()

    def _state_digest(self) -> str:
        return hashlib.sha256(self.run.state_path.read_bytes()).hexdigest()[:12]

    def plan(self) -> dict[str, Any]:
        run = self.run
        if run._plan_blockers:
            return self._result("BLOCKED", blockers=list(run._plan_blockers))
        if not run.state_path.is_file():
            return self._result("BLOCKED", blockers=["release-run-state-missing"],
                                next_action=f"There is no release run for {run.version} to abandon.")
        blockers: list[str] = []
        if run.state.get("version", run.version) != run.version:
            blockers.append("release-state-version-mismatch")
        approved = sorted({str(item.get("step_id")) for item in run.state.get("approvals") or []
                           if isinstance(item, dict) and item.get("step_id") in PUBLISHING_GATES})
        finished = [step for step in run.state.get("finished_steps") or [] if step in PUBLISHING_STEPS]
        if approved or finished:
            blockers.append("release-publication-started")
        rc, local_tag, _ = self._git("tag", "-l", run.tag)
        rc_remote, remote_tag, _ = self._git("ls-remote", "--tags", "origin", f"refs/tags/{run.tag}")
        if rc != 0 or rc_remote != 0:
            blockers.append("release-tag-check-unavailable")
        elif local_tag or remote_tag:
            blockers.append("release-already-tagged")
        release = run.runner(["gh", "api", f"repos/{{owner}}/{{repo}}/releases/tags/{run.tag}", "--jq", ".id"], run.root)
        if release.returncode == 0:
            blockers.append("release-already-published")
        elif "404" not in f"{release.stdout}\n{release.stderr}":
            blockers.append("github-release-check-unavailable")
        rc, current, _ = self._git("branch", "--show-current")
        if rc != 0:
            blockers.append("current-branch-unknown")
        elif current == run.branch:
            blockers.append("release-branch-checked-out")
        rc, dirty, _ = self._git("status", "--porcelain", "--untracked-files=no")
        if rc != 0 or dirty:
            blockers.append("worktree-not-clean")
        rc, remote_line, _ = self._git("ls-remote", "--heads", "origin", f"refs/heads/{run.branch}")
        if rc != 0:
            blockers.append("remote-branch-check-unavailable")
        remote_head = remote_line.split()[0] if remote_line else ""
        rc, local_head, _ = self._git("rev-parse", "--verify", "--quiet", f"refs/heads/{run.branch}")
        local_head = local_head if rc == 0 else ""
        pr_number, pr_blockers = self._release_pr()
        blockers.extend(pr_blockers)
        if pr_number and not remote_head:
            blockers.append("release-pr-open-without-branch")
        gate = {
            "kind": GATE_KIND,
            "gate_id": "ABANDON",
            "version": run.version,
            "tag": run.tag,
            "branch": run.branch,
            "pr_number": pr_number,
            "remote_head": remote_head,
            "local_head": local_head,
            "finished_steps": list(run.state.get("finished_steps") or []),
            "archive": self._archive_dir().relative_to(run.root).as_posix(),
            "action": "delete the release branch (closing its unmerged PR) and archive the run state",
        }
        gate["approval_signature"] = _approval_signature(gate)
        if blockers:
            return self._result("BLOCKED", gate=gate, blockers=sorted(dict.fromkeys(blockers)),
                                next_action="Resolve the blockers; an abandon never runs once anything may be published.")
        return self._result("AWAITING_APPROVAL", gate=gate, next_action=(
            f"agentic-kit release abandon --version {run.version} --execute --expected-signature "
            f"{gate['approval_signature']} --approved-by <owner> --consent-source <decision> --json"))

    def _release_pr(self) -> tuple[int | None, list[str]]:
        lookup = self.run._command("ABANDON-pr-lookup", [self.run.executable, "transfer", "pr-existing-for-branch",
                                                         "--head", self.run.branch, "--state", "all", "--json"])
        payload = lookup.get("json")
        if not isinstance(payload, dict) or payload.get("result_status") not in {"PASS", "MISS", "BLOCKED"} \
                or not isinstance(payload.get("prs"), list):
            return None, ["release-pr-lookup-unavailable"]
        if payload.get("result_status") == "BLOCKED" and "multiple_existing_prs_found" not in (payload.get("blockers") or []):
            return None, ["release-pr-lookup-unavailable"]
        prs = [item for item in payload["prs"] if isinstance(item, dict)]
        if any(str(item.get("state")).upper() == "MERGED" for item in prs):
            return None, ["release-pr-merged"]
        open_prs = [item for item in prs if str(item.get("state")).upper() == "OPEN"]
        if len(open_prs) > 1:
            return None, ["multiple-open-release-prs"]
        if not open_prs:
            return None, []
        number = open_prs[0].get("number")
        return (number, []) if isinstance(number, int) and number > 0 else (None, ["release-pr-lookup-unavailable"])

    def _archive_dir(self) -> Path:
        tmp = self.run.step_dir.parent
        return tmp / "release-run-archive" / f"{self.run.state_path.stem.removeprefix('release-run-')}-{self._state_digest()}"

    # --- execute ---------------------------------------------------------------------------------

    def execute(self) -> dict[str, Any]:
        planned = self.plan()
        if planned["result_status"] != "AWAITING_APPROVAL":
            return planned
        gate = planned["gate"]
        if self.options.expected_signature != gate["approval_signature"]:
            return self._result("BLOCKED", gate=gate, blockers=["approval-signature-mismatch"],
                                next_action="Plan again and approve the signature of the current plan.")
        if not self.options.approved_by.strip() or not self.options.consent_source.strip():
            return self._result("BLOCKED", gate=gate, blockers=["approval-attribution-missing"],
                                next_action="Name the approving owner (--approved-by) and the decision (--consent-source).")
        steps: list[dict[str, Any]] = []
        if gate["remote_head"]:
            deleted = self.run._command("ABANDON-delete-remote", [self.run.executable, "transfer", "branch-delete",
                                                                  self.run.branch, "--remote", "--json"],
                                        expected_status="PASS")
            steps.append({"step": "delete-remote-branch", "result_status": deleted["result_status"]})
            if deleted["result_status"] != "PASS":
                return self._result("BLOCKED", gate=gate, blockers=["remote-branch-delete-failed"], steps=steps,
                                    next_action=f"Inspect {self.run.log_path.as_posix()}; nothing was archived.")
        if gate["pr_number"]:
            closed = self._pr_closed(int(gate["pr_number"]))
            steps.append({"step": "release-pr-closed", "result_status": "PASS" if closed else "BLOCKED"})
            if not closed:
                return self._result("BLOCKED", gate=gate, blockers=["release-pr-still-open"], steps=steps,
                                    next_action=f"The branch is deleted but PR #{gate['pr_number']} is not closed; "
                                                "inspect it before planning the abandon again.")
        if gate["local_head"]:
            deleted = self.run._command("ABANDON-delete-local", [self.run.executable, "transfer", "branch-delete",
                                                                 self.run.branch, "--force", "--json"],
                                        expected_status="PASS")
            steps.append({"step": "delete-local-branch", "result_status": deleted["result_status"]})
            if deleted["result_status"] != "PASS":
                return self._result("BLOCKED", gate=gate, blockers=["local-branch-delete-failed"], steps=steps,
                                    next_action=f"Inspect {self.run.log_path.as_posix()}; nothing was archived.")
        archive = self._archive(gate, steps)
        steps.append({"step": "archive-run-state", "result_status": "PASS"})
        return self._result("PASS", gate=gate, steps=steps, archive=archive.relative_to(self.run.root).as_posix(),
                            next_action=f"The {self.run.version} attempt is abandoned; a new release run starts fresh.")

    def _pr_closed(self, number: int) -> bool:
        for attempt in range(PR_CLOSE_CHECKS):
            view = self.run.runner(["gh", "api", f"repos/{{owner}}/{{repo}}/pulls/{number}",
                                    "--jq", "[.state, (.merged_at // \"none\")] | @tsv"], self.run.root)
            if view.returncode == 0 and view.stdout.split() == ["closed", "none"]:
                return True
            if attempt + 1 < PR_CLOSE_CHECKS:
                self.sleep(2)
        return False

    def _archive(self, gate: dict[str, Any], steps: list[dict[str, Any]]) -> Path:
        run = self.run
        target = run.root / gate["archive"]
        target.mkdir(parents=True, exist_ok=False)
        record = {
            "schema_version": 1,
            "kind": "release_run_abandon_record",
            "abandoned_at": datetime.now(timezone.utc).isoformat(),
            "approved_by": self.options.approved_by,
            "consent_source": self.options.consent_source,
            "gate": gate,
            "steps": steps,
        }
        for source in (run.state_path, run.state_path.with_suffix(".json.pending"), run.log_path, run.step_dir):
            if source.exists():
                source.replace(target / source.name)
        (target / "abandon.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return target

    def _result(self, status: str, *, gate: dict[str, Any] | None = None, blockers: list[str] | None = None,
                steps: list[dict[str, Any]] | None = None, archive: str = "", next_action: str = "") -> dict[str, Any]:
        return {
            "schema_version": 1,
            "kind": KIND,
            "result_status": status,
            "version": self.run.version,
            "gate": gate,
            "blockers": blockers or [],
            "steps": steps or [],
            "archive": archive,
            "next_action": next_action,
        }


def abandon_release(options: ReleaseRunOptions, *, runner: Runner | None = None,
                    sleep: Callable[[float], None] = time.sleep) -> dict[str, Any]:
    abandon = ReleaseAbandon(options, runner=runner, sleep=sleep)
    return abandon.execute() if options.execute else abandon.plan()
