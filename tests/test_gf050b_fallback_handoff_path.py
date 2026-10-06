import subprocess

import agentic_project_kit.transfer_repo_actions as tra
from agentic_project_kit.handoff_state import load_handoff_state
from agentic_project_kit.workspace import NAMESPACE_DEFAULTS, Workspace


def test_gf050b_namespace_admin_refresh_reads_workspace_state(tmp_path, monkeypatch):
    ws = Workspace(tmp_path, NAMESPACE_DEFAULTS)
    state = ws.handoff_state_path()
    state.parent.mkdir(parents=True)
    state.write_text("schema_version: 1\n")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(tra, "load_workspace", lambda _p: ws)
    monkeypatch.setattr(tra, "_is_refresh_only_pr", lambda *_a, **_k: False)
    monkeypatch.setattr(
        tra,
        "_admin_refresh_pr_unlocked",
        lambda *_a, **_k: (
            load_handoff_state(ws.handoff_state_path()),
            tra.RepoActionResult("admin-refresh-pr", "PASS", 0, ["x"], "ok\n", "", "next"),
        )[1],
    )
    assert tra.admin_refresh_pr(1).result_status == "PASS"


def test_gf050b_missing_state_skips_before_branch(tmp_path, monkeypatch):
    ws = Workspace(tmp_path, NAMESPACE_DEFAULTS)
    monkeypatch.setattr(tra, "load_workspace", lambda _p: ws)
    monkeypatch.setattr(
        tra,
        "_is_refresh_only_pr",
        lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("must not run")),
    )
    result = tra.admin_refresh_pr(2)
    assert result.result_status == "PASS"
    assert ws.path_text(ws.handoff_state_path()) in result.stdout


def test_gf050b_failure_cleanup_returns_to_main(monkeypatch):
    calls = []

    def fake(command, cwd=None):
        calls.append(command)
        out = "main\n" if command == ["git", "branch", "--show-current"] else ""
        return subprocess.CompletedProcess(command, 0, out, "")

    monkeypatch.setattr(tra, "_run", fake)
    failed = subprocess.CompletedProcess(["bad"], 2, "", "boom")
    tra._admin_refresh_failure(
        ["bad"], failed, "failed", main_branch="main", start_point="origin/main"
    )
    assert ["git", "reset", "--hard", "origin/main"] in calls
    assert ["git", "clean", "-fd"] in calls
    assert ["git", "switch", "main"] in calls


def test_gf050b_pr_wait_ci_timeout_is_pending(monkeypatch):
    monkeypatch.setattr(tra, "_resolve_pr_head_sha", lambda *_a, **_k: ("a" * 40, None))
    monkeypatch.setattr(
        tra,
        "_run",
        lambda command, cwd=None: subprocess.CompletedProcess(
            command, 1, "PR readiness outcome: TIMEOUT\n", ""
        ),
    )
    result = tra.pr_wait_ci(2501)
    assert result.result_status == "PENDING"
    assert result.returncode == 1


def test_gf050b_pr_wait_ci_blocked_stays_fail(monkeypatch):
    monkeypatch.setattr(tra, "_resolve_pr_head_sha", lambda *_a, **_k: ("a" * 40, None))
    monkeypatch.setattr(
        tra,
        "_run",
        lambda command, cwd=None: subprocess.CompletedProcess(
            command, 1, "PR readiness outcome: BLOCKED\n", ""
        ),
    )
    result = tra.pr_wait_ci(2501)
    assert result.result_status == "FAIL"
    assert result.returncode == 1
