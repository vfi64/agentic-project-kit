"""K6: "CI never started" is its own state with its own route (owner decisions E3 c, variant A).

Release 1.3.0 (V4): the CI run stayed in the queue, `pr rerun-checks` needs a failed run, and the
release wait ended after 900 s with a plain TIMEOUT. Now a timeout whose last snapshot shows no
started check reports `ci_state` NOT_STARTED and names `agentic-kit pr wait-ci <PR>` as a transient
retry within the consent given, with a reason that sends a person to GitHub Actions if the queue
stays stuck. work finish and release run inherit that route from the nested result.
"""
from __future__ import annotations

import json
import subprocess

from agentic_project_kit.blocked_route import KIND_HUMAN, KIND_KIT, nested_route, route_problems
from agentic_project_kit.ci_readiness import (
    CI_NOT_STARTED_PREFIX,
    TIMEOUT,
    TIMEOUT_REASON,
    ci_not_started_reasons,
    render_pr_readiness,
    wait_for_pr_readiness,
)
from agentic_project_kit.cli_commands.human_workflows import _failed_local_step, _payload, _unrouted_step_reason
from agentic_project_kit.pr_orchestration_output import prepare_pr_output
from agentic_project_kit.release_run import ReleaseRun, ReleaseRunOptions


def _snapshot(*checks):
    return {"state": "OPEN", "headRefOid": "a" * 40, "mergeStateStatus": "BLOCKED", "mergeable": "MERGEABLE",
            "statusCheckRollup": [{"name": name, "status": status, "conclusion": ""} for name, status in checks]}


def _wait(snapshot):
    ticks = iter([0, 0, 1, 2, 3, 4])
    return wait_for_pr_readiness(lambda: snapshot, timeout_seconds=2, interval_seconds=1,
                                 clock=lambda: next(ticks), sleep=lambda seconds: None)


def test_a_timeout_without_any_check_is_ci_not_started():
    decision = _wait(_snapshot())
    assert decision.outcome == TIMEOUT
    assert decision.reasons == (TIMEOUT_REASON, CI_NOT_STARTED_PREFIX + "no check reported")


def test_a_timeout_with_only_queued_checks_is_ci_not_started():
    decision = _wait(_snapshot(("test", "QUEUED"), ("lint", "PENDING")))
    assert decision.reasons[1] == CI_NOT_STARTED_PREFIX + "2 check(s) still queued"


def test_a_timeout_with_a_running_check_is_slow_ci():
    assert _wait(_snapshot(("test", "QUEUED"), ("lint", "IN_PROGRESS"))).reasons == (TIMEOUT_REASON,)


def test_nothing_read_says_nothing_about_the_queue():
    assert ci_not_started_reasons(None) == ()


def _wait_ci_step(decision_text: str) -> dict:
    report = {"action": "pr-wait-ci", "result_status": "PENDING", "returncode": 1, "stdout": decision_text}
    return {"name": "pr-wait-ci", "returncode": 1, "result_status": "PENDING", "stdout": json.dumps(report)}


def _closeout(step: dict) -> dict:
    payload = {"result_status": "BLOCKED", "returncode": 2, "pr_number": 7, "failed_step": "pr-wait-ci",
               "steps": [step], "next_action": "x"}
    return prepare_pr_output(payload, root=None, summary=False)[0]


def test_pr_closeout_names_wait_ci_as_an_autonomous_retry_for_ci_not_started():
    decision = _wait(_snapshot())
    data = _closeout(_wait_ci_step(render_pr_readiness(decision)))
    assert data["ci_state"] == "NOT_STARTED" and route_problems(data) == []
    assert data["next_command"] == data["next_action"] == "agentic-kit pr wait-ci 7"
    assert data["next_command_kind"] == KIND_KIT and data["next_command_autonomous"] is True
    assert "never started" in data["next_command_reason"] and "GitHub Actions" in data["next_command_reason"]


