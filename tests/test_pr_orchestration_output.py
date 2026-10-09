from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner
from typer.main import get_command

from agentic_project_kit.cli import app
from agentic_project_kit.pr_orchestration_output import prepare_pr_output


def test_summary_under_4k_preserves_complete_success_evidence(tmp_path):
    payload = {"result_status": "PASS", "pr_number": 123, "next_action": "done", "steps": [
        {"name": "step-" + str(i), "returncode": 0, "stdout": "evidence" * 1000, "stderr": ""} for i in range(40)]}
    summary, rc = prepare_pr_output(payload, root=tmp_path, summary=True)
    assert rc == 0
    assert len(json.dumps(summary).encode()) < 4096
    evidence = json.loads(Path(summary["evidence_path"]).read_text())
    assert evidence["steps"] == payload["steps"]
    assert summary["pr_number"] == 123
    assert summary["result_status"] == "PASS"


@pytest.mark.parametrize("state", ["FAILED", "NOT_RUN", "PENDING"])
def test_ci_finding_is_not_execution_error_or_merge_success(tmp_path, state):
    output = ("PR readiness outcome: TIMEOUT" if state == "PENDING" else
              "PR readiness outcome: BLOCKED\n- check failed: test\nCI state: " + state)
    payload = {"result_status": "BLOCKED", "pr_number": 123, "next_action": "old", "steps": [
        {"name": "pr-wait-ci", "returncode": 1, "stdout": output}]}
    summary, rc = prepare_pr_output(payload, root=tmp_path, summary=True)
    assert rc == 0
    assert summary["result_status"] == "BLOCKED"
    assert summary["execution_status"] == "COMPLETED"
    assert summary["ci_state"] == state
    if state == "NOT_RUN":
        assert "pr rerun-checks --pr 123" in summary["next_action"]
    assert summary["failed_steps"]


def test_unknown_error_keeps_nonzero_exit(tmp_path):
    payload = {"result_status": "BLOCKED", "steps": [{"name": "pr-wait-ci", "returncode": 1,
        "stdout": "PR readiness outcome: GH_ERROR", "stderr": "timeout"}]}
    output, rc = prepare_pr_output(payload, root=tmp_path, summary=True)
    assert rc == 2
    assert "ci_state" not in output


def test_other_failed_step_is_not_hidden_by_ci_finding(tmp_path):
    payload = {"result_status": "BLOCKED", "steps": [
        {"name": "pr-wait-ci", "returncode": 1, "stdout": "PR readiness outcome: BLOCKED\n- check failed: test"},
        {"name": "sync-main", "returncode": 1, "stdout": "failed"}]}
    assert prepare_pr_output(payload, root=tmp_path, summary=True)[1] == 2


def test_nested_ci_finding_propagates_to_outer_create_wrapper(tmp_path):
    payload = {"result_status": "BLOCKED", "pr_number": 12, "steps": [{"name": "pr-complete", "returncode": 0,
        "payload_status": "BLOCKED", "stdout": json.dumps({"result_status": "BLOCKED", "ci_state": "NOT_RUN"})}]}
    result, rc = prepare_pr_output(payload, root=tmp_path, summary=False)
    assert rc == 0
    assert result["ci_state"] == "NOT_RUN"


@pytest.mark.parametrize("route", ["pr-complete", "pr-create-complete", "pr-closeout-complete"])
def test_summary_cli_option_exists(route):
    result = CliRunner().invoke(app, ["transfer", route, "--help"])
    assert result.exit_code == 0
    command = get_command(app).commands["transfer"].commands[route]
    assert any("--summary" in getattr(param, "opts", []) for param in command.params)


def test_closeout_cli_red_ci_rc0_and_summary(monkeypatch, tmp_path):
    from agentic_project_kit.pr_closeout_complete import PrCloseoutCompleteResult, PrCloseoutStep
    from agentic_project_kit.release_process_guardrails import rc_from_result_payload

    monkeypatch.chdir(tmp_path)
    result = PrCloseoutCompleteResult(12, "BLOCKED", 2, "PR_CI_BLOCKED", "inspect", False, steps=(
        PrCloseoutStep("pr-wait-ci", "FAIL", 1, "inspect", "PR readiness outcome: BLOCKED\n- check failed: test\nCI state: NOT_RUN"),))
    monkeypatch.setattr("agentic_project_kit.cli_commands.transfer_pr_closeout_complete.pr_closeout_complete",
                        lambda *a, **kw: result)
    response = CliRunner().invoke(app, ["transfer", "pr-closeout-complete", "--after-pr", "12", "--summary", "--json"])
    assert response.exit_code == 0
    payload = json.loads(response.stdout)
    assert payload["ci_state"] == "NOT_RUN"
    assert payload["merged_pr"] is False
    assert rc_from_result_payload(payload) == 2  # Existing merge/release guard still rejects it.
    assert len(response.stdout.encode()) < 4096
    assert Path(payload["evidence_path"]).is_file()


