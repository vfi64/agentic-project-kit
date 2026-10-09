from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.github_ci_failure import classify_failed_job
from agentic_project_kit.pr_ci_rerun import rerun_checks


class FakeApi:
    def __init__(self):
        self.calls = []
        self.head = "a" * 40
        self.attempt = 1
        self.steps = []
        self.start = "0001-01-01T00:00:00Z"
        self.end = "2026-10-09T18:00:01Z"
        self.fail_post = False

    def __call__(self, path, method):
        self.calls.append((path, method))
        if method == "POST":
            if self.fail_post:
                raise RuntimeError("connection lost after request")
            return None
        if "/pulls/" in path:
            return {"state": "open", "base": {"repo": {"full_name": "owner/project"}}, "head": {"sha": self.head}}
        if "head_sha=" in path:
            return [{"workflow_runs": [{"id": 10, "workflow_id": 5, "event": "pull_request",
                "head_sha": self.head, "run_attempt": self.attempt, "status": "completed", "conclusion": "failure"}]}]
        if "/jobs?" in path:
            return [{"jobs": [{"id": 20, "name": "test", "status": "completed", "conclusion": "failure",
                              "started_at": self.start, "completed_at": self.end, "steps": self.steps}]}]
        raise AssertionError(path)


def job(**kw):
    data = {"status": "completed", "conclusion": "failure", "started_at": "2026-10-09T18:00:00Z",
            "completed_at": "2026-10-09T18:00:03Z", "steps": []}
    data.update(kw)
    return data


@pytest.mark.parametrize("start", [None, "", "0001-01-01T00:00:00Z", "2026-10-09T18:00:00Z"])
def test_never_started_or_short_failure(start):
    assert classify_failed_job(job(started_at=start))[0] == "NOT_RUN"


@pytest.mark.parametrize("kw,state", [
    ({"steps": [{"conclusion": "failure", "name": "pytest"}]}, "FAILED"),
    ({"steps": [{"conclusion": "cancelled"}]}, "FAILED"),
    ({"completed_at": "2026-10-09T18:00:04Z"}, "FAILED"),
    ({"started_at": "invalid"}, "UNKNOWN"),
    ({"completed_at": "invalid"}, "UNKNOWN"),
    ({"completed_at": "2026-10-09T17:00:00Z"}, "UNKNOWN"),
    ({"status": "in_progress"}, "PENDING"),
    ({"steps": None}, "UNKNOWN"),
])
def test_real_failure_and_unknown_evidence_refused(kw, state):
    assert classify_failed_job(job(**kw))[0] == state


def test_plan_then_signed_execute_records_run_ids(tmp_path):
    api = FakeApi()
    plan = rerun_checks(tmp_path, 12, api=api)
    assert plan["result_status"] == "AWAITING_APPROVAL"
    assert not any(method == "POST" for _, method in api.calls)
    done = rerun_checks(tmp_path, 12, execute=True, expected_signature=plan["approval_signature"], api=api)
    assert done["result_status"] == "PASS"
    assert done["rerun_run_ids"] == [10]
    assert json.loads(Path(done["receipt_path"]).read_text())["rerun_run_ids"] == [10]
    again = rerun_checks(tmp_path, 12, execute=True, expected_signature=plan["approval_signature"], api=api)
    assert again["result_status"] == "BLOCKED"
    assert len([m for _, m in api.calls if m == "POST"]) == 1


@pytest.mark.parametrize("drift", ["wrong", "head", "attempt", "test"])
def test_wrong_or_stale_signature_has_no_mutation(tmp_path, drift):
    api = FakeApi()
    plan = rerun_checks(tmp_path, 12, api=api)
    sig = plan["approval_signature"]
    if drift == "wrong":
        sig = "bad"
    if drift == "head":
        api.head = "b" * 40
    if drift == "attempt":
        api.attempt = 2
    if drift == "test":
        api.steps = [{"conclusion": "failure"}]
    result = rerun_checks(tmp_path, 12, execute=True, expected_signature=sig, api=api)
    assert result["result_status"] == "BLOCKED"
    assert not any(method == "POST" for _, method in api.calls)


def test_lost_post_response_preserves_intent_and_does_not_repeat(tmp_path):
    api = FakeApi()
    sig = rerun_checks(tmp_path, 12, api=api)["approval_signature"]
    api.fail_post = True
    result = rerun_checks(tmp_path, 12, execute=True, expected_signature=sig, api=api)
    assert result["result_status"] == "BLOCKED"
    receipt = json.loads(Path(result["receipt_path"]).read_text())
    assert receipt["attempted_run_ids"] == [10]
    assert receipt["rerun_run_ids"] == []
    rerun_checks(tmp_path, 12, execute=True, expected_signature=sig, api=api)
    assert len([m for _, m in api.calls if m == "POST"]) == 1