def test_slow_ci_names_wait_ci_without_the_queue_reason():
    data = _closeout(_wait_ci_step(render_pr_readiness(_wait(_snapshot(("test", "IN_PROGRESS"))))))
    assert data["ci_state"] == "PENDING" and data["next_command"] == "agentic-kit pr wait-ci 7"
    assert data["next_command_reason"] == ""


def test_not_run_and_failed_ci_keep_their_routes():
    not_run = {"name": "pr-wait-ci", "returncode": 1, "result_status": "BLOCKED",
               "stdout": json.dumps({"ci_state": "NOT_RUN"})}
    data = _closeout(not_run)
    assert data["next_command"] == "agentic-kit pr rerun-checks --pr 7 --json"
    assert data["next_command_autonomous"] is False, "a rerun needs the signed approval"
    failed = {"name": "pr-wait-ci", "returncode": 1, "result_status": "BLOCKED", "stdout": json.dumps({"ci_state": "FAILED"})}
    data = _closeout(failed)
    assert data["next_command_kind"] == KIND_HUMAN and data["next_command_reason"].startswith("Repair the failed CI")


def _routed_child() -> str:
    return json.dumps({"result_status": "BLOCKED", "ci_state": "NOT_STARTED",
                       "next_command": "agentic-kit pr wait-ci 7", "next_command_autonomous": True,
                       "next_command_kind": KIND_KIT, "next_command_reason": "CI for PR #7 never started"})


def test_work_finish_inherits_the_route_of_its_nested_result():
    step = _failed_local_step("pr-create-complete", "")
    step["stdout"] = _routed_child()
    payload = _payload("work-finish", [step])
    assert route_problems(payload) == []
    assert payload["next_command"] == "agentic-kit pr wait-ci 7" and payload["next_command_autonomous"] is True
    assert payload["ci_state"] == "NOT_STARTED"


def test_a_nested_human_marker_is_not_inherited():
    human = json.dumps({"result_status": "BLOCKED", "next_command": "", "next_command_autonomous": False,
                        "next_command_kind": KIND_HUMAN, "next_command_reason": "owner must decide"})
    assert nested_route(human) == {}
    assert nested_route("not json") == {}
    step = _failed_local_step("pr-create-complete", "")
    step["stdout"] = human
    payload = _payload("work-finish", [step])
    assert payload["next_command_kind"] == KIND_HUMAN and "owner must decide" in payload["next_command_reason"]


def test_release_run_keeps_the_route_of_its_blocked_work_finish(tmp_path):
    child = json.dumps({**json.loads(_routed_child()), "kind": "human_work_finish_result"})

    def runner(argv, root):
        return subprocess.CompletedProcess(argv, 2, child, "")

    run = ReleaseRun(ReleaseRunOptions(version="1.2.3", root=tmp_path), runner=runner)
    step = run._command("B4", ["agentic-kit", "work", "finish", "--json"], expected_status="PASS")
    payload = run._payload(step)
    assert route_problems(payload) == [] and payload["ci_state"] == "NOT_STARTED"
    assert payload["next_command"] == "agentic-kit pr wait-ci 7"
    assert payload["next_action"] == "Run agentic-kit pr wait-ci 7, then continue the release run."


def test_unrouted_reason_reads_the_transfer_summary_block():
    step = _failed_local_step("sync-main", "")
    step["stdout"] = ("*" * 34 + " START SUMMARY " + "*" * 35 + "\nTRANSFER_SYNC_MAIN\n\nSTATE:                  FAIL\n"
                      "BLOCKERS:               1\n\nNEXT:                   Inspect sync-main blockers: normalize-session_failed\n"
                      "CHAT_REPLY:             f | NEXT=Inspect sync-main blockers\n" + "*" * 35 + " END SUMMARY " + "*" * 36 + "\n")
    assert _unrouted_step_reason(step).endswith(
        "sync-main: STATE=FAIL, NEXT=Inspect sync-main blockers: normalize-session_failed")
