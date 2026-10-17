"""Release 1.1.0 regressions: C3 settles from the workflow run, and an unchanged approved gate resumes.

Live 2026-10-17: the PyPI job waited for a required reviewer of the `pypi` environment, `gh run
watch` gave up and C3 was reported BLOCKED; after the deployment was approved, resuming asked for
the byte-identical C3 gate again.
"""

from __future__ import annotations

import json
from pathlib import Path

from agentic_project_kit.release_run import ReleaseRunOptions, run_release
from test_release_run import FakeRunner, _state_path, _workspace


class RunStateRunner(FakeRunner):
    """FakeRunner whose package-index run reports a scripted REST state."""

    def __init__(self, states: list[dict], pending: list[str] | None = None, watch_rc: int = 0) -> None:
        super().__init__()
        self.states = states
        self.pending = pending or []
        self.watch_rc = watch_rc

    def __call__(self, argv, cwd: Path):
        command = [str(item) for item in argv]
        if command[:2] == ["gh", "api"] and command[2].endswith("/pending_deployments"):
            self.calls.append(command)
            return self._completed(command, json.dumps(self.pending) + "\n")
        if command[:2] == ["gh", "api"] and "/actions/runs/" in command[2]:
            self.calls.append(command)
            state = self.states.pop(0) if len(self.states) > 1 else self.states[0]
            return self._completed(command, json.dumps(state) + "\n")
        if command[:3] == ["gh", "run", "watch"]:
            self.calls.append(command)
            return self._completed(command, "", "", rc=self.watch_rc)
        return super().__call__(argv, cwd)


def _to_c3(root: Path, runner: FakeRunner) -> dict:
    result = run_release(ReleaseRunOptions(version="1.2.3", root=root), runner=runner)
    for _ in range(3):
        if result["result_status"] != "AWAITING_APPROVAL" or result["current_step"] == "C3":
            break
        result = run_release(ReleaseRunOptions(version="1.2.3", root=root, execute=True,
                                               expected_signature=result["gate"]["approval_signature"]), runner=runner)
    assert result["current_step"] == "C3" and result["result_status"] == "AWAITING_APPROVAL"
    return result


def _approve(root: Path, runner: FakeRunner, gate_result: dict) -> dict:
    return run_release(ReleaseRunOptions(version="1.2.3", root=root, execute=True,
                                         expected_signature=gate_result["gate"]["approval_signature"]), runner=runner)


def test_environment_approval_pending_is_waiting_not_blocked_and_never_watched(tmp_path: Path) -> None:
    _workspace(tmp_path)
    runner = RunStateRunner([{"status": "waiting", "conclusion": None}], pending=["pypi"])

    result = _approve(tmp_path, runner, _to_c3(tmp_path, runner))

    assert result["result_status"] == "WAITING"
    assert result["blockers"] == ["environment-approval-pending"]
    assert "C3" not in result["finished_steps"]
    assert not any(call[:3] == ["gh", "run", "watch"] for call in runner.calls)


def test_waiting_run_resumes_without_reapproving_the_identical_c3_gate(tmp_path: Path) -> None:
    _workspace(tmp_path)
    runner = RunStateRunner([{"status": "waiting", "conclusion": None}], pending=["pypi"])
    _approve(tmp_path, runner, _to_c3(tmp_path, runner))
    dispatches = sum(1 for call in runner.calls if call[:3] == ["gh", "workflow", "run"])

    runner.states = [{"status": "completed", "conclusion": "success"}]
    resumed = run_release(ReleaseRunOptions(version="1.2.3", root=tmp_path), runner=runner)

    assert "C3" in resumed["finished_steps"]
    assert resumed["current_step"] == "D4" and resumed["result_status"] == "AWAITING_APPROVAL"
    assert [a["step_id"] for a in resumed["approvals"]].count("C3") == 1
    assert sum(1 for call in runner.calls if call[:3] == ["gh", "workflow", "run"]) == dispatches
    assert '"kind": "release_gate_approval_reused"' in Path(resumed["log_path"]).read_text()


def test_a_changed_gate_is_not_covered_by_an_earlier_approval(tmp_path: Path) -> None:
    _workspace(tmp_path)
    runner = RunStateRunner([{"status": "waiting", "conclusion": None}], pending=["pypi"])
    _approve(tmp_path, runner, _to_c3(tmp_path, runner))
    state = json.loads(_state_path(tmp_path).read_text())
    for approval in state["approvals"]:
        if approval["step_id"] == "C3":
            approval["gate"]["approval_signature"] = "a-different-subject"
    _state_path(tmp_path).write_text(json.dumps(state))

    resumed = run_release(ReleaseRunOptions(version="1.2.3", root=tmp_path), runner=runner)

    assert resumed["current_step"] == "C3" and resumed["result_status"] == "AWAITING_APPROVAL"


def test_a_watch_that_gives_up_settles_from_the_completed_run(tmp_path: Path) -> None:
    _workspace(tmp_path)
    runner = RunStateRunner([{"status": "in_progress", "conclusion": None}, {"status": "completed", "conclusion": "success"}],
                            watch_rc=1)

    result = _approve(tmp_path, runner, _to_c3(tmp_path, runner))

    assert "C3" in result["finished_steps"]


def test_a_failed_package_index_run_blocks(tmp_path: Path) -> None:
    _workspace(tmp_path)
    runner = RunStateRunner([{"status": "completed", "conclusion": "failure"}])

    result = _approve(tmp_path, runner, _to_c3(tmp_path, runner))

    assert result["result_status"] == "BLOCKED"
    assert result["blockers"] == ["package-index-run-failure"]