def test_fresh_pre_execution_head_drift_blocks(tmp_path):
    api = FakeApi()
    sig = rerun_checks(tmp_path, 12, api=api)["approval_signature"]
    count = 0
    def moving(path, method):
        nonlocal count
        if "/pulls/" in path:
            count += 1
            if count == 2:
                api.head = "b" * 40
        return api(path, method)
    assert rerun_checks(tmp_path, 12, execute=True, expected_signature=sig, api=moving)["result_status"] == "BLOCKED"
    assert not any(m == "POST" for _, m in api.calls)


def test_paginated_jobs_include_real_test_failure(tmp_path):
    api = FakeApi()
    def paged(path, method):
        data = api(path, method)
        if "/jobs?" in path:
            second = copy.deepcopy(data[0])
            second["jobs"][0]["steps"] = [{"conclusion": "failure"}]
            data.append(second)
        return data
    result = rerun_checks(tmp_path, 12, api=paged)
    assert result["result_status"] == "BLOCKED"
    assert "executable job step failed" in str(result)


def test_old_failed_run_is_not_rerun(tmp_path):
    api = FakeApi()
    def with_old(path, method):
        data = api(path, method)
        if "head_sha=" in path:
            old = copy.deepcopy(data[0]["workflow_runs"][0])
            old["id"] = 9
            data[0]["workflow_runs"].append(old)
        return data
    plan = rerun_checks(tmp_path, 12, api=with_old)
    assert [r["run_id"] for r in plan["plan"]["runs"]] == [10]


def test_cli_one_json_document(monkeypatch):
    monkeypatch.setattr("agentic_project_kit.pr_ci_rerun.rerun_checks", lambda *a, **kw: {
        "result_status": "BLOCKED", "next_action": "inspect", "evidence_path": "tmp/result.json"})
    result = CliRunner().invoke(app, ["pr", "rerun-checks", "--pr", "12", "--json"])
    assert result.exit_code == 2
    assert json.loads(result.stdout)["result_status"] == "BLOCKED"


def test_zero_jobs_is_distinct_from_unavailable_jobs(tmp_path):
    api = FakeApi()
    def empty(path, method):
        return [{"jobs": []}] if "/jobs?" in path else api(path, method)
    result = rerun_checks(tmp_path, 12, api=empty)
    assert result["result_status"] == "AWAITING_APPROVAL"
    def unavailable(path, method):
        if "/jobs?" in path:
            raise RuntimeError("HTTP 403")
        return api(path, method)
    blocked = rerun_checks(tmp_path, 12, api=unavailable)
    assert blocked["result_status"] == "BLOCKED"
    assert "HTTP 403" in blocked["blocker"]


def test_mixed_not_run_and_real_failed_jobs_refuses_all(tmp_path):
    api = FakeApi()
    def mixed(path, method):
        data = api(path, method)
        if "/jobs?" in path:
            real = copy.deepcopy(data[0]["jobs"][0])
            real["id"] = 21
            real["steps"] = [{"conclusion": "failure"}]
            data[0]["jobs"].append(real)
        return data
    result = rerun_checks(tmp_path, 12, execute=True, expected_signature="invalid", api=mixed)
    assert result["result_status"] == "BLOCKED"
    assert not any(m == "POST" for _, m in api.calls)


def test_missing_start_field_is_not_a_missing_start_timestamp():
    data = job()
    del data["started_at"]
    assert classify_failed_job(data)[0] == "UNKNOWN"


def test_manifest_declares_remote_mutation():
    from agentic_project_kit.command_manifest import build_current_reference
    ref = build_current_reference()
    command = next(c for c in ref["commands"] if c["qualified_name"] == "agentic-kit pr rerun-checks")
    assert command["remote_effects"] == ["network_read", "workflow_rerun"]
    assert command["safety"] == "BOUNDED"
    assert command["dry_run_available"]


def test_another_pr_signature_cannot_replay_same_workflow_attempt(tmp_path):
    api = FakeApi()
    first = rerun_checks(tmp_path, 12, api=api)
    assert rerun_checks(tmp_path, 12, execute=True, expected_signature=first["approval_signature"], api=api)["result_status"] == "PASS"
    other = rerun_checks(tmp_path, 13, api=api)
    assert rerun_checks(tmp_path, 13, execute=True, expected_signature=other["approval_signature"], api=api)["result_status"] == "BLOCKED"
    assert len([m for _, m in api.calls if m == "POST"]) == 1


def test_cli_storage_error_is_pure_json(monkeypatch):
    def fail(*a, **kw):
        raise OSError("disk full")
    monkeypatch.setattr("agentic_project_kit.pr_ci_rerun.rerun_checks", fail)
    result = CliRunner().invoke(app, ["pr", "rerun-checks", "--pr", "12", "--json"])
    assert result.exit_code == 2
    assert json.loads(result.stdout)["blocker"] == "disk full"