def test_create_cli_propagates_red_ci_without_merge(monkeypatch, tmp_path):
    import subprocess
    from agentic_project_kit.cli_commands import transfer_pr_create_flow as flow

    monkeypatch.chdir(tmp_path)
    calls = []
    def run(argv, **kw):
        calls.append(argv)
        if argv == ["git", "branch", "--show-current"]:
            return subprocess.CompletedProcess(argv, 0, "codex/demo", "")
        if argv == ["git", "rev-parse", "HEAD"]:
            return subprocess.CompletedProcess(argv, 0, "a" * 40, "")
        if "pr-create" in argv:
            return subprocess.CompletedProcess(argv, 0, "https://github.com/owner/project/pull/12", "")
        if "pr-complete" in argv:
            return subprocess.CompletedProcess(argv, 0, json.dumps({"kind": "transfer_pr_complete_result",
                "result_status": "BLOCKED", "ci_state": "FAILED", "returncode": 0}), "")
        return subprocess.CompletedProcess(argv, 99, "", "unexpected command")
    monkeypatch.setattr(subprocess, "run", run)
    monkeypatch.setattr(flow, "bind_github_cli_env_for_origin", lambda root: {})
    for attr in ("_require_transfer_capability", "_require_current_communication_context_or_exit"):
        monkeypatch.setattr("agentic_project_kit.cli_commands.transfer." + attr, lambda *a, **kw: None)
    result = CliRunner().invoke(app, ["transfer", "pr-create-complete", "--title", "Fix demo",
                                   "--skip-llm-context-gate", "--summary", "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["result_status"] == "BLOCKED"
    assert payload["ci_state"] == "FAILED"
    assert not any("post-merge-complete" in call for call in calls)


def test_evidence_write_failure_is_structured_blocker(monkeypatch, tmp_path):
    original = Path.write_text
    def fail(path, *a, **kw):
        if path.name.startswith("pr-orchestration-"):
            raise OSError("disk full")
        return original(path, *a, **kw)
    monkeypatch.setattr(Path, "write_text", fail)
    result, rc = prepare_pr_output({"result_status": "PASS", "steps": []}, root=tmp_path, summary=True)
    assert rc == 2
    assert result["result_status"] == "BLOCKED"
    assert "disk full" in result["blocker"]


def test_unicode_failure_details_are_byte_bounded(tmp_path):
    payload = {"result_status": "BLOCKED", "next_action": "inspect" * 1000, "steps": [
        {"name": "stage", "returncode": 1, "stdout": "🚀" * 4000, "stderr": "錯" * 4000} for _ in range(20)]}
    out, rc = prepare_pr_output(payload, root=tmp_path, summary=True)
    assert rc == 2
    assert len(json.dumps(out, ensure_ascii=False).encode()) < 4096
    assert json.loads(Path(out["evidence_path"]).read_text())["steps"] == payload["steps"]


def test_closeout_cli_unicode_failure_output_stays_under_4k(monkeypatch, tmp_path):
    from agentic_project_kit.pr_closeout_complete import PrCloseoutCompleteResult, PrCloseoutStep

    monkeypatch.chdir(tmp_path)
    raw = "PR readiness outcome: BLOCKED\n- check failed: test\nCI state: FAILED\n" + "🚀" * 4000
    steps = tuple(PrCloseoutStep("pr-wait-ci", "FAIL", 1, "inspect", raw, "錯" * 4000) for _ in range(2))
    result = PrCloseoutCompleteResult(12, "BLOCKED", 2, "PR_CI_BLOCKED", "inspect", False, steps=steps)
    monkeypatch.setattr("agentic_project_kit.cli_commands.transfer_pr_closeout_complete.pr_closeout_complete",
                        lambda *a, **kw: result)
    response = CliRunner().invoke(app, ["transfer", "pr-closeout-complete", "--after-pr", "12", "--summary", "--json"])
    assert response.exit_code == 0
    assert len(response.stdout.encode()) < 4096
    payload = json.loads(response.stdout)
    assert payload["ci_state"] == "FAILED"
    assert json.loads(Path(payload["evidence_path"]).read_text())["steps"][0]["stdout"] == raw
