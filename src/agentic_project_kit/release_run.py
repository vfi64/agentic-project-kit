from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import time
from typing import Any

import yaml

from agentic_project_kit.cli_executable import default_agentic_kit
from agentic_project_kit.publication_policy import publication_policy_for
from agentic_project_kit.release_run_policy import release_branch_plan, release_step_sequence
from agentic_project_kit.workspace import load_workspace


Runner = Callable[[Sequence[str], Path], subprocess.CompletedProcess[str]]


GATE_SEQUENCE = ("B4", "C2", "C3", "D4", "D2R")


@dataclass(frozen=True)
class ReleaseRunOptions:
    version: str
    summary_lines: tuple[str, ...] = ()
    execute: bool = False
    expected_signature: str = ""
    json_output: bool = False
    approved_by: str = ""
    consent_source: str = ""
    root: Path = Path(".")


def default_runner(argv: Sequence[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(list(argv), cwd=cwd, text=True, capture_output=True, check=False)


class ReleaseRun:
    def __init__(self, options: ReleaseRunOptions, *, runner: Runner | None = None) -> None:
        self.options = options
        self.root = options.root.resolve()
        self.runner = runner or default_runner
        self.version = options.version.removeprefix("v")
        self.tag = f"v{self.version}"
        workspace = load_workspace(self.root, suppress_legacy_profile_warning=True)
        self.policy = publication_policy_for(self.root)
        self.sequence = release_step_sequence(self.policy)
        self.branch, self.doi_branch, self._plan_blockers = release_branch_plan(self.version, self._release_config())
        safe_version = re.sub(r"[^A-Za-z0-9_.-]+", "-", self.version)
        self.state_path = workspace.tmp_file(f"release-run-{safe_version}.json")
        self.log_path = workspace.tmp_file(f"release-run-{safe_version}.log")
        self.step_dir = workspace.tmp() / f"release-run-{safe_version}-steps"
        self.executable = default_agentic_kit(self.root)
        self.state = self._load_state()
        self._approval_consumed = False

    def run(self) -> dict[str, Any]:
        from agentic_project_kit.release_run_approval import validate_consent

        blockers = [*self._plan_blockers, *validate_consent(self)]
        if blockers:
            return self._payload({"step_id": "approval-policy", "result_status": "BLOCKED", "blockers": blockers})
        self.state.setdefault("schema_version", 1)
        self.state.setdefault("kind", "release_run_state")
        self.state.setdefault("version", self.version)
        self.state.setdefault("summary_lines", list(self.options.summary_lines))
        self.state.setdefault("finished_steps", [])
        self.state.setdefault("step_results", {})
        self.state.setdefault("gates", {})
        self.state.setdefault("publication_policy", publication_policy_for(self.root).value)
        self.state.setdefault("release_branch", self.branch)
        self._save_state()

        for step_id in self.sequence:
            if self._is_finished(step_id):
                continue
            result = self._run_or_gate(step_id)
            if result["result_status"] != "PASS":
                return self._payload(result)
            self._mark_finished(step_id, result)
        return self._payload({"step_id": "complete", "result_status": "PASS", "next_action": "Release run completed."})

    def _run_or_gate(self, step_id: str) -> dict[str, Any]:
        if step_id not in self.sequence and not (step_id == "D2R" and "D4" in self.sequence):
            return {"step_id": step_id, "result_status": "BLOCKED",
                    "blockers": ["step-not-declared-by-publication-policy"]}
        if step_id == "D4" and self._doi_recovery_required():
            step_id = "D2R"
        if step_id in GATE_SEQUENCE:
            gate = self._gate_details(step_id)
            blockers = list(gate.get("blockers") or [])
            if step_id == "C3" and isinstance(gate.get("workflow"), dict):
                blockers.extend(gate["workflow"].get("blockers") or [])
            if blockers:
                return {
                    "step_id": step_id,
                    "result_status": "BLOCKED",
                    "blockers": blockers,
                    "gate": gate,
                    "next_action": "Configure the release-run gate inputs before approving this step.",
                }
            from agentic_project_kit.release_run_approval import authorize_gate

            decision = authorize_gate(self, step_id, gate)
            if decision is not None:
                return decision
        method = getattr(self, f"_step_{step_id.lower()}")
        return method()

    def _step_a1(self) -> dict[str, Any]:
        return self._command("A1", [self.executable, "transfer", "sync-main"])

    def _step_a2(self) -> dict[str, Any]:
        return self._command("A2", [self.executable, "release", "ready", "--version", self.version, *self._summary_args(), "--json"], expected_status="PASS")

    def _step_a3(self) -> dict[str, Any]:
        return self._command("A3", [self.executable, "release", "prepare", "--version", self.version, *self._summary_args(), "--json"], expected_status="PASS")

    def _step_b1(self) -> dict[str, Any]:
        return self._command("B1", [self.executable, "work", "start", "--branch", self.branch, "--json"], expected_status="PASS")

    def _step_b2(self) -> dict[str, Any]:
        return self._command("B2", [self.executable, "release", "prepare", "--version", self.version, "--write", *self._summary_args(), "--json"], expected_status="PASS")

    def _step_b3(self) -> dict[str, Any]:
        paths = self._changed_paths()
        self.state["b_paths"] = paths
        self._save_state()
        return self._work_finish("B3", branch=self.branch, paths=paths, execute=False, expected_status="PLANNED")

    def _step_b4(self) -> dict[str, Any]:
        expected = tuple(self.state.get("b_paths") or [])
        current = tuple(self._changed_paths())
        if current != expected:
            return {
                "step_id": "B4",
                "result_status": "BLOCKED",
                "blockers": ["changed-paths-drift"],
                "expected_paths": list(expected),
                "current_paths": list(current),
                "next_action": "Rerun release run without --execute to refresh the B4 approval gate.",
            }
        return self._work_finish("B4", branch=self.branch, paths=list(expected), execute=True, expected_status="PASS")

    def _step_c1(self) -> dict[str, Any]:
        result = self._command(
            "C1",
            [self.executable, "release-publish", "--version", self.version, "--dry-run", "--json"],
            release_publish=True,
        )
        signature = str((result.get("json") or {}).get("approval_signature") or "")
        self.state["c1_release_publish_signature"] = signature
        self._save_state()
        return result

    def _step_c2(self) -> dict[str, Any]:
        release_signature = str(self.state.get("c1_release_publish_signature") or "")
        return self._command(
            "C2",
            [
                self.executable,
                "release-publish",
                "--version",
                self.version,
                "--execute",
                "--allow-execute",
                "--expected-signature",
                release_signature,
                "--json",
            ],
            release_publish=True,
        )

    def _step_c3(self) -> dict[str, Any]:
        from agentic_project_kit.release_run_dispatch import package_index_step

        return package_index_step(self)

    def _step_c4(self) -> dict[str, Any]:
        last: dict[str, Any] | None = None
        attempts = 3 if self.policy.uses_zenodo else 1
        for attempt in range(attempts):
            last = self._command("C4", [self.executable, "post-release-check", "--version", self.version, "--json"], expected_status="PASS")
            if last["result_status"] == "PASS":
                return last
            if attempt + 1 < attempts:
                time.sleep(1)
        return last or {"step_id": "C4", "result_status": "BLOCKED", "blockers": ["post-release-check-not-run"]}

    def _step_d1(self) -> dict[str, Any]:
        return self._command("D1", [self.executable, "work", "start", "--branch", self.doi_branch, "--json"], expected_status="PASS")

    def _step_d2(self) -> dict[str, Any]:
        return self._command("D2", [self.executable, "post-release-doi-closeout", "--version", self.version, "--write", "--json"], expected_status="PASS")

    def _step_d3(self) -> dict[str, Any]:
        paths = self._changed_paths()
        self.state["d_paths"] = paths
        self._save_state()
        return self._work_finish("D3", branch=self.doi_branch, paths=paths, execute=False, expected_status="PLANNED")

    def _step_d4(self) -> dict[str, Any]:
        expected = tuple(self.state.get("d_paths") or [])
        current = tuple(self._changed_paths())
        if current != expected:
            return {
                "step_id": "D4",
                "result_status": "BLOCKED",
                "blockers": ["changed-paths-drift"],
                "expected_paths": list(expected),
                "current_paths": list(current),
                "next_action": "Rerun release run without --execute to refresh the D4 approval gate.",
            }
        result = self._work_finish("D4", branch=self.doi_branch, paths=list(expected), execute=True, expected_status="PASS")
        if result["result_status"] == "BLOCKED":
            self.state["doi_recovery_required"] = True
            self._save_state()
        return result

    def _doi_recovery_required(self) -> bool:
        if self.state.get("doi_recovery_required"):
            return True
        # Older runners did not persist failed step status in the state file.
        path = self.step_dir / "D4.json"
        if not path.exists():
            return False
        previous = _parse_json(path.read_text(encoding="utf-8"))
        return isinstance(previous, dict) and (
            previous.get("returncode", 0) != 0
            or (previous.get("json") or {}).get("result_status") == "BLOCKED"
        )

    def _step_d2r(self) -> dict[str, Any]:
        from agentic_project_kit.release_run_recovery import DoiRecovery

        result = DoiRecovery(self).execute(self.state["gates"]["D2R"])
        if result["result_status"] == "PASS":
            self._mark_finished("D2R", result)
        return result

    def _step_d5(self) -> dict[str, Any]:
        result = self._command("D5", [self.executable, "release-status", "--version", self.version, "--include-remote", "--json"], expected_status="PASS")
        current_state = str((result.get("json") or {}).get("current_state") or "")
        if result["result_status"] == "PASS" and current_state != "current_verified":
            return {
                "step_id": "D5",
                "result_status": "BLOCKED",
                "blockers": ["release-status-not-current-verified"],
                "current_state": current_state,
            }
        return result

    def _work_finish(self, step_id: str, *, branch: str, paths: list[str], execute: bool, expected_status: str) -> dict[str, Any]:
        argv = [
            self.executable,
            "work",
            "finish",
            "--branch",
            branch,
            "--title",
            f"Release {self.version}" if branch == self.branch else f"Record DOI for release {self.version}",
            "--message",
            f"Prepare release {self.version}" if branch == self.branch else f"Record DOI for release {self.version}",
        ]
        for path in paths:
            argv.extend(["--path", path])
        argv.extend(["--execute" if execute else "--dry-run", "--json"])
        return self._command(step_id, argv, expected_status=expected_status)

    def _command(
        self,
        step_id: str,
        argv: list[str],
        *,
        expected_status: str | None = None,
        release_publish: bool = False,
    ) -> dict[str, Any]:
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self.step_dir.mkdir(parents=True, exist_ok=True)
        started = time.monotonic()
        completed = self.runner(argv, self.root)
        duration = time.monotonic() - started
        parsed = _parse_json(completed.stdout)
        step_payload = {
            "step_id": step_id,
            "argv": argv,
            "returncode": completed.returncode,
            "duration_seconds": round(duration, 3),
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "json": parsed,
        }
        self._append_log(step_payload)
        (self.step_dir / f"{step_id}.json").write_text(json.dumps(step_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        blockers: list[str] = []
        if completed.returncode != 0:
            blockers.append("returncode")
        if release_publish:
            if not _release_publish_ok(parsed):
                blockers.append("release-publish")
        elif expected_status is not None and not _status_matches(parsed, expected_status):
            blockers.append("result-status")
        result_status = "PASS" if not blockers else "BLOCKED"
        step_payload["result_status"] = result_status
        step_payload["blockers"] = blockers
        if result_status != "PASS":
            step_payload["next_action"] = f"Inspect {self.log_path.as_posix()} and fix step {step_id}."
        return step_payload

    def _changed_paths(self) -> list[str]:
        completed = self.runner(["git", "status", "--porcelain"], self.root)
        self._append_log(
            {
                "step_id": "changed-paths",
                "argv": ["git", "status", "--porcelain"],
                "returncode": completed.returncode,
                "duration_seconds": 0,
                "stdout": completed.stdout,
                "stderr": completed.stderr,
            }
        )
        if completed.returncode != 0:
            return []
        paths: list[str] = []
        for line in completed.stdout.splitlines():
            if not line.strip():
                continue
            paths.append(line[3:].strip())
        return sorted(dict.fromkeys(paths))

    def _gate_details(self, gate_id: str) -> dict[str, Any]:
        if gate_id == "D2R":
            from agentic_project_kit.release_run_recovery import DoiRecovery

            return DoiRecovery(self).plan()
        target_commit = self._current_head()
        if gate_id == "B4":
            return {
                "kind": "release_run_gate",
                "gate_id": gate_id,
                "version": self.version,
                "action": "execute work finish for release metadata branch",
                "tag": self.tag,
                "branch": self.branch,
                "paths": list(self.state.get("b_paths") or []),
                "target_commit": target_commit,
            }
        if gate_id == "C2":
            return {
                "kind": "release_run_gate",
                "gate_id": gate_id,
                "version": self.version,
                "action": "execute signed release-publish",
                "tag": self.tag,
                "target_commit": target_commit,
                "release_publish_signature": self.state.get("c1_release_publish_signature", ""),
            }
        if gate_id == "C3":
            return {
                "kind": "release_run_gate",
                "gate_id": gate_id,
                "version": self.version,
                "action": "dispatch and watch package-index publication workflow",
                "tag": self.tag,
                "target_commit": target_commit,
                "workflow": self._package_index_workflow(),
            }
        return {
            "kind": "release_run_gate",
            "gate_id": gate_id,
            "version": self.version,
            "action": "execute work finish for DOI closeout branch",
            "tag": self.tag,
            "branch": self.doi_branch,
            "paths": list(self.state.get("d_paths") or []),
            "target_commit": target_commit,
        }

    def _awaiting_approval(self, gate_id: str, gate: dict[str, Any]) -> dict[str, Any]:
        signature = str(gate["approval_signature"])
        return {
            "step_id": gate_id,
            "result_status": "AWAITING_APPROVAL",
            "gate": gate,
            "next_action": self._next_action(gate_id, signature),
        }

    def _next_action(self, gate_id: str, signature: str) -> str:
        from agentic_project_kit.release_run_approval import approval_next_action

        return approval_next_action(self, signature)

    def _summary_args(self) -> list[str]:
        args: list[str] = []
        for line in self.options.summary_lines or tuple(self.state.get("summary_lines") or []):
            args.extend(["--summary-line", str(line)])
        return args

    def _package_index_workflow(self) -> dict[str, Any]:
        config = self._release_config()
        workflow = config.get("package_index_workflow") if isinstance(config, dict) else None
        if not isinstance(workflow, dict):
            workflow = {}
        file_name = str(workflow.get("file") or "")
        if not file_name:
            file_name = "release.yml"
        raw_input = workflow.get("input") or workflow.get("inputs") or []
        if isinstance(raw_input, str):
            inputs = [raw_input]
        elif isinstance(raw_input, list):
            inputs = [str(item) for item in raw_input]
        else:
            inputs = []
        if not inputs:
            inputs = _derived_package_index_inputs(publication_policy_for(self.root))
        blockers = _package_index_workflow_blockers(self.root, file_name, inputs)
        return {"file": file_name, "inputs": inputs, "blockers": blockers}

    def _release_config(self) -> dict[str, Any]:
        path = self.root / ".agentic" / "config.yaml"
        if not path.exists():
            return {}
        loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if not isinstance(loaded, dict):
            return {}
        release = loaded.get("release")
        return release if isinstance(release, dict) else {}

    def _current_head(self) -> str:
        completed = self.runner(["git", "rev-parse", "HEAD"], self.root)
        if completed.returncode != 0:
            return ""
        return completed.stdout.strip()

    def _is_finished(self, step_id: str) -> bool:
        return step_id in set(self.state.get("finished_steps") or [])

    def _mark_finished(self, step_id: str, result: dict[str, Any]) -> None:
        finished = list(self.state.get("finished_steps") or [])
        if step_id not in finished:
            finished.append(step_id)
        self.state["finished_steps"] = finished
        if step_id == "B4" and self.state.get("release_consent"):
            # Only a successful governed merge+handoff may advance the approved
            # source commit to the publication target. Later gates cannot repin it.
            head = self._current_head()
            self.state["release_consent"]["expected_head"] = head
            self._append_log({"kind": "release_consent_commit_transition", "step_id": step_id, "target_commit": head})
        self.state.setdefault("step_results", {})[step_id] = _compact_step_result(result)
        self._save_state()

    def _payload(self, current: dict[str, Any]) -> dict[str, Any]:
        status = str(current.get("result_status") or "BLOCKED")
        return {
            "schema_version": 1,
            "kind": "release_run_result",
            "result_status": status,
            "version": self.version,
            "current_step": current.get("step_id", ""),
            "gate": current.get("gate"),
            "blockers": current.get("blockers", []),
            "approvals": list(self.state.get("approvals") or []),
            "release_consent": self.state.get("release_consent"),
            "finished_steps": list(self.state.get("finished_steps") or []),
            "state_path": self.state_path.as_posix(),
            "log_path": self.log_path.as_posix(),
            "next_action": current.get("next_action", "Continue release run."),
        }

    def _load_state(self) -> dict[str, Any]:
        if not self.state_path.exists():
            return {}
        loaded = json.loads(self.state_path.read_text(encoding="utf-8"))
        return loaded if isinstance(loaded, dict) else {}

    def _save_state(self) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        pending = self.state_path.with_suffix(".json.pending")
        pending.write_text(json.dumps(self.state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        pending.replace(self.state_path)

    def _append_log(self, payload: dict[str, Any]) -> None:
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with self.log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True) + "\n")


def run_release(options: ReleaseRunOptions, *, runner: Runner | None = None) -> dict[str, Any]:
    return ReleaseRun(options, runner=runner).run()


def _derived_package_index_inputs(policy) -> list[str]:
    if policy.uses_pypi:
        return ["publish_target=pypi"]
    return []


def _package_index_workflow_blockers(root: Path, workflow_file: str, inputs: list[str]) -> list[str]:
    declared = {value.split("=", 1)[0] for value in inputs if "=" in value}
    workflow_path = root / ".github" / "workflows" / workflow_file
    if not workflow_path.exists():
        return [f"package-index-workflow-missing:{workflow_file}"]
    try:
        loaded = yaml.safe_load(workflow_path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        return []
    if not isinstance(loaded, dict):
        return []
    on_section = loaded.get("on", loaded.get(True, {}))
    if not isinstance(on_section, dict):
        return []
    dispatch = on_section.get("workflow_dispatch")
    if not isinstance(dispatch, dict):
        return []
    workflow_inputs = dispatch.get("inputs")
    if not isinstance(workflow_inputs, dict):
        return []
    blockers: list[str] = []
    for name, spec in workflow_inputs.items():
        if not isinstance(spec, dict):
            continue
        required = bool(spec.get("required"))
        has_default = spec.get("default") is not None
        if required and not has_default and str(name) not in declared:
            blockers.append(f"missing-required-workflow-input:{name}")
    return blockers


def _parse_github_datetime(value: str) -> datetime | None:
    if not value:
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _parse_json(text: str) -> Any:
    stripped = text.strip()
    if not stripped:
        return None
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        return None


def _status_matches(payload: Any, expected: str) -> bool:
    if not isinstance(payload, dict):
        return expected == "PASS"
    if payload.get("result_status") == expected:
        return True
    if payload.get("status") == expected:
        return True
    if expected == "PASS" and payload.get("ok") is True:
        return True
    return False


def _release_publish_ok(payload: Any) -> bool:
    if not isinstance(payload, dict):
        return False
    if payload.get("status") != "PASS":
        return False
    if int(payload.get("blocker_count") or 0) != 0:
        return False
    checks = payload.get("checks")
    if isinstance(checks, list):
        return all(isinstance(check, dict) and check.get("status") == "PASS" for check in checks)
    return True


def _approval_signature(subject: dict[str, Any]) -> str:
    raw = json.dumps(subject, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def _compact_step_result(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "result_status": result.get("result_status"),
        "returncode": result.get("returncode"),
        "blockers": result.get("blockers", []),
    }
