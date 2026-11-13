"""K5 (V3, release 1.3.0 B4): transfer commit retries a held .git/index.lock a bounded number of
times, logs every retry, and ends BLOCKED with the rerun command when the lock stays."""
import subprocess

import agentic_project_kit.transfer_repo_actions as tra

LOCK = "fatal: Unable to create '/repo/.git/index.lock': File exists.\n"


def _fake(sequence, calls):
    def run(command, *, cwd=None):
        calls.append(list(command))
        rc, err = sequence.pop(0)
        return subprocess.CompletedProcess(command, rc, "", err)
    return run


def test_policy_is_five_attempts_two_seconds_apart():
    assert tra.INDEX_LOCK_RETRY_DELAYS_SECONDS == (2.0, 2.0, 2.0, 2.0)


def test_lock_gone_after_the_second_attempt_commits_and_logs_the_retry(monkeypatch):
    calls, sleeps = [], []
    monkeypatch.setattr(tra, "_run", _fake([(128, LOCK), (0, "")], calls))
    completed = tra._run_index_retry_with(["git", "commit", "-m", "m"], sleeps.append)
    assert completed.returncode == 0 and len(calls) == 2 and sleeps == [2.0]
    assert "KIT_INDEX_LOCK_RETRY attempt=2" in completed.stderr


def test_retry_is_bounded(monkeypatch):
    calls, sleeps = [], []
    monkeypatch.setattr(tra, "_run", _fake([(128, LOCK)] * 5, calls))
    completed = tra._run_index_retry_with(["git", "add", "x"], sleeps.append)
    assert tra._is_index_lock_failure(completed) and len(calls) == 5 and sum(sleeps) == 8.0


def test_other_failures_are_not_retried(monkeypatch):
    calls, sleeps = [], []
    monkeypatch.setattr(tra, "_run", _fake([(1, "nothing to commit\n")], calls))
    completed = tra._run_index_retry_with(["git", "commit", "-m", "m"], sleeps.append)
    assert completed.returncode == 1 and len(calls) == 1 and sleeps == []


def test_a_lock_that_stays_blocks_commit_paths_with_the_rerun_command(monkeypatch):
    monkeypatch.setattr(tra, "_current_branch_result", lambda: ("fix/x", None))
    monkeypatch.setattr(tra, "_selection_includes_dirty_rule_ack_state", lambda paths: False)
    monkeypatch.setattr(tra.time, "sleep", lambda delay: None)
    calls: list[list[str]] = []
    monkeypatch.setattr(tra, "_run", _fake([(128, LOCK)] * 5, calls))
    result = tra._commit_paths_unlocked("Msg", ["a.py"])
    assert result.result_status == "BLOCKED"
    assert result.next_command == "agentic-kit transfer commit --message Msg --path a.py"
    assert result.next_command_autonomous is True
    assert all(call[:2] == ["git", "add"] for call in calls)
    data = result.as_json_data()
    assert {"next_command", "next_command_autonomous"} <= set(data)
