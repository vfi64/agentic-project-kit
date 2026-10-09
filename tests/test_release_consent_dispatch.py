"""External workspace regressions for attributed consent and C3 recovery."""
import json
from pathlib import Path

import pytest

from agentic_project_kit.release_run import ReleaseRun, ReleaseRunOptions, run_release
from test_release_run import FakeRunner, _state_path, _workspace


def upfront(root: Path) -> None:
    _workspace(root, package_index_workflow=False)
    path = root / ".agentic/config.yaml"
    path.write_text(path.read_text() + "release:\n  approval: upfront\n")


def test_upfront_consent_runs_all_matching_gates_and_records_identity(tmp_path):
    upfront(tmp_path)
    runner = FakeRunner()
    first = run_release(ReleaseRunOptions(version="1.2.3", root=tmp_path), runner=runner)
    assert first["current_step"] == "B4"
    assert first["gate"]["release_plan"]["tag"] == "v1.2.3"
    result = run_release(ReleaseRunOptions(version="1.2.3", root=tmp_path, execute=True,
                         expected_signature=first["gate"]["approval_signature"],
                         approved_by="owner", consent_source="work-order:42"), runner=runner)
    assert result["result_status"] == "PASS"
    assert [a["step_id"] for a in result["approvals"]] == ["B4", "C2", "C3", "D4"]
    assert all(a["approved_by"] == "owner" and a["consent_source"] == "work-order:42" for a in result["approvals"])
    log = Path(result["log_path"]).read_text()
    assert '"kind": "release_gate_approval"' in log
    assert '"consent_source": "work-order:42"' in log


def test_upfront_missing_attribution_and_wrong_signature_have_no_gated_effect(tmp_path):
    upfront(tmp_path)
    runner = FakeRunner()
    first = run_release(ReleaseRunOptions(version="1.2.3", root=tmp_path), runner=runner)
    for sig, blocker in [("wrong", "signature-mismatch"), (first["gate"]["approval_signature"], "release-consent-attribution-required")]:
        result = run_release(ReleaseRunOptions(version="1.2.3", root=tmp_path, execute=True, expected_signature=sig), runner=runner)
        assert result["blockers"] == [blocker]
    assert not any("finish" in call and "--execute" in call for call in runner.calls)


@pytest.mark.parametrize("drift", ["version", "tag", "publication_policy", "workflow"])
def test_upfront_resumed_plan_drift_blocks_before_subprocess(tmp_path, drift):
    upfront(tmp_path)
    runner = FakeRunner()
    first = run_release(ReleaseRunOptions(version="1.2.3", root=tmp_path), runner=runner)
    runner.block_step = "release-publish"
    run_release(ReleaseRunOptions(version="1.2.3", root=tmp_path, execute=True,
                expected_signature=first["gate"]["approval_signature"], approved_by="owner", consent_source="click:1"), runner=runner)
    state = json.loads(_state_path(tmp_path).read_text())
    state["release_consent"]["plan"][drift] = "different"
    _state_path(tmp_path).write_text(json.dumps(state))
    runner.calls.clear()
    result = run_release(ReleaseRunOptions(version="1.2.3", root=tmp_path), runner=runner)
    assert result["blockers"] == ["release-consent-plan-drift"]
    assert runner.calls == []


def test_upfront_target_commit_drift_blocks_before_publish(tmp_path):
    upfront(tmp_path)
    runner = FakeRunner()
    first = run_release(ReleaseRunOptions(version="1.2.3", root=tmp_path), runner=runner)
    runner.block_step = "release-publish"
    run_release(ReleaseRunOptions(version="1.2.3", root=tmp_path, execute=True,
                expected_signature=first["gate"]["approval_signature"], approved_by="owner", consent_source="click:1"), runner=runner)
    state = json.loads(_state_path(tmp_path).read_text())
    state["finished_steps"].append("C1")
    state["release_consent"]["expected_head"] = "another-commit"
    _state_path(tmp_path).write_text(json.dumps(state))
    runner.calls.clear()
    result = run_release(ReleaseRunOptions(version="1.2.3", root=tmp_path), runner=runner)
    assert result["blockers"] == ["release-consent-commit-drift"]
    assert not any("release-publish" in call for call in runner.calls)


def test_declared_per_gate_requires_attribution_and_stops_at_next_gate(tmp_path):
    upfront(tmp_path)
    path = tmp_path / ".agentic/config.yaml"
    path.write_text(path.read_text().replace("upfront", "per_gate"))
    runner = FakeRunner()
    first = run_release(ReleaseRunOptions(version="1.2.3", root=tmp_path), runner=runner)
    result = run_release(ReleaseRunOptions(version="1.2.3", root=tmp_path, execute=True,
                         expected_signature=first["gate"]["approval_signature"], approved_by="owner", consent_source="chat:1"), runner=runner)
    assert result["current_step"] == "C2" and result["result_status"] == "AWAITING_APPROVAL"
    assert result["approvals"][0]["consent_source"] == "chat:1"


def dispatch_run(root, runner):
    _workspace(root)
    run = ReleaseRun(ReleaseRunOptions(version="1.2.3", root=root), runner=runner)
    run.state = {"finished_steps": []}
    return run


