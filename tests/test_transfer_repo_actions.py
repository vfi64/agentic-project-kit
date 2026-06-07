from __future__ import annotations

import subprocess

from typer.testing import CliRunner

from agentic_project_kit.cli import app
import agentic_project_kit.transfer_repo_actions as transfer_repo_actions
from agentic_project_kit.transfer_repo_actions import (
    admin_refresh_pr,
    branch_create,
    branch_delete,
    branch_switch,
    commit_paths,
    fetch_origin,
    head_sha,
    pr_merge_safe,
    pr_wait_ci,
    post_merge_check,
    pull_current,
    push_current,
    repo_diff,
    repo_log,
    repo_status,
    result_terminal,
)
from tests.test_rule_source_validator import write_minimal_sources
from pathlib import Path


def _init_repo(path):
    subprocess.run(["git", "init"], cwd=path, check=True, stdout=subprocess.PIPE)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=path, check=True)
    (path / "README.md").write_text("base\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=path, check=True)
    subprocess.run(["git", "commit", "-m", "Initial"], cwd=path, check=True, stdout=subprocess.PIPE)
    subprocess.run(["git", "branch", "-M", "main"], cwd=path, check=True, stdout=subprocess.PIPE)


def _acknowledge_rules(path):
    write_minimal_sources(path)
    subprocess.run(["git", "add", "."], cwd=path, check=True)
    subprocess.run(
        ["git", "commit", "-m", "Add minimal rule sources"],
        cwd=path,
        check=True,
        stdout=subprocess.PIPE,
    )
    result = CliRunner().invoke(app, ["rules", "acknowledge", "--root", str(path)])
    assert result.exit_code == 0, result.output


def test_branch_create_and_switch(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    created = branch_create("feature/example", start_point="main")
    switched = branch_switch("main")

    assert created.result_status == "PASS"
    assert switched.result_status == "PASS"


def test_commit_paths(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    (tmp_path / "file.txt").write_text("content\n", encoding="utf-8")

    result = commit_paths("Add file", ["file.txt"], allow_main=True)

    assert result.result_status == "PASS"
    assert result.returncode == 0


def test_commit_paths_refuses_main_by_default(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    (tmp_path / "file.txt").write_text("content\n", encoding="utf-8")

    result = commit_paths("Add file", ["file.txt"])

    assert result.result_status == "FAIL"
    assert result.returncode == 2
    assert "Refusing to commit directly on main" in result.stderr


def test_commit_paths_allows_feature_branch_by_default(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    branch_create("feature/commit-ok", start_point="main")
    (tmp_path / "file.txt").write_text("content\n", encoding="utf-8")

    result = commit_paths("Add file", ["file.txt"])

    assert result.result_status == "PASS"
    assert result.returncode == 0


def test_transfer_commit_cli_supports_allow_main(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    _acknowledge_rules(tmp_path)
    monkeypatch.chdir(tmp_path)
    (tmp_path / "file.txt").write_text("content\n", encoding="utf-8")

    blocked = CliRunner().invoke(
        app, ["transfer", "commit", "--message", "Add file", "--path", "file.txt"]
    )
    allowed = CliRunner().invoke(
        app, ["transfer", "commit", "--message", "Add file", "--path", "file.txt", "--allow-main"]
    )

    assert blocked.exit_code != 0
    assert "Refusing to commit directly on main" in blocked.stdout
    assert allowed.exit_code == 0


def test_transfer_branch_create_cli(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    _acknowledge_rules(tmp_path)
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(app, ["transfer", "branch-create", "feature/cli"])

    assert result.exit_code == 0
    assert '"action": "branch-create"' in result.stdout
    assert '"result_status": "PASS"' in result.stdout


def test_transfer_commit_cli_requires_path(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    _acknowledge_rules(tmp_path)
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(app, ["transfer", "commit", "--message", "No paths"])

    assert result.exit_code != 0
    assert "No paths supplied" in result.stdout


def test_repo_status_log_and_diff(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    (tmp_path / "changed.txt").write_text("change\n", encoding="utf-8")

    status = repo_status()
    log = repo_log(limit=1)
    diff = repo_diff(name_only=True)

    assert status.result_status == "PASS"
    assert "changed.txt" in status.stdout
    assert log.result_status == "PASS"
    assert "Initial" in log.stdout
    assert diff.result_status == "PASS"


def test_head_sha_short_and_full(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    short = head_sha()
    full = head_sha(full=True)

    assert short.result_status == "PASS"
    assert short.command == ["git", "rev-parse", "--short", "HEAD"]
    assert len(short.stdout.strip()) >= 4
    assert full.result_status == "PASS"
    assert full.command == ["git", "rev-parse", "HEAD"]
    assert len(full.stdout.strip()) == 40
    assert full.stdout.strip().startswith(short.stdout.strip())


def test_fetch_and_pull_current_without_origin_fail_deterministically(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    fetch = fetch_origin("main")
    pull = pull_current()

    assert fetch.result_status == "FAIL"
    assert "origin" in fetch.stderr
    assert pull.result_status == "FAIL"
    assert "origin" in pull.stderr


def test_branch_delete(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    created = branch_create("feature/delete-me", start_point="main")
    switched = branch_switch("main")
    deleted = branch_delete("feature/delete-me")

    assert created.result_status == "PASS"
    assert switched.result_status == "PASS"
    assert deleted.result_status == "PASS"


def test_transfer_repo_status_cli(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(app, ["transfer", "repo-status"])

    assert result.exit_code == 0
    assert '"action": "repo-status"' in result.stdout


def test_transfer_repo_log_cli(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(app, ["transfer", "repo-log", "--limit", "1"])

    assert result.exit_code == 0
    assert '"action": "repo-log"' in result.stdout


def test_transfer_head_sha_cli(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(app, ["transfer", "head-sha"])
    full_result = CliRunner().invoke(app, ["transfer", "head-sha", "--full"])

    assert result.exit_code == 0
    assert '"action": "head-sha"' in result.stdout
    assert '"rev-parse"' in result.stdout
    assert '"--short"' in result.stdout
    assert full_result.exit_code == 0
    assert '"action": "head-sha"' in full_result.stdout
    assert '"--short"' not in full_result.stdout


def test_transfer_branch_delete_cli(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    _acknowledge_rules(tmp_path)
    monkeypatch.chdir(tmp_path)

    created = branch_create("feature/cli-delete", start_point="main")
    assert created.returncode == 0, created.as_json_data()

    switched = subprocess.run(
        ["git", "switch", "main"],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=False,
    )
    assert switched.returncode == 0, {
        "stdout": switched.stdout,
        "stderr": switched.stderr,
    }

    result = CliRunner().invoke(app, ["transfer", "branch-delete", "feature/cli-delete"])

    assert result.exit_code == 0, {
        "stdout": result.stdout,
        "stderr": result.stderr,
        "exception": repr(result.exception),
    }
    assert "\"action\": \"branch-delete\"" in result.stdout


def test_guarded_pr_actions_reject_short_expected_head_sha(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    wait_result = pr_wait_ci(123, expected_head_sha="abc123")
    merge_result = pr_merge_safe(123, expected_head_sha="abc123")

    assert wait_result.result_status == "FAIL"
    assert wait_result.returncode == 2
    assert "full 40-character head SHA" in wait_result.stderr
    assert merge_result.result_status == "FAIL"
    assert merge_result.returncode == 2
    assert "full 40-character head SHA" in merge_result.stderr


def test_result_terminal_adds_final_signal_lines_for_pass_and_fail(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    passing = repo_log(limit=1)
    failing = fetch_origin("main")

    passing_output = result_terminal(passing)
    failing_output = result_terminal(failing)

    assert passing_output.splitlines()[-3:] == [
        "FINAL_SIGNAL=d",
        "FINAL_NEXT=Use commit SHAs for guarded PR or merge work.",
        "CHAT_REPLY=d | NEXT=Use commit SHAs for guarded PR or merge work.",
    ]
    assert failing_output.splitlines()[-3] == "FINAL_SIGNAL=f"
    assert failing_output.splitlines()[-2].startswith("FINAL_NEXT=")
    assert failing_output.splitlines()[-1].startswith("CHAT_REPLY=f | NEXT=")


def test_transfer_repo_log_cli_prints_final_signal_last(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(app, ["transfer", "repo-log", "--limit", "1"])

    assert result.exit_code == 0
    assert result.stdout.splitlines()[-3:] == [
        "FINAL_SIGNAL=d",
        "FINAL_NEXT=Use commit SHAs for guarded PR or merge work.",
        "CHAT_REPLY=d | NEXT=Use commit SHAs for guarded PR or merge work.",
    ]


def test_transfer_branch_create_cli_block_prints_final_signal_last(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(app, ["transfer", "branch-create", "feature/blocked"])

    assert result.exit_code == 2
    assert result.stdout.splitlines()[-3].strip() == "FINAL_SIGNAL=f"
    assert result.stdout.splitlines()[-2].startswith("FINAL_NEXT=")
    assert result.stdout.splitlines()[-1].startswith("CHAT_REPLY=f | NEXT=")


def test_transfer_pr_wait_ci_cli_accepts_interval_seconds_option(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(
        app,
        [
            "transfer",
            "pr-wait-ci",
            "123",
            "--expected-head-sha",
            "abc123",
            "--interval-seconds",
            "1",
        ],
    )

    assert result.exit_code != 0
    assert "full 40-character head SHA" in result.stdout


def test_post_merge_check_noop_on_main(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    calls = []

    def fake_run(command, cwd=None):
        calls.append(command)
        if command == ["git", "branch", "--show-current"]:
            return subprocess.CompletedProcess(command, 0, "main\n", "")
        if command == ["agentic-kit", "handoff", "post-merge-refresh-status"]:
            return subprocess.CompletedProcess(
                command, 0, "POST_MERGE_HANDOFF_REFRESH\nresult=NOOP\n", ""
            )
        return subprocess.CompletedProcess(command, 99, "", "unexpected command\n")

    monkeypatch.setattr("agentic_project_kit.transfer_repo_actions._run", fake_run)
    monkeypatch.setattr(
        "agentic_project_kit.transfer_repo_actions._agentic_kit_command", lambda: "agentic-kit"
    )

    result = post_merge_check(main_branch="main")

    assert result.result_status == "PASS"
    assert result.returncode == 0
    assert result.action == "post-merge-check"
    assert "Continue without administrative handoff refresh" in result.next_action
    assert calls == [
        ["git", "branch", "--show-current"],
        ["agentic-kit", "handoff", "post-merge-refresh-status"],
    ]


def test_post_merge_check_requires_main_branch(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    branch_create("feature/not-main", start_point="main")

    result = post_merge_check(main_branch="main")

    assert result.result_status == "FAIL"
    assert result.returncode == 2
    assert "Expected branch main" in result.stderr


def test_post_merge_check_detects_refresh_required(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    def fake_run(command, cwd=None):
        if command == ["git", "branch", "--show-current"]:
            return subprocess.CompletedProcess(command, 0, "main\n", "")
        if command == ["agentic-kit", "handoff", "post-merge-refresh-status"]:
            return subprocess.CompletedProcess(
                command, 0, "POST_MERGE_HANDOFF_REFRESH\nresult=REFRESH_REQUIRED\n", ""
            )
        return subprocess.CompletedProcess(command, 99, "", "unexpected command\n")

    monkeypatch.setattr("agentic_project_kit.transfer_repo_actions._run", fake_run)
    monkeypatch.setattr(
        "agentic_project_kit.transfer_repo_actions._agentic_kit_command", lambda: "agentic-kit"
    )

    result = post_merge_check(main_branch="main")

    assert result.result_status == "PASS"
    assert result.returncode == 0
    assert "admin-refresh-pr" in result.next_action
    assert "--allow-main" in result.next_action


def test_admin_refresh_pr_creates_branch_and_pr(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    calls = []

    def fake_run(command, cwd=None):
        calls.append(command)
        if command == ["git", "branch", "--show-current"]:
            return subprocess.CompletedProcess(command, 0, "main\n", "")
        if command == ["git", "status", "--short"]:
            status_count = sum(1 for item in calls if item == ["git", "status", "--short"])
            return subprocess.CompletedProcess(
                command, 0, "" if status_count == 1 else " M .agentic/handoff_state.yaml\n", ""
            )
        if command == ["git", "switch", "-c", "docs/post-pr123-handoff-refresh", "main"]:
            return subprocess.CompletedProcess(command, 0, "", "")
        if command == [
            "agentic-kit",
            "handoff",
            "refresh",
            ".agentic/handoff_state.yaml",
            "--write",
        ]:
            return subprocess.CompletedProcess(
                command, 0, "Updated .agentic/handoff_state.yaml\n", ""
            )
        if command == ["agentic-kit", "handoff", "check"]:
            return subprocess.CompletedProcess(
                command, 0, "Persistent handoff state check passed\n", ""
            )
        if command == ["agentic-kit", "handoff", "post-merge-refresh-status"]:
            return subprocess.CompletedProcess(
                command, 0, "POST_MERGE_HANDOFF_REFRESH\nresult=NOOP\n", ""
            )
        if command == ["git", "add", ".agentic/handoff_state.yaml"]:
            return subprocess.CompletedProcess(command, 0, "", "")
        if command == ["git", "commit", "-m", "Refresh handoff state after PR123"]:
            return subprocess.CompletedProcess(
                command, 0, "[branch abc123] Refresh handoff state after PR123\n", ""
            )
        if command == ["git", "push", "-u", "origin", "docs/post-pr123-handoff-refresh"]:
            return subprocess.CompletedProcess(command, 0, "", "")
        if command[:4] == ["gh", "pr", "create", "--base"]:
            return subprocess.CompletedProcess(
                command, 0, "https://github.com/vfi64/agentic-project-kit/pull/999\n", ""
            )
        return subprocess.CompletedProcess(command, 99, "", f"unexpected command: {command}\n")

    monkeypatch.setattr("agentic_project_kit.transfer_repo_actions._run", fake_run)
    monkeypatch.setattr(
        "agentic_project_kit.transfer_repo_actions._agentic_kit_command", lambda: "agentic-kit"
    )

    result = admin_refresh_pr(123)

    assert result.result_status == "PASS"
    assert result.returncode == 0
    assert "docs/post-pr123-handoff-refresh" in result.stdout
    assert "pull/999" in result.stdout


def test_admin_refresh_pr_requires_clean_main(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    def fake_run(command, cwd=None):
        if command == ["git", "branch", "--show-current"]:
            return subprocess.CompletedProcess(command, 0, "main\n", "")
        if command == ["git", "status", "--short"]:
            return subprocess.CompletedProcess(command, 0, " M file.txt\n", "")
        return subprocess.CompletedProcess(command, 99, "", "unexpected command\n")

    monkeypatch.setattr("agentic_project_kit.transfer_repo_actions._run", fake_run)

    result = admin_refresh_pr(123)

    assert result.result_status == "FAIL"
    assert "dirty worktree" in result.stderr


def test_admin_refresh_pr_returns_existing_pr_when_refresh_branch_exists(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    calls = []

    def fake_run(command, cwd=None):
        calls.append(command)
        if command == ["git", "branch", "--show-current"]:
            return subprocess.CompletedProcess(command, 0, "main\n", "")
        if command == ["git", "status", "--short"]:
            return subprocess.CompletedProcess(command, 0, "", "")
        if command == ["git", "switch", "-c", "docs/post-pr123-handoff-refresh", "main"]:
            return subprocess.CompletedProcess(
                command,
                128,
                "",
                "fatal: a branch named 'docs/post-pr123-handoff-refresh' already exists\n",
            )
        if command == [
            "gh",
            "pr",
            "list",
            "--head",
            "docs/post-pr123-handoff-refresh",
            "--state",
            "open",
            "--json",
            "number,url,headRefName,headRefOid,state,title",
        ]:
            return subprocess.CompletedProcess(
                command,
                0,
                '[{"number":999,"url":"https://github.com/vfi64/agentic-project-kit/pull/999","headRefName":"docs/post-pr123-handoff-refresh","headRefOid":"a%s","state":"OPEN","title":"Refresh handoff state after PR123"}]\n'
                % ("a" * 39),
                "",
            )
        return subprocess.CompletedProcess(command, 99, "", f"unexpected command: {command}\n")

    monkeypatch.setattr("agentic_project_kit.transfer_repo_actions._run", fake_run)

    result = admin_refresh_pr(123)

    assert result.result_status == "PASS"
    assert result.returncode == 0
    assert "ADMIN_REFRESH_EXISTING_BRANCH_RECOVERY" in result.stdout
    assert "existing_pr=999" in result.stdout
    assert "pull/999" in result.stdout
    assert "Run transfer pr-status on the existing admin refresh PR" in result.next_action
    assert ["agentic-kit", "handoff", "refresh", ".agentic/handoff_state.yaml", "--write"] not in calls


def test_admin_refresh_pr_fails_when_existing_branch_has_multiple_open_prs(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    def fake_run(command, cwd=None):
        if command == ["git", "branch", "--show-current"]:
            return subprocess.CompletedProcess(command, 0, "main\n", "")
        if command == ["git", "status", "--short"]:
            return subprocess.CompletedProcess(command, 0, "", "")
        if command == ["git", "switch", "-c", "docs/post-pr123-handoff-refresh", "main"]:
            return subprocess.CompletedProcess(
                command,
                128,
                "",
                "fatal: a branch named 'docs/post-pr123-handoff-refresh' already exists\n",
            )
        if command[:6] == ["gh", "pr", "list", "--head", "docs/post-pr123-handoff-refresh", "--state"]:
            return subprocess.CompletedProcess(
                command,
                0,
                '[{"number":998},{"number":999}]\n',
                "",
            )
        return subprocess.CompletedProcess(command, 99, "", f"unexpected command: {command}\n")

    monkeypatch.setattr("agentic_project_kit.transfer_repo_actions._run", fake_run)

    result = admin_refresh_pr(123)

    assert result.result_status == "FAIL"
    assert result.returncode == 2
    assert "Multiple open admin refresh PRs found" in result.stderr


def test_transfer_post_merge_check_cli_help(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(app, ["transfer", "post-merge-check", "--help"])

    assert result.exit_code == 0
    assert "post-merge-check" in result.stdout


def test_transfer_branch_create_cli_blocks_without_rule_acknowledgement(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(app, ["transfer", "branch-create", "feature/blocked"])

    assert result.exit_code == 2
    assert '"required_capability": "rules_confirmed"' in result.stdout
    assert '"result_status": "BLOCKED"' in result.stdout


def test_transfer_branch_delete_cli_blocks_without_rule_acknowledgement(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    branch_create("feature/delete-blocked", start_point="main")
    branch_switch("main")

    result = CliRunner().invoke(app, ["transfer", "branch-delete", "feature/delete-blocked"])

    assert result.exit_code == 2
    assert '"required_capability": "rules_confirmed"' in result.stdout
    assert '"result_status": "BLOCKED"' in result.stdout

def test_pr_wait_ci_auto_resolves_head_sha_when_omitted(monkeypatch):
    calls = []

    def fake_run(command, cwd=None):
        calls.append(command)
        if command == ["gh", "pr", "view", "123", "--json", "headRefOid", "--jq", ".headRefOid"]:
            return subprocess.CompletedProcess(command, 0, "a" * 40 + "\n", "")
        if command[:4] == ["agentic-kit", "pr", "wait-ci", "123"]:
            return subprocess.CompletedProcess(command, 0, "ready\n", "")
        return subprocess.CompletedProcess(command, 99, "", f"unexpected command: {command}\n")

    monkeypatch.setattr("agentic_project_kit.transfer_repo_actions._run", fake_run)
    monkeypatch.setattr(
        "agentic_project_kit.transfer_repo_actions._agentic_kit_command",
        lambda: "agentic-kit",
    )

    from agentic_project_kit.transfer_repo_actions import pr_wait_ci

    result = pr_wait_ci(123, timeout_seconds=5, poll_seconds=1)

    assert result.result_status == "PASS"
    assert result.returncode == 0
    assert ["gh", "pr", "view", "123", "--json", "headRefOid", "--jq", ".headRefOid"] in calls
    assert ["--expected-head-sha", "a" * 40] == calls[-1][-2:]


def test_pr_merge_safe_auto_resolves_head_sha_when_omitted(monkeypatch):
    calls = []

    class PassingMonitor:
        decision = transfer_repo_actions.MonitorDecision.CONTINUE
        actual_branch = "main"
        required_branch = "main"
        reason = "test_monitor_pass"

    def fake_guard_branch(**kwargs):
        calls.append(["guard_branch", kwargs])
        return PassingMonitor()

    def fake_run(command, cwd=None):
        calls.append(command)
        if command == ["gh", "pr", "view", "123", "--json", "headRefOid", "--jq", ".headRefOid"]:
            return subprocess.CompletedProcess(command, 0, "b" * 40 + "\n", "")
        if command[:4] == ["agentic-kit", "pr", "merge-if-green", "123"]:
            return subprocess.CompletedProcess(command, 0, "merged\n", "")
        return subprocess.CompletedProcess(command, 99, "", f"unexpected command: {command}\n")

    monkeypatch.setattr("agentic_project_kit.transfer_repo_actions.guard_branch", fake_guard_branch)
    monkeypatch.setattr("agentic_project_kit.transfer_repo_actions._run", fake_run)
    monkeypatch.setattr(
        "agentic_project_kit.transfer_repo_actions._agentic_kit_command",
        lambda: "agentic-kit",
    )

    from agentic_project_kit.transfer_repo_actions import pr_merge_safe

    result = pr_merge_safe(123, expected_head_sha="", main_branch="main", merge_method="squash")

    assert result.result_status == "PASS"
    assert result.returncode == 0
    assert ["gh", "pr", "view", "123", "--json", "headRefOid", "--jq", ".headRefOid"] in calls
    assert ["--expected-head-sha", "b" * 40] == calls[-1][4:6]


def test_pr_wait_ci_auto_sha_failure_fails_closed(monkeypatch):
    def fake_run(command, cwd=None):
        if command == ["gh", "pr", "view", "123", "--json", "headRefOid", "--jq", ".headRefOid"]:
            return subprocess.CompletedProcess(command, 1, "", "network failure\n")
        return subprocess.CompletedProcess(command, 99, "", f"unexpected command: {command}\n")

    monkeypatch.setattr("agentic_project_kit.transfer_repo_actions._run", fake_run)

    from agentic_project_kit.transfer_repo_actions import pr_wait_ci

    result = pr_wait_ci(123)

    assert result.result_status == "FAIL"
    assert result.returncode == 1
    assert "network failure" in result.stderr
    assert "PR head SHA lookup failure" in result.next_action

def test_transfer_pr_merge_safe_cli_allows_omitted_expected_head_sha(monkeypatch):
    from agentic_project_kit.transfer_repo_actions import RepoActionResult

    calls = []

    def fake_require(capability):
        calls.append(("capability", capability))

    def fake_pr_merge_safe(
        pr_number,
        *,
        expected_head_sha="",
        main_branch="main",
        merge_method="squash",
        no_verify_main=False,
        merge_state_timeout_seconds=60,
        merge_state_poll_seconds=5,
    ):
        calls.append(
            (
                pr_number,
                expected_head_sha,
                main_branch,
                merge_method,
                no_verify_main,
                merge_state_timeout_seconds,
                merge_state_poll_seconds,
            )
        )
        return RepoActionResult(
            action="pr-merge-safe",
            result_status="PASS",
            returncode=0,
            command=["fake"],
            stdout="merged\n",
            stderr="",
            next_action="Sync main and run post-merge handoff refresh status.",
        )

    monkeypatch.setattr(
        "agentic_project_kit.cli_commands.transfer._require_transfer_capability",
        fake_require,
    )
    monkeypatch.setattr(
        "agentic_project_kit.cli_commands.transfer.pr_merge_safe",
        fake_pr_merge_safe,
    )

    result = CliRunner().invoke(app, ["transfer", "pr-merge-safe", "123"])

    assert result.exit_code == 0
    assert calls == [
        ("capability", "rules_confirmed"),
        (123, "", "main", "squash", False, 60, 5),
    ]


def test_transfer_pr_wait_ci_cli_quiet_report_prints_only_go_lines(tmp_path, monkeypatch):
    from typer.testing import CliRunner
    from agentic_project_kit.cli import app

    monkeypatch.chdir(tmp_path)

    def fake_pr_wait_ci(pr_number, *, expected_head_sha="", timeout_seconds=300, poll_seconds=10):
        from agentic_project_kit.transfer_repo_actions import RepoActionResult
        return RepoActionResult(
            action="pr-wait-ci",
            result_status="PASS",
            returncode=0,
            command=["fake", "wait-ci", str(pr_number)],
            stdout="PR readiness outcome: READY_TO_MERGE\\nterminal=true\\nsuccess=true\\n",
            stderr="",
            next_action="Run transfer pr-status or merge-if-green after CI is green.",
        )

    monkeypatch.setattr("agentic_project_kit.cli_commands.transfer.pr_wait_ci", fake_pr_wait_ci)

    result = CliRunner().invoke(
        app,
        ["transfer", "pr-wait-ci", "123", "--quiet-report"],
    )

    assert result.exit_code == 0
    lines = result.stdout.splitlines()
    assert lines[0] == "TRANSFER_UPLOAD=done"
    assert lines[1].startswith("REMOTE_REPORT=docs/reports/transfer_runs/")
    assert lines[2] == "CHAT_REPLY=g"
    assert len(lines) == 3

    report_path = lines[1].split("=", 1)[1]
    report = (tmp_path / report_path).read_text(encoding="utf-8")
    assert "READY_TO_MERGE" in report
    assert "pr-wait-ci" in report


def test_transfer_pr_wait_ci_cli_quiet_report_still_exits_nonzero_on_failure(tmp_path, monkeypatch):
    from typer.testing import CliRunner
    from agentic_project_kit.cli import app

    monkeypatch.chdir(tmp_path)

    def fake_pr_wait_ci(pr_number, *, expected_head_sha="", timeout_seconds=300, poll_seconds=10):
        from agentic_project_kit.transfer_repo_actions import RepoActionResult
        return RepoActionResult(
            action="pr-wait-ci",
            result_status="FAIL",
            returncode=1,
            command=["fake", "wait-ci", str(pr_number)],
            stdout="PR readiness outcome: NOT_READY\\n",
            stderr="pending checks remain\\n",
            next_action="Inspect failed or pending PR status before merge.",
        )

    monkeypatch.setattr("agentic_project_kit.cli_commands.transfer.pr_wait_ci", fake_pr_wait_ci)

    result = CliRunner().invoke(
        app,
        ["transfer", "pr-wait-ci", "123", "--quiet-report"],
    )

    assert result.exit_code == 1
    lines = result.stdout.splitlines()
    assert lines[0] == "TRANSFER_UPLOAD=done"
    assert lines[1].startswith("REMOTE_REPORT=docs/reports/transfer_runs/")
    assert lines[2] == "CHAT_REPLY=g"
    assert len(lines) == 3

    report_path = lines[1].split("=", 1)[1]
    report = (tmp_path / report_path).read_text(encoding="utf-8")
    assert "NOT_READY" in report
    assert "pending checks remain" in report

def test_commit_paths_refuses_branch_drift_between_add_and_commit(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    subprocess.run(["git", "init", "-b", "main"], check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], check=True)
    Path("file.txt").write_text("demo\n", encoding="utf-8")
    subprocess.run(["git", "add", "file.txt"], check=True)
    subprocess.run(["git", "commit", "-m", "Initial"], check=True)
    subprocess.run(["git", "switch", "-c", "feature/demo"], check=True)

    calls = {"branch": 0}
    original_run = transfer_repo_actions._run

    def drifting_run(command, *, cwd=None):
        if command == ["git", "branch", "--show-current"]:
            calls["branch"] += 1
            branch = "feature/demo" if calls["branch"] == 1 else "main"
            return subprocess.CompletedProcess(command, 0, branch + "\n", "")
        return original_run(command, cwd=cwd)

    monkeypatch.setattr(transfer_repo_actions, "_run", drifting_run)

    Path("file.txt").write_text("changed\n", encoding="utf-8")
    result = commit_paths("Change file", ["file.txt"])

    assert result.returncode == 2
    assert "current branch changed during transfer commit" in result.stderr
    assert result.next_action == "Inspect branch drift before committing."

def test_branch_create_refuses_branch_drift_after_create(monkeypatch):
    calls = []

    class PassingMonitor:
        decision = transfer_repo_actions.MonitorDecision.CONTINUE
        actual_branch = "main"
        required_branch = "main"
        reason = "test_monitor_pass"

    def fake_guard_branch(**kwargs):
        calls.append(["guard_branch", kwargs])
        return PassingMonitor()

    def fake_run(command, cwd=None):
        calls.append(command)
        if command == ["git", "switch", "-c", "feature/drift", "main"]:
            return subprocess.CompletedProcess(command, 0, "", "")
        if command == ["git", "branch", "--show-current"]:
            return subprocess.CompletedProcess(command, 0, "main\n", "")
        return subprocess.CompletedProcess(command, 99, "", f"unexpected command: {command}\n")

    monkeypatch.setattr(transfer_repo_actions, "guard_branch", fake_guard_branch)
    monkeypatch.setattr(transfer_repo_actions, "_run", fake_run)

    result = branch_create("feature/drift", start_point="main")

    assert result.returncode == 2
    assert result.result_status == "FAIL"
    assert "current branch drifted" in result.stderr
    assert result.next_action == "Inspect branch drift before continuing."
    assert ["git", "push", "-u", "origin", "feature/drift"] not in calls


def test_branch_switch_refuses_branch_drift_after_pull(monkeypatch):
    calls = {"branch": 0}

    class PassingMonitor:
        decision = transfer_repo_actions.MonitorDecision.CONTINUE
        actual_branch = "feature/drift"
        required_branch = "feature/drift"
        reason = "test_monitor_pass"

    def fake_guard_branch(**kwargs):
        return PassingMonitor()

    def fake_run(command, cwd=None):
        if command == ["git", "switch", "feature/drift"]:
            return subprocess.CompletedProcess(command, 0, "", "")
        if command == ["git", "pull", "--ff-only", "origin", "feature/drift"]:
            return subprocess.CompletedProcess(command, 0, "Already up to date.\n", "")
        if command == ["git", "branch", "--show-current"]:
            calls["branch"] += 1
            branch = "feature/drift" if calls["branch"] == 1 else "main"
            return subprocess.CompletedProcess(command, 0, branch + "\n", "")
        return subprocess.CompletedProcess(command, 99, "", f"unexpected command: {command}\n")

    monkeypatch.setattr(transfer_repo_actions, "guard_branch", fake_guard_branch)
    monkeypatch.setattr(transfer_repo_actions, "_run", fake_run)

    result = branch_switch("feature/drift", pull=True)

    assert result.returncode == 2
    assert result.result_status == "FAIL"
    assert "current branch drifted" in result.stderr
    assert result.next_action == "Inspect branch drift before continuing."


def test_push_current_refuses_branch_drift_after_push(monkeypatch):
    calls = {"branch": 0}

    class PassingMonitor:
        decision = transfer_repo_actions.MonitorDecision.CONTINUE
        actual_branch = "feature/demo"
        required_branch = "feature/demo"
        reason = "test_monitor_pass"

    def fake_guard_branch(**kwargs):
        return PassingMonitor()

    def fake_run(command, cwd=None):
        if command == ["git", "branch", "--show-current"]:
            calls["branch"] += 1
            branch = "feature/demo" if calls["branch"] == 1 else "main"
            return subprocess.CompletedProcess(command, 0, branch + "\n", "")
        if command == ["git", "push", "-u", "origin", "feature/demo"]:
            return subprocess.CompletedProcess(command, 0, "pushed\n", "")
        return subprocess.CompletedProcess(command, 99, "", f"unexpected command: {command}\n")

    monkeypatch.setattr(transfer_repo_actions, "guard_branch", fake_guard_branch)
    monkeypatch.setattr(transfer_repo_actions, "_run", fake_run)

    result = push_current()

    assert result.returncode == 2
    assert result.result_status == "FAIL"
    assert "current branch drifted" in result.stderr
    assert result.next_action == "Inspect branch drift before continuing."



def test_push_current_refuses_main_without_monitor_allowance(monkeypatch):
    def fake_run(command, cwd=None):
        if command == ["git", "branch", "--show-current"]:
            return subprocess.CompletedProcess(command, 0, "main\n", "")
        return subprocess.CompletedProcess(command, 99, "", f"unexpected command: {command}\n")

    monkeypatch.setattr(transfer_repo_actions, "_run", fake_run)

    result = push_current()

    assert result.returncode == 2
    assert result.result_status == "FAIL"
    assert "Transfer operation monitor blocked push-current" in result.stderr
    assert "main_mutation_not_allowed" in result.stderr


def test_pr_create_blocks_head_equal_base_before_gh_call(monkeypatch):
    calls = []

    def fake_run(command, cwd=None):
        calls.append(command)
        return subprocess.CompletedProcess(command, 99, "", f"unexpected command: {command}\n")

    monkeypatch.setattr(transfer_repo_actions, "_run", fake_run)

    result = transfer_repo_actions.pr_create(base="main", head="main", title="Bad PR", body="bad")

    assert result.returncode == 2
    assert result.result_status == "FAIL"
    assert "pr_create_head_equals_base" in result.stderr
    assert not any(command[:3] == ["gh", "pr", "create"] for command in calls)


def test_push_current_with_required_branch_switches_before_push(monkeypatch):
    calls = []

    class SwitchMonitor:
        decision = transfer_repo_actions.MonitorDecision.SWITCH
        actual_branch = "feature/demo"
        required_branch = "feature/demo"
        reason = "switched_to_required_branch"

    def fake_guard_branch(**kwargs):
        calls.append(["guard_branch", kwargs])
        return SwitchMonitor()

    def fake_run(command, cwd=None):
        calls.append(command)
        if command == ["git", "branch", "--show-current"]:
            return subprocess.CompletedProcess(command, 0, "feature/demo\n", "")
        if command == ["git", "push", "-u", "origin", "feature/demo"]:
            return subprocess.CompletedProcess(command, 0, "pushed\n", "")
        return subprocess.CompletedProcess(command, 99, "", f"unexpected command: {command}\n")

    monkeypatch.setattr(transfer_repo_actions, "guard_branch", fake_guard_branch)
    monkeypatch.setattr(transfer_repo_actions, "_run", fake_run)

    result = transfer_repo_actions.push_current(required_branch="feature/demo")

    assert result.returncode == 0
    assert result.result_status == "PASS"
    assert ["git", "push", "-u", "origin", "feature/demo"] in calls


def test_push_current_with_required_branch_blocks_before_push(monkeypatch):
    calls = []

    class BlockMonitor:
        decision = transfer_repo_actions.MonitorDecision.BLOCK
        actual_branch = "main"
        required_branch = "feature/demo"
        reason = "dirty_worktree_blocks_branch_switch"

    def fake_guard_branch(**kwargs):
        calls.append(["guard_branch", kwargs])
        return BlockMonitor()

    def fake_run(command, cwd=None):
        calls.append(command)
        return subprocess.CompletedProcess(command, 99, "", f"unexpected command: {command}\n")

    monkeypatch.setattr(transfer_repo_actions, "guard_branch", fake_guard_branch)
    monkeypatch.setattr(transfer_repo_actions, "_run", fake_run)

    result = transfer_repo_actions.push_current(required_branch="feature/demo")

    assert result.returncode == 2
    assert result.result_status == "FAIL"
    assert "Transfer operation monitor blocked push-current" in result.stderr
    assert ["git", "push", "-u", "origin", "feature/demo"] not in calls


def test_commit_paths_with_required_branch_switches_before_add(monkeypatch):
    calls = []

    class SwitchMonitor:
        decision = transfer_repo_actions.MonitorDecision.SWITCH
        actual_branch = "feature/demo"
        required_branch = "feature/demo"
        reason = "switched_to_required_branch"

    def fake_guard_branch(**kwargs):
        calls.append(["guard_branch", kwargs])
        return SwitchMonitor()

    def fake_run(command, cwd=None):
        calls.append(command)
        if command == ["git", "branch", "--show-current"]:
            return subprocess.CompletedProcess(command, 0, "feature/demo\n", "")
        if command == ["git", "add", "file.txt"]:
            return subprocess.CompletedProcess(command, 0, "", "")
        if command == ["git", "commit", "-m", "Commit on feature"]:
            return subprocess.CompletedProcess(command, 0, "committed\n", "")
        return subprocess.CompletedProcess(command, 99, "", f"unexpected command: {command}\n")

    monkeypatch.setattr(transfer_repo_actions, "guard_branch", fake_guard_branch)
    monkeypatch.setattr(transfer_repo_actions, "_run", fake_run)

    result = transfer_repo_actions.commit_paths(
        "Commit on feature",
        ["file.txt"],
        required_branch="feature/demo",
    )

    assert result.returncode == 0
    assert calls[0][0] == "guard_branch"
    assert ["git", "add", "file.txt"] in calls
    assert ["git", "commit", "-m", "Commit on feature"] in calls


def test_commit_paths_with_required_branch_blocks_before_add(monkeypatch):
    calls = []

    class BlockMonitor:
        decision = transfer_repo_actions.MonitorDecision.BLOCK
        actual_branch = "main"
        required_branch = "feature/demo"
        reason = "dirty_worktree_blocks_branch_switch"

    def fake_guard_branch(**kwargs):
        calls.append(["guard_branch", kwargs])
        return BlockMonitor()

    def fake_run(command, cwd=None):
        calls.append(command)
        return subprocess.CompletedProcess(command, 99, "", f"unexpected command: {command}\n")

    monkeypatch.setattr(transfer_repo_actions, "guard_branch", fake_guard_branch)
    monkeypatch.setattr(transfer_repo_actions, "_run", fake_run)

    result = transfer_repo_actions.commit_paths(
        "Blocked commit",
        ["file.txt"],
        required_branch="feature/demo",
    )

    assert result.returncode == 2
    assert result.result_status == "FAIL"
    assert "Transfer operation monitor blocked commit" in result.stderr
    assert ["git", "add", "file.txt"] not in calls


def test_branch_create_monitor_switches_to_start_point_before_create(monkeypatch):
    calls = []

    class SwitchMonitor:
        decision = transfer_repo_actions.MonitorDecision.SWITCH
        actual_branch = "main"
        required_branch = "main"
        reason = "switched_to_required_branch"

    def fake_guard_branch(**kwargs):
        calls.append(["guard_branch", kwargs])
        return SwitchMonitor()

    def fake_run(command, cwd=None):
        calls.append(command)
        if command == ["git", "switch", "-c", "feature/demo", "main"]:
            return subprocess.CompletedProcess(command, 0, "", "")
        if command == ["git", "branch", "--show-current"]:
            return subprocess.CompletedProcess(command, 0, "feature/demo\n", "")
        return subprocess.CompletedProcess(command, 99, "", f"unexpected command: {command}\n")

    monkeypatch.setattr(transfer_repo_actions, "guard_branch", fake_guard_branch)
    monkeypatch.setattr(transfer_repo_actions, "_run", fake_run)

    result = transfer_repo_actions.branch_create("feature/demo", start_point="main")

    assert result.returncode == 0
    assert calls[0][0] == "guard_branch"
    assert calls[0][1]["required_branch"] == "main"
    assert ["git", "switch", "-c", "feature/demo", "main"] in calls


def test_branch_create_monitor_blocks_before_create(monkeypatch):
    calls = []

    class BlockMonitor:
        decision = transfer_repo_actions.MonitorDecision.BLOCK
        actual_branch = "feature/dirty"
        required_branch = "main"
        reason = "dirty_worktree_blocks_branch_switch"

    def fake_guard_branch(**kwargs):
        calls.append(["guard_branch", kwargs])
        return BlockMonitor()

    def fake_run(command, cwd=None):
        calls.append(command)
        return subprocess.CompletedProcess(command, 99, "", f"unexpected command: {command}\n")

    monkeypatch.setattr(transfer_repo_actions, "guard_branch", fake_guard_branch)
    monkeypatch.setattr(transfer_repo_actions, "_run", fake_run)

    result = transfer_repo_actions.branch_create("feature/demo", start_point="main")

    assert result.returncode == 2
    assert "Transfer operation monitor blocked branch-create" in result.stderr
    assert ["git", "switch", "-c", "feature/demo", "main"] not in calls


def test_branch_switch_monitor_blocks_before_switch(monkeypatch):
    calls = []

    class BlockMonitor:
        decision = transfer_repo_actions.MonitorDecision.BLOCK
        actual_branch = "main"
        required_branch = "feature/demo"
        reason = "dirty_worktree_blocks_branch_switch"

    def fake_guard_branch(**kwargs):
        calls.append(["guard_branch", kwargs])
        return BlockMonitor()

    def fake_run(command, cwd=None):
        calls.append(command)
        return subprocess.CompletedProcess(command, 99, "", f"unexpected command: {command}\n")

    monkeypatch.setattr(transfer_repo_actions, "guard_branch", fake_guard_branch)
    monkeypatch.setattr(transfer_repo_actions, "_run", fake_run)

    result = transfer_repo_actions.branch_switch("feature/demo")

    assert result.returncode == 2
    assert "Transfer operation monitor blocked branch-switch" in result.stderr
    assert ["git", "switch", "feature/demo"] not in calls


def test_pr_merge_safe_monitor_blocks_before_sha_lookup(monkeypatch):
    calls = []

    class BlockMonitor:
        decision = transfer_repo_actions.MonitorDecision.BLOCK
        actual_branch = "feature/work"
        required_branch = "main"
        reason = "dirty_worktree_blocks_branch_switch"

    def fake_guard_branch(**kwargs):
        calls.append(["guard_branch", kwargs])
        return BlockMonitor()

    def fake_run(command, cwd=None):
        calls.append(command)
        return subprocess.CompletedProcess(command, 99, "", f"unexpected command: {command}\n")

    monkeypatch.setattr(transfer_repo_actions, "guard_branch", fake_guard_branch)
    monkeypatch.setattr(transfer_repo_actions, "_run", fake_run)

    result = transfer_repo_actions.pr_merge_safe(123, expected_head_sha="", main_branch="main")

    assert result.returncode == 2
    assert result.result_status == "FAIL"
    assert "Transfer operation monitor blocked pr-merge-safe" in result.stderr
    assert ["gh", "pr", "view", "123", "--json", "headRefOid", "--jq", ".headRefOid"] not in calls


def test_admin_refresh_pr_monitor_blocks_before_status(monkeypatch):
    calls = []

    class BlockMonitor:
        decision = transfer_repo_actions.MonitorDecision.BLOCK
        actual_branch = "feature/work"
        required_branch = "main"
        reason = "dirty_worktree_blocks_branch_switch"

    def fake_guard_branch(**kwargs):
        calls.append(["guard_branch", kwargs])
        return BlockMonitor()

    def fake_run(command, cwd=None):
        calls.append(command)
        return subprocess.CompletedProcess(command, 99, "", f"unexpected command: {command}\n")

    monkeypatch.setattr(transfer_repo_actions, "guard_branch", fake_guard_branch)
    monkeypatch.setattr(transfer_repo_actions, "_run", fake_run)

    result = transfer_repo_actions.admin_refresh_pr(123, main_branch="main")

    assert result.returncode == 2
    assert result.result_status == "FAIL"
    assert "Transfer operation monitor blocked admin-refresh-pr" in result.stderr
    assert ["git", "status", "--short"] not in calls


def test_transfer_protected_diff_plan_runs_diff_and_ns(monkeypatch):
    calls: list[list[str]] = []

    def fake_run(argv, *args, **kwargs):
        command = list(argv)
        calls.append(command)
        if command[:2] == ["git", "diff"]:
            return subprocess.CompletedProcess(command, 0, "", "")
        if command[:2] == ["./ns", "protected-change-plan"]:
            return subprocess.CompletedProcess(command, 0, "PROTECTED_CHANGE_PLAN\nresult=PASS\n", "")
        return subprocess.CompletedProcess(command, 99, "", f"unexpected command: {command}\n")

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = CliRunner().invoke(app, ["transfer", "protected-diff-plan", "--label", "demo"])

    assert result.exit_code == 0
    assert "TRANSFER_PROTECTED_DIFF_PLAN" in result.stdout
    assert "PASS" in result.stdout
    assert calls[0][:2] == ["git", "diff"]
    assert "--output" in calls[0]
    assert calls[1][:2] == ["./ns", "protected-change-plan"]


def test_transfer_protected_diff_plan_blocks_on_ns_failure(monkeypatch):
    def fake_run(argv, *args, **kwargs):
        command = list(argv)
        if command[:2] == ["git", "diff"]:
            return subprocess.CompletedProcess(command, 0, "", "")
        if command[:2] == ["./ns", "protected-change-plan"]:
            return subprocess.CompletedProcess(command, 1, "result=BLOCK\n", "")
        return subprocess.CompletedProcess(command, 99, "", f"unexpected command: {command}\n")

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = CliRunner().invoke(app, ["transfer", "protected-diff-plan", "--label", "demo"])

    assert result.exit_code == 1
    assert "TRANSFER_PROTECTED_DIFF_PLAN" in result.stdout
    assert "FAIL" in result.stdout


def test_transfer_conflict_status_reports_clean_state(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".git").mkdir()

    def fake_run(argv, *args, **kwargs):
        command = list(argv)
        if command == ["git", "branch", "--show-current"]:
            return subprocess.CompletedProcess(command, 0, "feature/demo\n", "")
        if command == ["git", "status", "--short"]:
            return subprocess.CompletedProcess(command, 0, "", "")
        if command == ["git", "diff", "--name-only", "--diff-filter=U"]:
            return subprocess.CompletedProcess(command, 0, "", "")
        return subprocess.CompletedProcess(command, 99, "", f"unexpected command: {command}\n")

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = CliRunner().invoke(app, ["transfer", "conflict-status"])

    assert result.exit_code == 0
    assert "TRANSFER_CONFLICT_STATUS" in result.stdout
    assert "CONFLICT:" in result.stdout
    assert "no" in result.stdout


def test_transfer_conflict_status_blocks_when_unmerged_files_exist(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".git").mkdir()

    def fake_run(argv, *args, **kwargs):
        command = list(argv)
        if command == ["git", "branch", "--show-current"]:
            return subprocess.CompletedProcess(command, 0, "feature/demo\n", "")
        if command == ["git", "status", "--short"]:
            return subprocess.CompletedProcess(command, 0, "UU file.txt\n", "")
        if command == ["git", "diff", "--name-only", "--diff-filter=U"]:
            return subprocess.CompletedProcess(command, 0, "file.txt\n", "")
        return subprocess.CompletedProcess(command, 99, "", f"unexpected command: {command}\n")

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = CliRunner().invoke(app, ["transfer", "conflict-status"])

    assert result.exit_code == 2
    assert "TRANSFER_CONFLICT_STATUS" in result.stdout
    assert "CONFLICT:" in result.stdout
    assert "yes" in result.stdout
    assert "file.txt" in result.stdout