class DelayedRunner(FakeRunner):
    def __init__(self, rows):
        super().__init__()
        self.rows = rows

    def __call__(self, argv, cwd):
        if list(argv[:3]) == ["gh", "run", "list"]:
            self.calls.append(list(argv))
            return self._completed(list(argv), json.dumps(self.rows.pop(0) if self.rows else []))
        if list(argv[:3]) == ["gh", "workflow", "run"]:
            state = json.loads(_state_path(cwd).read_text())
            assert state["c3_dispatch"]["dispatched"] is True  # before API call
        return super().__call__(argv, cwd)


def row(number=12345, **kwargs):
    return {"databaseId": number, "event": "workflow_dispatch", "headSha": "abc123",
            "createdAt": "2099-01-01T00:00:00Z", **kwargs}


def test_dispatch_waits_for_visibility_and_logs_all_attempts(tmp_path, monkeypatch):
    monkeypatch.setattr("agentic_project_kit.release_run_dispatch.time.sleep", lambda _: None)
    runner = DelayedRunner([[], [], [row()]])
    run = dispatch_run(tmp_path, runner)
    assert run._step_c3()["result_status"] == "PASS"
    assert sum(c[:3] == ["gh", "workflow", "run"] for c in runner.calls) == 1
    assert sum(c[:3] == ["gh", "run", "list"] for c in runner.calls) == 3
    assert run.log_path.read_text().count('"step_id": "C3-identify"') == 2


def test_missing_run_id_resumes_search_without_redispatch(tmp_path, monkeypatch):
    monkeypatch.setattr("agentic_project_kit.release_run_dispatch.time.sleep", lambda _: None)
    runner = DelayedRunner([])
    run = dispatch_run(tmp_path, runner)
    assert run._step_c3()["result_status"] == "BLOCKED"
    assert sum(c[:3] == ["gh", "run", "list"] for c in runner.calls) == 7
    runner.rows = [[row()]]
    resumed = ReleaseRun(ReleaseRunOptions(version="1.2.3", root=tmp_path), runner=runner)
    assert resumed._step_c3()["result_status"] == "PASS"
    assert sum(c[:3] == ["gh", "workflow", "run"] for c in runner.calls) == 1


@pytest.mark.parametrize("rows", [[row(headSha="wrong")], [row(event="push")],
                                   [row(createdAt="2020-01-01T00:00:00Z")], [row(1), row(2)]])
def test_unrelated_old_or_ambiguous_runs_are_never_watched(tmp_path, monkeypatch, rows):
    monkeypatch.setattr("agentic_project_kit.release_run_dispatch.time.sleep", lambda _: None)
    runner = DelayedRunner([[], *([rows] * 6)])
    run = dispatch_run(tmp_path, runner)
    assert run._step_c3()["result_status"] == "BLOCKED"
    assert not any(c[:3] == ["gh", "run", "watch"] for c in runner.calls)


def test_release_run_cli_forwards_attribution_and_returns_pure_json(monkeypatch):
    from typer.testing import CliRunner
    from agentic_project_kit.cli import app
    from agentic_project_kit.cli_commands import human_workflows

    seen = []
    def fake_run(options):
        seen.append(options)
        return {"result_status": "BLOCKED", "blockers": ["signature-mismatch"]}
    monkeypatch.setattr(human_workflows, "run_release", fake_run)
    result = CliRunner().invoke(app, ["release", "run", "--version", "1.2.3", "--execute",
        "--expected-signature", "bad", "--approved-by", "owner", "--consent-source", "work-order:42", "--json"])
    assert result.exit_code == 2
    assert json.loads(result.output)["blockers"] == ["signature-mismatch"]
    assert seen[0].approved_by == "owner" and seen[0].consent_source == "work-order:42"


def test_invalid_approval_policy_blocks_before_any_subprocess(tmp_path):
    upfront(tmp_path)
    path = tmp_path / ".agentic/config.yaml"
    path.write_text(path.read_text().replace("upfront", "invalid"))
    runner = FakeRunner()
    result = run_release(ReleaseRunOptions(version="1.2.3", root=tmp_path), runner=runner)
    assert result["blockers"] == ["invalid-release-approval-policy"]
    assert runner.calls == []


def test_dispatch_inventory_rejects_an_existing_run_in_the_same_second(tmp_path, monkeypatch):
    from datetime import datetime, timezone
    monkeypatch.setattr("agentic_project_kit.release_run_dispatch.time.sleep", lambda _: None)
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    stale = row(111, createdAt=now)
    runner = DelayedRunner([[stale], [stale, row(222)]])
    run = dispatch_run(tmp_path, runner)
    assert run._step_c3()["result_status"] == "PASS"
    assert [c for c in runner.calls if c[:3] == ["gh", "run", "watch"]][-1][3] == "222"


def test_uncertain_dispatch_response_never_causes_a_second_dispatch(tmp_path):
    class UncertainRunner(DelayedRunner):
        def __call__(self, argv, cwd):
            if list(argv[:3]) == ["gh", "workflow", "run"]:
                self.calls.append(list(argv))
                assert json.loads(_state_path(cwd).read_text())["c3_dispatch"]["dispatched"]
                return self._completed(list(argv), "", "connection interrupted", rc=1)
            return super().__call__(argv, cwd)

    runner = UncertainRunner([[], [row()]])
    run = dispatch_run(tmp_path, runner)
    assert run._step_c3()["result_status"] == "BLOCKED"
    resumed = ReleaseRun(ReleaseRunOptions(version="1.2.3", root=tmp_path), runner=runner)
    assert resumed._step_c3()["result_status"] == "PASS"
    assert sum(c[:3] == ["gh", "workflow", "run"] for c in runner.calls) == 1
