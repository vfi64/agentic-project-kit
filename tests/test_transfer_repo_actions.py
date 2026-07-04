from __future__ import annotations

import json
import subprocess
import sys

from typer.testing import CliRunner

from agentic_project_kit.cli import app
import agentic_project_kit.transfer_repo_actions as transfer_repo_actions
from agentic_project_kit.cli_commands import transfer as transfer_commands
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
    assert "TRANSFER_BRANCH_CREATE" in result.stdout
    assert '"action": "branch-create"' not in result.stdout
    assert "STATE:" in result.stdout
    assert "PASS" in result.stdout


def test_transfer_list_refs_returns_tags_newest_first(monkeypatch):
    calls: list[list[str]] = []

    def fake_run(argv, *args, **kwargs):
        command = list(argv)
        calls.append(command)
        if command == ["git", "tag", "--sort=-creatordate"]:
            return subprocess.CompletedProcess(command, 0, "v0.4.11\nv0.4.10\nnot-a-release\n", "")
        if command == ["git", "branch", "--format=%(refname:short)"]:
            return subprocess.CompletedProcess(command, 0, "main\ncodex/demo\n", "")
        if command == ["git", "branch", "-r", "--format=%(refname:short)"]:
            return subprocess.CompletedProcess(command, 0, "origin/main\norigin/codex/demo\n", "")
        return subprocess.CompletedProcess(command, 99, "", f"unexpected command: {command}\n")

    monkeypatch.setattr(transfer_commands.subprocess, "run", fake_run)

    result = CliRunner().invoke(app, ["transfer", "list-refs", "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["result_status"] == "PASS"
    assert payload["default_ref"] == "main"
    assert payload["tags"] == ["v0.4.11", "v0.4.10"]
    assert payload["branches"] == ["main", "codex/demo"]
    assert payload["remote_branches"] == ["origin/main", "origin/codex/demo"]


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
    assert "TRANSFER_REPO_STATUS" in result.stdout
    assert '"action": "repo-status"' not in result.stdout


def test_transfer_repo_log_cli(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(app, ["transfer", "repo-log", "--limit", "1"])

    assert result.exit_code == 0
    assert "TRANSFER_REPO_LOG" in result.stdout
    assert '"action": "repo-log"' not in result.stdout


def test_transfer_head_sha_cli(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(app, ["transfer", "head-sha"])
    full_result = CliRunner().invoke(app, ["transfer", "head-sha", "--full"])

    assert result.exit_code == 0
    assert "TRANSFER_HEAD_SHA" in result.stdout
    assert '"action": "head-sha"' not in result.stdout
    assert "COMMAND" in result.stdout
    assert "rev-parse" in result.stdout
    assert "--short" in result.stdout
    assert full_result.exit_code == 0
    assert "TRANSFER_HEAD_SHA" in full_result.stdout
    assert '"action": "head-sha"' not in full_result.stdout
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
    assert "TRANSFER_BRANCH_DELETE" in result.stdout
    assert "\"action\": \"branch-delete\"" not in result.stdout


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


def test_result_terminal_renders_compact_summary_for_pass_and_fail(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    passing = repo_log(limit=1)
    failing = fetch_origin("main")

    passing_output = result_terminal(passing)
    failing_output = result_terminal(failing)

    assert "START SUMMARY" in passing_output
    assert "TRANSFER_REPO_LOG" in passing_output
    assert "STATE:" in passing_output
    assert "PASS" in passing_output
    assert "CHAT_REPLY:" in passing_output
    assert "d | NEXT=Use commit SHAs for guarded PR or merge work." in passing_output
    assert "FINAL_SIGNAL=d" not in passing_output
    assert '"action": "repo-log"' not in passing_output

    assert "START SUMMARY" in failing_output
    assert "TRANSFER_FETCH_ORIGIN" in failing_output
    assert "STATE:" in failing_output
    assert "FAIL" in failing_output
    assert "CHAT_REPLY:" in failing_output
    assert "f | NEXT=" in failing_output
    assert "FINAL_SIGNAL=f" not in failing_output
    assert '"action": "fetch-origin"' not in failing_output

def test_transfer_repo_log_cli_prints_compact_summary(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(app, ["transfer", "repo-log", "--limit", "1"])

    assert result.exit_code == 0
    assert "START SUMMARY" in result.stdout
    assert "TRANSFER_REPO_LOG" in result.stdout
    assert "CHAT_REPLY:" in result.stdout
    assert "d | NEXT=Use commit SHAs for guarded PR or merge work." in result.stdout
    assert "FINAL_SIGNAL=d" not in result.stdout
    assert '"action": "repo-log"' not in result.stdout

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
        if command == ["git", "ls-remote", "--exit-code", "origin", "HEAD"]:
            return subprocess.CompletedProcess(command, 0, "ref\tHEAD\n", "")
        if command == ["git", "branch", "--show-current"]:
            return subprocess.CompletedProcess(command, 0, "main\n", "")
        if command == ["agentic-kit", "handoff", "post-merge-refresh-status"]:
            return subprocess.CompletedProcess(
                command, 0, "POST_MERGE_HANDOFF_REFRESH\nresult=NOOP\n", ""
            )
        if command == ["agentic-kit", "transfer", "prepare-successor-handoff", "--render-prompt"]:
            return subprocess.CompletedProcess(command, 0, "fresh successor prompt\n", "")
        if command == ["agentic-kit", "boot", "write"]:
            return subprocess.CompletedProcess(command, 0, "Wrote docs/handoff/NEXT_CHAT_BOOTSTRAP.md\n", "")
        return subprocess.CompletedProcess(command, 99, "", "unexpected command\n")

    monkeypatch.setattr("agentic_project_kit.transfer_repo_actions._run", fake_run)
    monkeypatch.setattr(
        "agentic_project_kit.transfer_repo_actions._agentic_kit_command", lambda: "agentic-kit"
    )

    result = post_merge_check(main_branch="main")

    assert result.result_status == "PASS"
    assert result.returncode == 0
    assert result.action == "post-merge-check"
    assert "STATE=READY" in result.next_action
    assert "NEXT=none" in result.next_action
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
    assert "STATE=NEEDS_HANDOFF_REFRESH" in result.next_action
    assert "NEXT=refresh_handoff_state" in result.next_action


def test_post_merge_check_classifies_stale_successor_package(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    def fake_run(command, cwd=None):
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
    monkeypatch.setattr(
        "agentic_project_kit.transfer_repo_actions._successor_package_freshness_findings",
        lambda: ["validation_report.json generated_head does not match HEAD or refresh-only ancestry"],
    )

    result = post_merge_check(main_branch="main")

    assert result.result_status == "FAIL"
    assert result.returncode == 1
    assert "STATE=NEEDS_SUCCESSOR_PACKAGE_REFRESH" in result.next_action
    assert "NEXT=refresh_successor_package" in result.next_action
    assert "validation_report.json generated_head" in result.stdout


def test_post_merge_check_reports_refresh_only_successor_package_evidence(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    def fake_run(command, cwd=None):
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
    monkeypatch.setattr(
        "agentic_project_kit.transfer_repo_actions._successor_package_freshness_findings",
        lambda: [],
    )
    monkeypatch.setattr(
        "agentic_project_kit.transfer_repo_actions._successor_package_freshness_notes",
        lambda: [
            "successor_package_head_status=refresh_only_descendant",
            "successor_package_generated_head=f96380798db1f11406889c476252ac54a53f8506",
            "successor_package_current_head=a0ba8f99d8aaf121694c62ef8d607361bb982140",
        ],
    )

    result = post_merge_check(main_branch="main")

    assert result.result_status == "PASS"
    assert result.returncode == 0
    assert "STATE=READY" in result.next_action
    assert "successor_package_head_status=refresh_only_descendant" in result.stdout
    assert (
        "successor_package_generated_head=f96380798db1f11406889c476252ac54a53f8506"
        in result.stdout
    )
    assert (
        "successor_package_current_head=a0ba8f99d8aaf121694c62ef8d607361bb982140"
        in result.stdout
    )


def test_post_merge_check_classifies_unexpected_refresh_status_output(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    def fake_run(command, cwd=None):
        if command == ["git", "branch", "--show-current"]:
            return subprocess.CompletedProcess(command, 0, "main\n", "")
        if command == ["agentic-kit", "handoff", "post-merge-refresh-status"]:
            return subprocess.CompletedProcess(
                command, 0, "POST_MERGE_HANDOFF_REFRESH\nresult=UNKNOWN\n", ""
            )
        return subprocess.CompletedProcess(command, 99, "", "unexpected command\n")

    monkeypatch.setattr("agentic_project_kit.transfer_repo_actions._run", fake_run)
    monkeypatch.setattr(
        "agentic_project_kit.transfer_repo_actions._agentic_kit_command", lambda: "agentic-kit"
    )

    result = post_merge_check(main_branch="main")

    assert result.result_status == "PASS"
    assert result.returncode == 0
    assert "STATE=BLOCKED" in result.next_action
    assert "NEXT=diagnose_post_merge_refresh_status_output" in result.next_action


def test_admin_refresh_pr_creates_branch_and_pr(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    calls = []
    wrapper_calls = []

    def fake_run(command, cwd=None):
        calls.append(command)
        if command == ["git", "ls-remote", "--exit-code", "origin", "HEAD"]:
            return subprocess.CompletedProcess(command, 0, "ref\tHEAD\n", "")
        if command == ["git", "branch", "--show-current"]:
            return subprocess.CompletedProcess(command, 0, "main\n", "")
        if command == ["git", "status", "--short"]:
            status_count = sum(1 for item in calls if item == ["git", "status", "--short"])
            if status_count == 1:
                return subprocess.CompletedProcess(command, 0, "", "")
            return subprocess.CompletedProcess(
                command,
                0,
                " M .agentic/handoff_state.yaml\n"
                " M .agentic/operational_handoff_state.yaml\n"
                " M docs/STATUS.md\n"
                " M docs/handoff/CURRENT_HANDOFF.md\n"
                " M docs/handoff/NEXT_CHAT_BOOTSTRAP.md\n"
                " M docs/handoff/START_NEW_CHAT_PROMPT.md\n"
                " M docs/reports/handoff-packages/latest/execution_contract.json\n"
                " M docs/reports/handoff-packages/latest/successor_context.yaml\n"
                " M docs/reports/handoff-packages/latest/successor_prompt.md\n"
                " M docs/reports/handoff-packages/latest/validation_report.json\n"
                "?? docs/reports/terminal/post-pr123-successor-chat-handoff.md\n",
                "",
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
            return subprocess.CompletedProcess(command, 99, "", "old single-file refresh must not run\n")
        if command == ["agentic-kit", "handoff", "check"]:
            return subprocess.CompletedProcess(
                command, 0, "Persistent handoff state check passed\n", ""
            )
        if command == ["agentic-kit", "handoff", "post-merge-refresh-status"]:
            return subprocess.CompletedProcess(
                command, 0, "POST_MERGE_HANDOFF_REFRESH\nresult=NOOP\n", ""
            )
        if command == ["agentic-kit", "transfer", "protected-diff-plan", "--label", "post-pr123-handoff-refresh"]:
            return subprocess.CompletedProcess(command, 0, "PLAN: PASS\n", "")
        return subprocess.CompletedProcess(command, 99, "", f"unexpected command: {command}\n")

    def fake_refresh_operational_handoff_docs(after_pr):
        assert after_pr == 123
        return subprocess.CompletedProcess(
            ["admin-refresh-operational-handoff-docs", "--after-pr", "123"],
            0,
            "Updated operational handoff docs:\n",
            "",
        )

    monkeypatch.setattr("agentic_project_kit.transfer_repo_actions._run", fake_run)
    monkeypatch.setattr(
        "agentic_project_kit.transfer_repo_actions._agentic_kit_command", lambda: "agentic-kit"
    )
    monkeypatch.setattr(
        "agentic_project_kit.transfer_repo_actions._refresh_operational_handoff_docs",
        fake_refresh_operational_handoff_docs,
    )
    monkeypatch.setattr(
        transfer_repo_actions,
        "commit_paths",
        lambda message, paths, required_branch="", allow_main=False: wrapper_calls.append(
            ("commit_paths", message, tuple(paths), required_branch, allow_main)
        )
        or transfer_repo_actions.RepoActionResult(
            "commit", "PASS", 0, ["commit"], "committed\n", "", "Push current branch or inspect status."
        ),
    )
    monkeypatch.setattr(
        transfer_repo_actions,
        "push_current",
        lambda required_branch="": wrapper_calls.append(("push_current", required_branch))
        or transfer_repo_actions.RepoActionResult(
            "push-current", "PASS", 0, ["push-current"], "pushed\n", "", "Create or inspect pull request."
        ),
    )
    monkeypatch.setattr(
        transfer_repo_actions,
        "pr_create",
        lambda base, head, title, body: wrapper_calls.append((base, head, title, body))
        or transfer_repo_actions.RepoActionResult(
            "pr-create",
            "PASS",
            0,
            ["pr-create"],
            "https://github.com/vfi64/agentic-project-kit/pull/999\n",
            "",
            "Run agentic-kit transfer pr-status on the created PR.",
        ),
    )

    result = admin_refresh_pr(123)

    assert result.result_status == "PASS"
    assert result.returncode == 0
    assert "docs/post-pr123-handoff-refresh" in result.stdout
    assert "pull/999" in result.stdout
    assert (
        "commit_paths",
        "Refresh handoff state after PR123",
        (*transfer_repo_actions.ADMIN_REFRESH_PATHS, "docs/reports/terminal/post-pr123-successor-chat-handoff.md"),
        "docs/post-pr123-handoff-refresh",
        False,
    ) in wrapper_calls
    assert ("push_current", "docs/post-pr123-handoff-refresh") in wrapper_calls
    assert any(call[:3] == ("main", "docs/post-pr123-handoff-refresh", "Refresh handoff state after PR123") for call in wrapper_calls if isinstance(call, tuple))
    assert ["git", "push", "-u", "origin", "docs/post-pr123-handoff-refresh"] not in calls
    assert not any(command[:3] == ["gh", "pr", "create"] for command in calls)


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
        if command == ["git", "ls-remote", "--exit-code", "origin", "HEAD"]:
            return subprocess.CompletedProcess(command, 0, "ref\tHEAD\n", "")
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
        if command == ["git", "ls-remote", "--exit-code", "origin", "HEAD"]:
            return subprocess.CompletedProcess(command, 0, "ref\tHEAD\n", "")
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
        if command == ["git", "ls-remote", "--exit-code", "origin", "HEAD"]:
            return subprocess.CompletedProcess(command, 0, "ref\tHEAD\n", "")
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
        if command == ["git", "ls-remote", "--exit-code", "origin", "HEAD"]:
            return subprocess.CompletedProcess(command, 0, "ref\tHEAD\n", "")
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

    result = CliRunner().invoke(app, ["transfer", "pr-merge-safe", "123", "--skip-llm-context-gate"])

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
        if command == ["git", "ls-remote", "--exit-code", "origin", "HEAD"]:
            return subprocess.CompletedProcess(command, 0, "ref\tHEAD\n", "")
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
        if command == ["git", "ls-remote", "--exit-code", "origin", "HEAD"]:
            return subprocess.CompletedProcess(command, 0, "ref\tHEAD\n", "")
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
        if command == ["git", "ls-remote", "--exit-code", "origin", "HEAD"]:
            return subprocess.CompletedProcess(command, 0, "ref\tHEAD\n", "")
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
        if command == ["git", "ls-remote", "--exit-code", "origin", "HEAD"]:
            return subprocess.CompletedProcess(command, 0, "ref\tHEAD\n", "")
        if command == ["git", "branch", "--show-current"]:
            return subprocess.CompletedProcess(command, 0, "feature/demo\n", "")
        if command == ["git", "push", "-u", "origin", "feature/demo"]:
            return subprocess.CompletedProcess(command, 0, "pushed\n", "")
        if command == ["git", "rev-parse", "HEAD"]:
            return subprocess.CompletedProcess(command, 0, "abc123\n", "")
        if command == ["git", "ls-remote", "--exit-code", "--heads", "origin", "feature/demo"]:
            return subprocess.CompletedProcess(command, 0, "abc123\trefs/heads/feature/demo\n", "")
        return subprocess.CompletedProcess(command, 99, "", f"unexpected command: {command}\n")

    monkeypatch.setattr(transfer_repo_actions, "guard_branch", fake_guard_branch)
    monkeypatch.setattr(transfer_repo_actions, "_run", fake_run)

    result = transfer_repo_actions.push_current(required_branch="feature/demo")

    assert result.returncode == 0
    assert result.result_status == "PASS"
    assert ["git", "push", "-u", "origin", "feature/demo"] in calls


def test_push_current_refuses_remote_mismatch_after_push(monkeypatch):
    calls = []

    class PassingMonitor:
        decision = transfer_repo_actions.MonitorDecision.CONTINUE
        actual_branch = "feature/demo"
        required_branch = "feature/demo"
        reason = "test_monitor_pass"

    def fake_run(command, cwd=None):
        calls.append(command)
        if command == ["git", "branch", "--show-current"]:
            return subprocess.CompletedProcess(command, 0, "feature/demo\n", "")
        if command == ["git", "ls-remote", "--exit-code", "origin", "HEAD"]:
            return subprocess.CompletedProcess(command, 0, "ref\tHEAD\n", "")
        if command == ["git", "push", "-u", "origin", "feature/demo"]:
            return subprocess.CompletedProcess(command, 0, "pushed\n", "")
        if command == ["git", "rev-parse", "HEAD"]:
            return subprocess.CompletedProcess(command, 0, "local123\n", "")
        if command == ["git", "ls-remote", "--exit-code", "--heads", "origin", "feature/demo"]:
            return subprocess.CompletedProcess(command, 0, "remote456\trefs/heads/feature/demo\n", "")
        return subprocess.CompletedProcess(command, 99, "", f"unexpected command: {command}\n")

    monkeypatch.setattr(transfer_repo_actions, "_run", fake_run)
    monkeypatch.setattr(transfer_repo_actions, "guard_branch", lambda **kwargs: PassingMonitor())

    result = transfer_repo_actions.push_current(required_branch="feature/demo")

    assert result.returncode == 2
    assert result.result_status == "FAIL"
    assert "does not match local HEAD after push" in result.stderr
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
        if command == ["git", "ls-remote", "--exit-code", "origin", "HEAD"]:
            return subprocess.CompletedProcess(command, 0, "ref\tHEAD\n", "")
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
        if command == ["git", "ls-remote", "--exit-code", "origin", "HEAD"]:
            return subprocess.CompletedProcess(command, 0, "ref\tHEAD\n", "")
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
        if command == ["git", "ls-remote", "--exit-code", "origin", "HEAD"]:
            return subprocess.CompletedProcess(command, 0, "ref\tHEAD\n", "")
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
        if command == ["git", "ls-remote", "--exit-code", "origin", "HEAD"]:
            return subprocess.CompletedProcess(command, 0, "ref\tHEAD\n", "")
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
        if command == ["git", "ls-remote", "--exit-code", "origin", "HEAD"]:
            return subprocess.CompletedProcess(command, 0, "ref\tHEAD\n", "")
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
        if command == ["git", "ls-remote", "--exit-code", "origin", "HEAD"]:
            return subprocess.CompletedProcess(command, 0, "ref\tHEAD\n", "")
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
        if command == ["git", "ls-remote", "--exit-code", "origin", "HEAD"]:
            return subprocess.CompletedProcess(command, 0, "ref\tHEAD\n", "")
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
        if command == ["git", "ls-remote", "--exit-code", "origin", "HEAD"]:
            return subprocess.CompletedProcess(command, 0, "ref\tHEAD\n", "")
        return subprocess.CompletedProcess(command, 99, "", f"unexpected command: {command}\n")

    monkeypatch.setattr(transfer_repo_actions, "guard_branch", fake_guard_branch)
    monkeypatch.setattr(transfer_repo_actions, "_run", fake_run)

    result = transfer_repo_actions.admin_refresh_pr(123, main_branch="main")

    assert result.returncode == 2
    assert result.result_status == "FAIL"
    assert "Transfer operation monitor blocked admin-refresh-pr" in result.stderr
    assert ["git", "status", "--short"] not in calls


def test_transfer_protected_diff_plan_runs_diff_and_python_planner(monkeypatch):
    calls: list[list[str]] = []

    def fake_run(argv, *args, **kwargs):
        command = list(argv)
        calls.append(command)
        if command == ["git", "ls-remote", "--exit-code", "origin", "HEAD"]:
            return subprocess.CompletedProcess(command, 0, "ref\tHEAD\n", "")
        if command[:2] == ["git", "diff"]:
            return subprocess.CompletedProcess(command, 0, "", "")
        if command[:3] == [sys.executable, "-m", "agentic_project_kit.protected_change_planner"]:
            return subprocess.CompletedProcess(command, 0, "PROTECTED_CHANGE_PLAN\nresult=PASS\n", "")
        return subprocess.CompletedProcess(command, 99, "", f"unexpected command: {command}\n")

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = CliRunner().invoke(app, ["transfer", "protected-diff-plan", "--label", "demo"])

    assert result.exit_code == 0
    assert "TRANSFER_PROTECTED_DIFF_PLAN" in result.stdout
    assert "PASS" in result.stdout
    assert calls[0][:2] == ["git", "diff"]
    assert "--output" in calls[0]
    assert calls[1][:3] == [sys.executable, "-m", "agentic_project_kit.protected_change_planner"]
    assert "--diff-file" in calls[1]


def test_transfer_protected_diff_plan_blocks_on_python_planner_failure(monkeypatch):
    def fake_run(argv, *args, **kwargs):
        command = list(argv)
        if command[:2] == ["git", "diff"]:
            return subprocess.CompletedProcess(command, 0, "", "")
        if command[:3] == [sys.executable, "-m", "agentic_project_kit.protected_change_planner"]:
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

def test_transfer_work_order_patch_applies_exact_text_replacement(monkeypatch, tmp_path):
    from typer.testing import CliRunner
    from agentic_project_kit.cli import app

    monkeypatch.chdir(tmp_path)
    (tmp_path / ".git").mkdir()
    (tmp_path / "demo.txt").write_text("alpha\nold\nomega\n", encoding="utf-8")
    patch = tmp_path / "patch.yaml"
    patch.write_text(
        """
kind: patch_file
expected_branch: feature/demo
protected_change_plan_required: true
operations:
  - path: demo.txt
    old: "old\\n"
    new: "new\\n"
""".lstrip(),
        encoding="utf-8",
    )

    def fake_run(argv, *args, **kwargs):
        command = list(argv)
        if command == ["git", "branch", "--show-current"]:
            return subprocess.CompletedProcess(command, 0, "feature/demo\n", "")
        return subprocess.CompletedProcess(command, 99, "", f"unexpected command: {command}\n")

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = CliRunner().invoke(app, ["transfer", "work-order-patch", "--path", str(patch)])

    assert result.exit_code == 0
    assert "TRANSFER_WORK_ORDER_PATCH" in result.stdout
    assert "STATE:                  PASS" in result.stdout
    assert (tmp_path / "demo.txt").read_text(encoding="utf-8") == "alpha\nnew\nomega\n"


def test_transfer_work_order_patch_blocks_branch_mismatch(monkeypatch, tmp_path):
    from typer.testing import CliRunner
    from agentic_project_kit.cli import app

    monkeypatch.chdir(tmp_path)
    (tmp_path / ".git").mkdir()
    (tmp_path / "demo.txt").write_text("old\n", encoding="utf-8")
    patch = tmp_path / "patch.yaml"
    patch.write_text(
        """
kind: patch_file
expected_branch: feature/expected
operations:
  - path: demo.txt
    old: "old\\n"
    new: "new\\n"
""".lstrip(),
        encoding="utf-8",
    )

    def fake_run(argv, *args, **kwargs):
        command = list(argv)
        if command == ["git", "branch", "--show-current"]:
            return subprocess.CompletedProcess(command, 0, "feature/actual\n", "")
        return subprocess.CompletedProcess(command, 99, "", f"unexpected command: {command}\n")

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = CliRunner().invoke(app, ["transfer", "work-order-patch", "--path", str(patch)])

    assert result.exit_code == 2
    assert "branch mismatch" in result.stdout
    assert (tmp_path / "demo.txt").read_text(encoding="utf-8") == "old\n"


def test_transfer_work_order_patch_blocks_ambiguous_replacement(monkeypatch, tmp_path):
    from typer.testing import CliRunner
    from agentic_project_kit.cli import app

    monkeypatch.chdir(tmp_path)
    (tmp_path / ".git").mkdir()
    (tmp_path / "demo.txt").write_text("old\nold\n", encoding="utf-8")
    patch = tmp_path / "patch.yaml"
    patch.write_text(
        """
kind: patch_file
expected_branch: feature/demo
operations:
  - path: demo.txt
    old: "old\\n"
    new: "new\\n"
""".lstrip(),
        encoding="utf-8",
    )

    def fake_run(argv, *args, **kwargs):
        command = list(argv)
        if command == ["git", "branch", "--show-current"]:
            return subprocess.CompletedProcess(command, 0, "feature/demo\n", "")
        return subprocess.CompletedProcess(command, 99, "", f"unexpected command: {command}\n")

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = CliRunner().invoke(app, ["transfer", "work-order-patch", "--path", str(patch)])

    assert result.exit_code == 2
    assert "found 2" in result.stdout
    assert (tmp_path / "demo.txt").read_text(encoding="utf-8") == "old\nold\n"

def test_transfer_rebase_on_upstream_rebases_current_branch(monkeypatch):
    from typer.testing import CliRunner
    from agentic_project_kit.cli import app

    calls: list[list[str]] = []

    def fake_run(argv, *args, **kwargs):
        command = list(argv)
        calls.append(command)
        if command == ["git", "ls-remote", "--exit-code", "origin", "HEAD"]:
            return subprocess.CompletedProcess(command, 0, "ref\tHEAD\n", "")
        if command == ["git", "branch", "--show-current"]:
            return subprocess.CompletedProcess(command, 0, "feature/demo\n", "")
        if command == ["git", "fetch", "origin", "feature/demo"]:
            return subprocess.CompletedProcess(command, 0, "fetched\n", "")
        if command == ["git", "rebase", "origin/feature/demo"]:
            return subprocess.CompletedProcess(command, 0, "rebased\n", "")
        if command == ["./.venv/bin/agentic-kit", "transfer", "conflict-status", "--json"]:
            return subprocess.CompletedProcess(command, 0, '{"conflict_present": false}\n', "")
        return subprocess.CompletedProcess(command, 99, "", f"unexpected command: {command}\n")

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = CliRunner().invoke(app, ["transfer", "rebase-on-upstream"])

    assert result.exit_code == 0
    assert "TRANSFER_REBASE_ON_UPSTREAM" in result.stdout
    assert "STATE:" in result.stdout
    assert "PASS" in result.stdout
    assert ["git", "rebase", "origin/feature/demo"] in calls


def test_transfer_rebase_on_upstream_blocks_on_main(monkeypatch):
    from typer.testing import CliRunner
    from agentic_project_kit.cli import app

    def fake_run(argv, *args, **kwargs):
        command = list(argv)
        if command == ["git", "branch", "--show-current"]:
            return subprocess.CompletedProcess(command, 0, "main\n", "")
        if command == ["./.venv/bin/agentic-kit", "transfer", "conflict-status", "--json"]:
            return subprocess.CompletedProcess(command, 0, '{"conflict_present": false}\n', "")
        return subprocess.CompletedProcess(command, 99, "", f"unexpected command: {command}\n")

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = CliRunner().invoke(app, ["transfer", "rebase-on-upstream"])

    assert result.exit_code == 2
    assert "refuse_main_branch" in result.stdout


def test_transfer_rebase_on_upstream_reports_conflict(monkeypatch):
    from typer.testing import CliRunner
    from agentic_project_kit.cli import app

    def fake_run(argv, *args, **kwargs):
        command = list(argv)
        if command == ["git", "branch", "--show-current"]:
            return subprocess.CompletedProcess(command, 0, "feature/demo\n", "")
        if command == ["git", "fetch", "origin", "feature/demo"]:
            return subprocess.CompletedProcess(command, 0, "fetched\n", "")
        if command == ["git", "rebase", "origin/feature/demo"]:
            return subprocess.CompletedProcess(command, 1, "", "conflict\n")
        if command == ["./.venv/bin/agentic-kit", "transfer", "conflict-status", "--json"]:
            return subprocess.CompletedProcess(command, 2, '{"conflict_present": true, "unmerged_files": ["demo.txt"]}\n', "")
        return subprocess.CompletedProcess(command, 99, "", f"unexpected command: {command}\n")

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = CliRunner().invoke(app, ["transfer", "rebase-on-upstream"])

    assert result.exit_code == 2
    assert "TRANSFER_REBASE_ON_UPSTREAM" in result.stdout
    assert "rebase_failed" in result.stdout
    assert "conflict_detected" in result.stdout

def test_transfer_conflict_resolve_file_replaces_and_stages(monkeypatch, tmp_path):
    from typer.testing import CliRunner
    from agentic_project_kit.cli import app

    monkeypatch.chdir(tmp_path)
    (tmp_path / ".git").mkdir()
    (tmp_path / "file.txt").write_text("conflict\n", encoding="utf-8")
    source = tmp_path / "resolved.txt"
    source.write_text("resolved\n", encoding="utf-8")
    calls: list[list[str]] = []

    def fake_run(argv, *args, **kwargs):
        command = list(argv)
        calls.append(command)
        if command == ["git", "ls-remote", "--exit-code", "origin", "HEAD"]:
            return subprocess.CompletedProcess(command, 0, "ref\tHEAD\n", "")
        if command == ["git", "branch", "--show-current"]:
            return subprocess.CompletedProcess(command, 0, "feature/demo\n", "")
        if command == ["git", "diff", "--name-only", "--diff-filter=U"]:
            return subprocess.CompletedProcess(command, 0, "file.txt\n", "")
        if command == ["git", "add", "file.txt"]:
            return subprocess.CompletedProcess(command, 0, "", "")
        return subprocess.CompletedProcess(command, 99, "", f"unexpected command: {command}\n")

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = CliRunner().invoke(
        app,
        ["transfer", "conflict-resolve-file", "file.txt", "--source", str(source), "--branch", "feature/demo"],
    )

    assert result.exit_code == 0
    assert "TRANSFER_CONFLICT_RESOLVE_FILE" in result.stdout
    assert (tmp_path / "file.txt").read_text(encoding="utf-8") == "resolved\n"
    assert ["git", "add", "file.txt"] in calls


def test_transfer_conflict_resolve_file_blocks_non_unmerged_target(monkeypatch, tmp_path):
    from typer.testing import CliRunner
    from agentic_project_kit.cli import app

    monkeypatch.chdir(tmp_path)
    (tmp_path / ".git").mkdir()
    (tmp_path / "file.txt").write_text("original\n", encoding="utf-8")
    source = tmp_path / "resolved.txt"
    source.write_text("resolved\n", encoding="utf-8")

    def fake_run(argv, *args, **kwargs):
        command = list(argv)
        if command == ["git", "branch", "--show-current"]:
            return subprocess.CompletedProcess(command, 0, "feature/demo\n", "")
        if command == ["git", "diff", "--name-only", "--diff-filter=U"]:
            return subprocess.CompletedProcess(command, 0, "", "")
        return subprocess.CompletedProcess(command, 99, "", f"unexpected command: {command}\n")

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = CliRunner().invoke(
        app,
        ["transfer", "conflict-resolve-file", "file.txt", "--source", str(source), "--branch", "feature/demo"],
    )

    assert result.exit_code == 2
    assert "target_not_unmerged" in result.stdout
    assert (tmp_path / "file.txt").read_text(encoding="utf-8") == "original\n"


def test_transfer_conflict_resolve_file_blocks_main_branch(monkeypatch, tmp_path):
    from typer.testing import CliRunner
    from agentic_project_kit.cli import app

    monkeypatch.chdir(tmp_path)
    (tmp_path / ".git").mkdir()
    (tmp_path / "file.txt").write_text("original\n", encoding="utf-8")
    source = tmp_path / "resolved.txt"
    source.write_text("resolved\n", encoding="utf-8")

    def fake_run(argv, *args, **kwargs):
        command = list(argv)
        if command == ["git", "branch", "--show-current"]:
            return subprocess.CompletedProcess(command, 0, "main\n", "")
        if command == ["git", "diff", "--name-only", "--diff-filter=U"]:
            return subprocess.CompletedProcess(command, 0, "file.txt\n", "")
        return subprocess.CompletedProcess(command, 99, "", f"unexpected command: {command}\n")

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = CliRunner().invoke(
        app,
        ["transfer", "conflict-resolve-file", "file.txt", "--source", str(source)],
    )

    assert result.exit_code == 2
    assert "refuse_main_branch" in result.stdout
    assert (tmp_path / "file.txt").read_text(encoding="utf-8") == "original\n"

def test_transfer_delete_merged_work_branch_deletes_local_and_remote(monkeypatch):
    from typer.testing import CliRunner
    from agentic_project_kit.cli import app

    calls: list[list[str]] = []

    def fake_run(argv, *args, **kwargs):
        command = list(argv)
        calls.append(command)
        if command == ["git", "ls-remote", "--exit-code", "origin", "HEAD"]:
            return subprocess.CompletedProcess(command, 0, "ref\tHEAD\n", "")
        if command == ["git", "branch", "--show-current"]:
            return subprocess.CompletedProcess(command, 0, "main\n", "")
        if command[:3] == ["gh", "pr", "view"]:
            return subprocess.CompletedProcess(command, 0, "MERGED\t2026-06-08T10:00:00Z\t123\tfeature/done\n", "")
        if command == ["git", "branch", "-d", "feature/done"]:
            return subprocess.CompletedProcess(command, 0, "deleted\n", "")
        if command == ["git", "push", "origin", "--delete", "feature/done"]:
            return subprocess.CompletedProcess(command, 0, "deleted remote\n", "")
        return subprocess.CompletedProcess(command, 99, "", f"unexpected command: {command}\n")

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = CliRunner().invoke(app, ["transfer", "delete-merged-work-branch", "feature/done"])

    assert result.exit_code == 0
    assert "TRANSFER_DELETE_MERGED_WORK_BRANCH" in result.stdout
    assert ["git", "branch", "-d", "feature/done"] in calls
    assert ["git", "push", "origin", "--delete", "feature/done"] in calls


def test_transfer_delete_merged_work_branch_refuses_main(monkeypatch):
    from typer.testing import CliRunner
    from agentic_project_kit.cli import app

    def fake_run(argv, *args, **kwargs):
        command = list(argv)
        if command == ["git", "branch", "--show-current"]:
            return subprocess.CompletedProcess(command, 0, "feature/demo\n", "")
        if command[:3] == ["gh", "pr", "view"]:
            return subprocess.CompletedProcess(command, 0, "MERGED\t2026-06-08T10:00:00Z\t123\tmain\n", "")
        return subprocess.CompletedProcess(command, 99, "", f"unexpected command: {command}\n")

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = CliRunner().invoke(app, ["transfer", "delete-merged-work-branch", "main"])

    assert result.exit_code == 2
    assert "refuse_main_branch" in result.stdout


def test_transfer_delete_merged_work_branch_blocks_unmerged_pr(monkeypatch):
    from typer.testing import CliRunner
    from agentic_project_kit.cli import app

    def fake_run(argv, *args, **kwargs):
        command = list(argv)
        if command == ["git", "branch", "--show-current"]:
            return subprocess.CompletedProcess(command, 0, "main\n", "")
        if command[:3] == ["gh", "pr", "view"]:
            return subprocess.CompletedProcess(command, 0, "OPEN\t\t123\tfeature/not-done\n", "")
        return subprocess.CompletedProcess(command, 99, "", f"unexpected command: {command}\n")

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = CliRunner().invoke(app, ["transfer", "delete-merged-work-branch", "feature/not-done"])

    assert result.exit_code == 2
    assert "pr_not_merged" in result.stdout


def test_transfer_delete_merged_work_branch_refuses_current_branch(monkeypatch):
    from typer.testing import CliRunner
    from agentic_project_kit.cli import app

    def fake_run(argv, *args, **kwargs):
        command = list(argv)
        if command == ["git", "branch", "--show-current"]:
            return subprocess.CompletedProcess(command, 0, "feature/current\n", "")
        if command[:3] == ["gh", "pr", "view"]:
            return subprocess.CompletedProcess(command, 0, "MERGED\t2026-06-08T10:00:00Z\t123\tfeature/current\n", "")
        return subprocess.CompletedProcess(command, 99, "", f"unexpected command: {command}\n")

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = CliRunner().invoke(app, ["transfer", "delete-merged-work-branch", "feature/current"])

    assert result.exit_code == 2
    assert "refuse_delete_current_branch" in result.stdout



def test_pr_merge_safe_repairs_known_volatile_before_merge(monkeypatch):
    calls = []

    class BlockMonitor:
        decision = transfer_repo_actions.MonitorDecision.BLOCK
        actual_branch = "feature/work"
        required_branch = "main"
        reason = "dirty_worktree_blocks_branch_switch"

    class ContinueMonitor:
        decision = transfer_repo_actions.MonitorDecision.CONTINUE
        actual_branch = "main"
        required_branch = "main"
        reason = "already_on_required_branch"

    monitors = [BlockMonitor(), ContinueMonitor()]

    def fake_guard_branch(**kwargs):
        calls.append(["guard_branch", kwargs])
        return monitors.pop(0)

    def fake_run(command, cwd=None):
        calls.append(command)
        if command == ["git", "ls-remote", "--exit-code", "origin", "HEAD"]:
            return subprocess.CompletedProcess(command, 0, "ref\tHEAD\n", "")
        if (
            len(command) >= 4
            and command[0].endswith("agentic-kit")
            and command[1:] == ["transfer", "normalize-session", "--repair-known-volatile"]
        ):
            return subprocess.CompletedProcess(command, 0, "normalized\n", "")
        if len(command) >= 3 and command[0].endswith("agentic-kit") and command[1:3] == ["pr", "merge-if-green"]:
            return subprocess.CompletedProcess(command, 0, "merged\n", "")
        return subprocess.CompletedProcess(command, 99, "", f"unexpected command: {command}\n")

    monkeypatch.setattr(transfer_repo_actions, "guard_branch", fake_guard_branch)
    monkeypatch.setattr(transfer_repo_actions, "_run", fake_run)

    result = transfer_repo_actions.pr_merge_safe(
        123,
        expected_head_sha="0123456789abcdef0123456789abcdef01234567",
        main_branch="main",
    )

    assert result.returncode == 0
    assert result.result_status == "PASS"
    assert any(
        isinstance(call, list)
        and len(call) >= 4 and call[0].endswith("agentic-kit") and call[1:] == ["transfer", "normalize-session", "--repair-known-volatile"]
        for call in calls
    )
    assert any(
        isinstance(call, list)
        and len(call) >= 3 and call[0].endswith("agentic-kit") and call[1:3] == ["pr", "merge-if-green"]
        for call in calls
    )
    assert len([call for call in calls if isinstance(call, list) and call and call[0] == "guard_branch"]) == 2


def test_pr_merge_safe_still_blocks_when_volatile_repair_fails(monkeypatch):
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
        if command == ["git", "ls-remote", "--exit-code", "origin", "HEAD"]:
            return subprocess.CompletedProcess(command, 0, "ref\tHEAD\n", "")
        if command == [
            "./.venv/bin/agentic-kit",
            "transfer",
            "normalize-session",
            "--repair-known-volatile",
        ]:
            return subprocess.CompletedProcess(command, 2, "", "dirty product file\n")
        return subprocess.CompletedProcess(command, 99, "", f"unexpected command: {command}\n")

    monkeypatch.setattr(transfer_repo_actions, "guard_branch", fake_guard_branch)
    monkeypatch.setattr(transfer_repo_actions, "_run", fake_run)

    result = transfer_repo_actions.pr_merge_safe(
        123,
        expected_head_sha="0123456789abcdef0123456789abcdef01234567",
        main_branch="main",
    )

    assert result.returncode == 2
    assert result.result_status == "FAIL"
    assert "Transfer operation monitor blocked pr-merge-safe" in result.stderr
    assert any(
        isinstance(call, list)
        and len(call) >= 4 and call[0].endswith("agentic-kit") and call[1:] == ["transfer", "normalize-session", "--repair-known-volatile"]
        for call in calls
    )
    assert not any(
        isinstance(call, list)
        and len(call) >= 3 and call[0].endswith("agentic-kit") and call[1:3] == ["pr", "merge-if-green"]
        for call in calls
    )

def test_admin_refresh_pr_reuses_existing_local_branch_without_open_pr(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    calls = []
    wrapper_calls = []

    def fake_run(command, cwd=None):
        calls.append(command)
        if command == ["git", "ls-remote", "--exit-code", "origin", "HEAD"]:
            return subprocess.CompletedProcess(command, 0, "ref\tHEAD\n", "")
        if command == ["git", "branch", "--show-current"]:
            return subprocess.CompletedProcess(command, 0, "main\n", "")
        if command == ["git", "status", "--short"]:
            status_count = sum(1 for item in calls if item == ["git", "status", "--short"])
            if status_count == 1:
                return subprocess.CompletedProcess(command, 0, "", "")
            return subprocess.CompletedProcess(
                command,
                0,
                " M .agentic/handoff_state.yaml\n"
                " M .agentic/operational_handoff_state.yaml\n"
                " M docs/STATUS.md\n"
                " M docs/handoff/CURRENT_HANDOFF.md\n"
                " M docs/handoff/NEXT_CHAT_BOOTSTRAP.md\n"
                " M docs/handoff/START_NEW_CHAT_PROMPT.md\n"
                " M docs/reports/handoff-packages/latest/execution_contract.json\n"
                " M docs/reports/handoff-packages/latest/source_manifest.json\n"
                " M docs/reports/handoff-packages/latest/successor_context.yaml\n"
                " M docs/reports/handoff-packages/latest/successor_prompt.md\n"
                " M docs/reports/handoff-packages/latest/validation_report.json\n"
                "?? docs/reports/terminal/post-pr123-successor-chat-handoff.md\n",
                "",
            )
        if command == ["git", "switch", "-c", "docs/post-pr123-handoff-refresh", "main"]:
            return subprocess.CompletedProcess(
                command,
                128,
                "",
                "fatal: a branch named 'docs/post-pr123-handoff-refresh' already exists\n",
            )
        if command[:6] == ["gh", "pr", "list", "--head", "docs/post-pr123-handoff-refresh", "--state"]:
            return subprocess.CompletedProcess(command, 0, "[]\n", "")
        if command == ["git", "switch", "docs/post-pr123-handoff-refresh"]:
            return subprocess.CompletedProcess(command, 0, "", "")
        if command == ["git", "reset", "--hard", "main"]:
            return subprocess.CompletedProcess(command, 0, "HEAD is now at abc123 main\n", "")
        if command == ["agentic-kit", "handoff", "refresh", ".agentic/handoff_state.yaml", "--write"]:
            return subprocess.CompletedProcess(command, 99, "", "old single-file refresh must not run\n")
        if command == ["agentic-kit", "handoff", "check"]:
            return subprocess.CompletedProcess(command, 0, "Persistent handoff state check passed\n", "")
        if command == ["agentic-kit", "handoff", "post-merge-refresh-status"]:
            return subprocess.CompletedProcess(command, 0, "POST_MERGE_HANDOFF_REFRESH\nresult=NOOP\n", "")
        if command == ["agentic-kit", "transfer", "protected-diff-plan", "--label", "post-pr123-handoff-refresh"]:
            return subprocess.CompletedProcess(command, 0, "PLAN: PASS\n", "")
        return subprocess.CompletedProcess(command, 99, "", f"unexpected command: {command}\n")

    def fake_refresh_operational_handoff_docs(after_pr):
        assert after_pr == 123
        return subprocess.CompletedProcess(
            ["admin-refresh-operational-handoff-docs", "--after-pr", "123"],
            0,
            "Updated operational handoff docs:\n",
            "",
        )

    monkeypatch.setattr("agentic_project_kit.transfer_repo_actions._run", fake_run)
    monkeypatch.setattr(
        "agentic_project_kit.transfer_repo_actions._agentic_kit_command",
        lambda: "agentic-kit",
    )
    monkeypatch.setattr(
        "agentic_project_kit.transfer_repo_actions._refresh_operational_handoff_docs",
        fake_refresh_operational_handoff_docs,
    )
    monkeypatch.setattr(
        transfer_repo_actions,
        "commit_paths",
        lambda message, paths, required_branch="", allow_main=False: wrapper_calls.append(
            ("commit_paths", message, tuple(paths), required_branch, allow_main)
        )
        or transfer_repo_actions.RepoActionResult(
            "commit", "PASS", 0, ["commit"], "committed\n", "", "Push current branch or inspect status."
        ),
    )
    monkeypatch.setattr(
        transfer_repo_actions,
        "push_current",
        lambda required_branch="": wrapper_calls.append(("push_current", required_branch))
        or transfer_repo_actions.RepoActionResult(
            "push-current", "PASS", 0, ["push-current"], "pushed\n", "", "Create or inspect pull request."
        ),
    )
    monkeypatch.setattr(
        transfer_repo_actions,
        "pr_create",
        lambda base, head, title, body: wrapper_calls.append((base, head, title, body))
        or transfer_repo_actions.RepoActionResult(
            "pr-create",
            "PASS",
            0,
            ["pr-create"],
            "https://github.com/vfi64/agentic-project-kit/pull/999\n",
            "",
            "Run agentic-kit transfer pr-status on the created PR.",
        ),
    )

    result = admin_refresh_pr(123)

    assert result.result_status == "PASS"
    assert result.returncode == 0
    assert ["git", "switch", "docs/post-pr123-handoff-refresh"] in calls
    assert ["git", "reset", "--hard", "main"] in calls
    assert "pull/999" in result.stdout
    assert ("push_current", "docs/post-pr123-handoff-refresh") in wrapper_calls
    assert any(call[:3] == ("main", "docs/post-pr123-handoff-refresh", "Refresh handoff state after PR123") for call in wrapper_calls if isinstance(call, tuple))
    assert ["git", "push", "-u", "origin", "docs/post-pr123-handoff-refresh"] not in calls
    assert not any(command[:3] == ["gh", "pr", "create"] for command in calls)

def test_transfer_pr_complete_treats_post_merge_complete_failure_as_automatic_admin_refresh(monkeypatch):
    calls = []

    def fake_run(command, text=True, capture_output=True):
        calls.append(command)
        if command == ["git", "ls-remote", "--exit-code", "origin", "HEAD"]:
            return subprocess.CompletedProcess(command, 0, "ref\tHEAD\n", "")
        if command[:3] == ["./.venv/bin/agentic-kit", "transfer", "pr-wait-ci"]:
            return subprocess.CompletedProcess(command, 0, "", "")
        if command[:3] == ["./.venv/bin/agentic-kit", "transfer", "pr-merge-safe"]:
            return subprocess.CompletedProcess(command, 0, "", "")
        if command == ["git", "switch", "main"]:
            return subprocess.CompletedProcess(command, 0, "", "")
        if command == ["git", "pull", "--ff-only", "origin", "main"]:
            return subprocess.CompletedProcess(command, 0, "", "")
        if command == ["./.venv/bin/agentic-kit", "rules", "acknowledge"]:
            return subprocess.CompletedProcess(command, 0, "", "")
        if command == ["./.venv/bin/agentic-kit", "transfer", "post-merge-complete", "--after-pr", "123"]:
            return subprocess.CompletedProcess(command, 2, "post merge follow-up needed\n", "")
        if command == ["gh", "pr", "view", "123", "--json", "state,mergedAt,mergeCommit"]:
            return subprocess.CompletedProcess(
                command,
                0,
                '{"state":"MERGED","mergedAt":"2026-06-18T08:00:00Z","mergeCommit":{"oid":"abc"}}\n',
                "",
            )
        if command == ["./.venv/bin/agentic-kit", "transfer", "sync-main"]:
            return subprocess.CompletedProcess(command, 0, "synced\n", "")
        if command == ["./.venv/bin/agentic-kit", "transfer", "post-merge-check"]:
            prior_checks = sum(1 for item in calls if item == command)
            if prior_checks == 1:
                return subprocess.CompletedProcess(
                    command,
                    2,
                    "NEEDS_SUCCESSOR_PACKAGE_REFRESH\nsuccessor package stale\n",
                    "",
                )
            return subprocess.CompletedProcess(command, 0, "TRANSFER_POST_MERGE_CHECK\nSTATE=PASS\n", "")
        if command == [
            "./.venv/bin/agentic-kit",
            "transfer",
            "admin-refresh-pr",
            "--after-pr",
            "123",
            "--main-branch",
            "main",
            "--json",
        ]:
            return subprocess.CompletedProcess(
                command,
                0,
                '{"stdout":"https://github.com/vfi64/agentic-project-kit/pull/456"}\n',
                "",
            )
        if command == ["gh", "pr", "view", "456", "--json", "headRefOid", "--jq", ".headRefOid"]:
            return subprocess.CompletedProcess(command, 0, "b" * 40 + "\n", "")
        if command == [
            "./.venv/bin/agentic-kit",
            "transfer",
            "pr-complete",
            "456",
            "--expected-head-sha",
            "b" * 40,
            "--merge-method",
            "squash",
            "--timeout-seconds",
            "300",
            "--interval-seconds",
            "10",
            "--skip-llm-context-gate",
            "--json",
        ]:
            return subprocess.CompletedProcess(command, 0, '{"result_status":"PASS"}\n', "")
        return subprocess.CompletedProcess(command, 99, "", f"unexpected command: {command}\n")

    monkeypatch.setattr("subprocess.run", fake_run)

    result = CliRunner().invoke(
        app,
        [
            "transfer",
            "pr-complete",
            "123",
            "--expected-head-sha",
            "a" * 40,
            "--skip-llm-context-gate",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["result_status"] == "PASS"
    assert payload["post_merge_complete_followup_required"] is True
    assert payload["failed_step"] is None
    assert "created, completed, and verified" in payload["next_action"]

    step_names = [step["name"] for step in payload["steps"]]
    assert "sync-main-before-post-merge-check-after-post-merge-complete" in step_names
    assert "post-merge-check-after-post-merge-complete" in step_names
    assert "admin-refresh-pr-after-successor-refresh-needed" in step_names
    assert "admin-refresh-pr-complete" in step_names
    assert "post-merge-check-after-admin-refresh-complete" in step_names

def test_refresh_operational_handoff_docs_updates_arbitrary_previous_pr_state(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".agentic").mkdir()
    (tmp_path / "docs" / "handoff").mkdir(parents=True)
    (tmp_path / "docs" / "planning").mkdir(parents=True)

    (tmp_path / ".agentic" / "handoff_state.yaml").write_text(
        """
schema_version: 1
safe_state:
  commit: abcdef1
  commit_subject: Old subject (#1111)
completed_since_previous_handoff:
- historical post-PR1111 must stay untouched
first_instruction: Start the next chat from the fresh post-PR1111 successor handoff prompt. Verify main at abcdef1, confirm the post-PR1111 operational handoff refresh passes explicit summary inspection.
handoff_maintenance:
  latest_successor_prompt: docs/reports/terminal/post-pr1111-successor-chat-handoff.md
administrative_evidence_state:
  current_head: abcdef1
  current_head_subject: Old subject (#1111)
  latest_successor_prompt: docs/reports/terminal/post-pr1111-successor-chat-handoff.md
""".lstrip(),
        encoding="utf-8",
    )
    (tmp_path / ".agentic" / "operational_handoff_state.yaml").write_text(
        """
schema_version: 1
current_head:
  full: 1111111111111111111111111111111111111111
  short: 1111111
  subject: Old subject (#1111)
last_substantive_work_state:
  full: 1111111111111111111111111111111111111111
  short: 1111111
  subject: Old subject (#1111)
""".lstrip(),
        encoding="utf-8",
    )

    for name in [
        "docs/STATUS.md",
        "docs/handoff/CURRENT_HANDOFF.md",
        "docs/handoff/START_NEW_CHAT_PROMPT.md",
    ]:
        Path(name).write_text("Curated text\n", encoding="utf-8")

    full = "1234567890abcdef1234567890abcdef12345678"
    short = "12345678"
    subject = "New admin refresh behavior (#2222)"

    def fake_run(command, cwd=None):
        if command == ["git", "rev-parse", "HEAD"]:
            return subprocess.CompletedProcess(command, 0, full + "\n", "")
        if command == ["git", "rev-parse", "--short=8", "HEAD"]:
            return subprocess.CompletedProcess(command, 0, short + "\n", "")
        if command == ["git", "log", "-1", "--format=%s"]:
            return subprocess.CompletedProcess(command, 0, subject + "\n", "")
        if command == ["agentic-kit", "transfer", "prepare-successor-handoff", "--render-prompt"]:
            for package_path in [
                "docs/reports/handoff-packages/latest/execution_contract.json",
                "docs/reports/handoff-packages/latest/source_manifest.json",
                "docs/reports/handoff-packages/latest/successor_context.yaml",
                "docs/reports/handoff-packages/latest/successor_prompt.md",
                "docs/reports/handoff-packages/latest/validation_report.json",
            ]:
                Path(package_path).parent.mkdir(parents=True, exist_ok=True)
                Path(package_path).write_text("fresh package\n", encoding="utf-8")
            return subprocess.CompletedProcess(command, 0, "fresh successor prompt\n", "")
        if command == ["agentic-kit", "boot", "write"]:
            Path("docs/handoff/NEXT_CHAT_BOOTSTRAP.md").write_text("bootstrap\n", encoding="utf-8")
            return subprocess.CompletedProcess(command, 0, "WROTE docs/handoff/NEXT_CHAT_BOOTSTRAP.md\n", "")
        if command == ["agentic-kit", "handoff", "prompt"]:
            return subprocess.CompletedProcess(command, 0, "successor prompt\n", "")
        if command == ["agentic-kit", "handoff", "post-merge-refresh-status"]:
            state = Path(".agentic/handoff_state.yaml").read_text(encoding="utf-8")
            for required in [
                "post-pr2222-successor-chat-handoff.md",
                "post-PR2222 successor handoff prompt",
                "post-PR2222 operational handoff refresh",
                "main at 12345678",
            ]:
                assert required in state
            for file_name in [
                "docs/STATUS.md",
                "docs/handoff/CURRENT_HANDOFF.md",
                "docs/handoff/START_NEW_CHAT_PROMPT.md",
            ]:
                content = Path(file_name).read_text(encoding="utf-8")
                assert "Operational documentation refresh state after PR #2222" in content
                assert "12345678" in content
            return subprocess.CompletedProcess(command, 0, "result=NOOP\nrefresh_required=False\n", "")
        return subprocess.CompletedProcess(command, 99, "", f"unexpected command: {command}\n")

    monkeypatch.setattr("agentic_project_kit.transfer_repo_actions._run", fake_run)
    monkeypatch.setattr(
        "agentic_project_kit.transfer_repo_actions._agentic_kit_command",
        lambda: "agentic-kit",
    )

    result = transfer_repo_actions._refresh_operational_handoff_docs(2222)

    assert result.returncode == 0, result.stderr
    handoff_text = Path(".agentic/handoff_state.yaml").read_text(encoding="utf-8")
    operational_text = Path(".agentic/operational_handoff_state.yaml").read_text(encoding="utf-8")
    assert "commit: 12345678" in handoff_text
    assert "current_head: 12345678" in handoff_text
    assert "commit_subject: New admin refresh behavior (#2222)" in handoff_text
    assert "current_head_subject: New admin refresh behavior (#2222)" in handoff_text
    assert "post-pr2222-successor-chat-handoff.md" in handoff_text
    assert "post-PR2222" in handoff_text
    assert "historical post-PR1111 must stay untouched" in handoff_text
    assert full in operational_text
    assert "short: 12345678" in operational_text
    assert "subject: New admin refresh behavior (#2222)" in operational_text
    assert Path("docs/reports/terminal/post-pr2222-successor-chat-handoff.md").read_text(encoding="utf-8") == "successor prompt\n"
    assert "Operational documentation refresh state after PR #2222" in Path("docs/STATUS.md").read_text(encoding="utf-8")
    assert "Updated operational handoff docs:" in result.stdout


def test_admin_refresh_updates_status_current_state_block() -> None:
    status = "\n".join(
        [
            "> STATUS boundary.",
            "",
            "## Current State",
            "",
            "Current version: 0.4.11",
            "Current verified release: 0.4.11.",
            "Current verified main: `old1234` (`Old subject (#1)`).",
            "Latest substantive transfer hardening: PR #1 (`Old subject (#1)`).",
            "Post-merge handoff status: PASS/NOOP after PR #1 administrative refresh PR #2.",
            "Next safe step: continue old work.",
            "",
            "## Historical State Snapshots",
            "",
            "Current verified main: `history1` (`Historical`).",
        ]
    )

    updated = transfer_repo_actions._refresh_status_current_state_block(
        status,
        after_pr=1613,
        short="3a681620",
        subject="Add status current-state audit (#1613)",
    )

    assert "Current verified main: `3a681620` (`Add status current-state audit (#1613)`)." in updated
    assert "Latest substantive work: PR #1613 (`Add status current-state audit (#1613)`)." in updated
    assert "Post-merge handoff status: PASS/NOOP after PR #1613 administrative refresh." in updated
    assert "Next safe step: continue from fresh main with the next planned governed slice." in updated
    assert "Current verified main: `history1` (`Historical`)." in updated



def test_admin_refresh_replaces_existing_operational_refresh_marker(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    for rel in (
        ".agentic/handoff_state.yaml",
        ".agentic/operational_handoff_state.yaml",
        "docs/STATUS.md",
        "docs/handoff/CURRENT_HANDOFF.md",
        "docs/handoff/START_NEW_CHAT_PROMPT.md",
    ):
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)

    (tmp_path / ".agentic/handoff_state.yaml").write_text(
        "administrative_evidence_state:\n"
        "  commit: 979825da\n"
        "  commit_subject: Old refresh (#1338)\n"
        "  latest_successor_prompt: docs/reports/terminal/post-pr1338-successor-chat-handoff.md\n",
        encoding="utf-8",
    )
    (tmp_path / ".agentic/operational_handoff_state.yaml").write_text(
        "main_head:\n"
        "  full: 979825da00000000000000000000000000000000\n"
        "  short: 979825da\n"
        "  subject: Old refresh (#1338)\n",
        encoding="utf-8",
    )
    old_marker = (
        "\n## Operational documentation refresh state after PR #1338\n\n"
        "Current administrative handoff refresh state is `979825da` (`Old refresh (#1338)`). "
        "Continue next only after this post-PR1338 refresh is committed and merged; "
        "the next substantive slice must be created from fresh main.\n"
    )
    for rel in (
        "docs/STATUS.md",
        "docs/handoff/CURRENT_HANDOFF.md",
        "docs/handoff/START_NEW_CHAT_PROMPT.md",
    ):
        (tmp_path / rel).write_text(f"# Doc\n{old_marker}", encoding="utf-8")

    def fake_run(argv: list[str]) -> subprocess.CompletedProcess[str]:
        if argv[:3] == ["git", "rev-parse", "HEAD"]:
            return subprocess.CompletedProcess(argv, 0, "eed934fe54c9d926074a99055ed997c2a91332be\n", "")
        if argv[:3] == ["git", "rev-parse", "--short=8"]:
            return subprocess.CompletedProcess(argv, 0, "eed934fe\n", "")
        if argv[:3] == ["git", "log", "-1"]:
            return subprocess.CompletedProcess(argv, 0, "Publish remote-next transfer report\n", "")
        if argv[-2:] == ["prepare-successor-handoff", "--render-prompt"]:
            for rel in (
                "docs/reports/handoff-packages/latest/execution_contract.json",
                "docs/reports/handoff-packages/latest/source_manifest.json",
                "docs/reports/handoff-packages/latest/successor_context.yaml",
                "docs/reports/handoff-packages/latest/successor_prompt.md",
                "docs/reports/handoff-packages/latest/validation_report.json",
            ):
                (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
                (tmp_path / rel).write_text("{}", encoding="utf-8")
            return subprocess.CompletedProcess(argv, 0, "", "")
        if argv[-2:] == ["boot", "write"]:
            (tmp_path / "docs/handoff/NEXT_CHAT_BOOTSTRAP.md").parent.mkdir(parents=True, exist_ok=True)
            (tmp_path / "docs/handoff/NEXT_CHAT_BOOTSTRAP.md").write_text("bootstrap eed934fe\n", encoding="utf-8")
            return subprocess.CompletedProcess(argv, 0, "", "")
        if argv[-2:] == ["handoff", "prompt"]:
            return subprocess.CompletedProcess(argv, 0, "successor prompt eed934fe\n", "")
        if argv[-2:] == ["post-merge-refresh-status"]:
            return subprocess.CompletedProcess(argv, 0, "result=NOOP\n", "")
        return subprocess.CompletedProcess(argv, 0, "", "")

    monkeypatch.setattr(transfer_repo_actions, "_run", fake_run)

    result = transfer_repo_actions._refresh_operational_handoff_docs(1338)

    assert result.returncode == 0
    for rel in (
        "docs/STATUS.md",
        "docs/handoff/CURRENT_HANDOFF.md",
        "docs/handoff/START_NEW_CHAT_PROMPT.md",
    ):
        content = (tmp_path / rel).read_text(encoding="utf-8")
        assert "979825da" not in content
        assert "eed934fe" in content
        assert content.count("Operational documentation refresh state after PR #1338") == 1



def test_transfer_repo_actions_path_contract_snapshot(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    for rel in (
        ".agentic/handoff_state.yaml",
        ".agentic/operational_handoff_state.yaml",
        "docs/STATUS.md",
        "docs/handoff/CURRENT_HANDOFF.md",
        "docs/handoff/START_NEW_CHAT_PROMPT.md",
    ):
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)

    (tmp_path / ".agentic/handoff_state.yaml").write_text(
        "administrative_evidence_state:\n"
        "  current_head: oldhead1\n"
        "  current_head_subject: Old subject\n"
        "  latest_successor_prompt: docs/reports/terminal/post-pr1000-successor-chat-handoff.md\n"
        "first_instruction: Start the next chat from the fresh post-PR1000 successor handoff prompt. "
        "Verify main at oldhead1, confirm the post-PR1000 operational handoff refresh passes explicit summary inspection.\n",
        encoding="utf-8",
    )
    (tmp_path / ".agentic/operational_handoff_state.yaml").write_text(
        "current_head:\n"
        "  full: 0000000000000000000000000000000000000000\n"
        "  short: oldhead1\n"
        "  subject: Old subject\n",
        encoding="utf-8",
    )
    for rel in (
        "docs/STATUS.md",
        "docs/handoff/CURRENT_HANDOFF.md",
        "docs/handoff/START_NEW_CHAT_PROMPT.md",
    ):
        (tmp_path / rel).write_text("# Stable document\n", encoding="utf-8")

    full = "1234567890abcdef1234567890abcdef12345678"
    short = "12345678"
    subject = "Refresh path contract (#2468)"

    def fake_run(argv: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
        if cwd is not None:
            raise AssertionError(f"unexpected cwd for snapshot fake: {cwd}")
        if argv == ["git", "rev-parse", "HEAD"]:
            return subprocess.CompletedProcess(argv, 0, full + "\n", "")
        if argv == ["git", "rev-parse", "--short=8", "HEAD"]:
            return subprocess.CompletedProcess(argv, 0, short + "\n", "")
        if argv == ["git", "log", "-1", "--format=%s"]:
            return subprocess.CompletedProcess(argv, 0, subject + "\n", "")
        if argv[-2:] == ["prepare-successor-handoff", "--render-prompt"]:
            for rel in (
                "docs/reports/handoff-packages/latest/execution_contract.json",
                "docs/reports/handoff-packages/latest/source_manifest.json",
                "docs/reports/handoff-packages/latest/successor_context.yaml",
                "docs/reports/handoff-packages/latest/successor_prompt.md",
                "docs/reports/handoff-packages/latest/validation_report.json",
            ):
                (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
                (tmp_path / rel).write_text(f"package artifact: {rel}\n", encoding="utf-8")
            return subprocess.CompletedProcess(argv, 0, "fresh package\n", "")
        if argv[-2:] == ["boot", "write"]:
            bootstrap = tmp_path / "docs/handoff/NEXT_CHAT_BOOTSTRAP.md"
            bootstrap.parent.mkdir(parents=True, exist_ok=True)
            bootstrap.write_text("bootstrap contract\n", encoding="utf-8")
            return subprocess.CompletedProcess(argv, 0, "WROTE docs/handoff/NEXT_CHAT_BOOTSTRAP.md\n", "")
        if argv[-2:] == ["handoff", "prompt"]:
            return subprocess.CompletedProcess(argv, 0, "successor prompt contract\n", "")
        if argv[-2:] == ["handoff", "post-merge-refresh-status"]:
            return subprocess.CompletedProcess(argv, 0, "result=NOOP\nrefresh_required=False\n", "")
        return subprocess.CompletedProcess(argv, 99, "", f"unexpected command: {argv}\n")

    monkeypatch.setattr(transfer_repo_actions, "_run", fake_run)

    result = transfer_repo_actions._refresh_operational_handoff_docs(2468)

    assert result.returncode == 0, result.stderr
    relative_files = sorted(
        path.relative_to(tmp_path).as_posix()
        for path in tmp_path.rglob("*")
        if path.is_file()
    )
    assert relative_files == [
        ".agentic/handoff_state.yaml",
        ".agentic/operational_handoff_state.yaml",
        "docs/STATUS.md",
        "docs/handoff/CURRENT_HANDOFF.md",
        "docs/handoff/NEXT_CHAT_BOOTSTRAP.md",
        "docs/handoff/START_NEW_CHAT_PROMPT.md",
        "docs/reports/handoff-packages/latest/execution_contract.json",
        "docs/reports/handoff-packages/latest/source_manifest.json",
        "docs/reports/handoff-packages/latest/successor_context.yaml",
        "docs/reports/handoff-packages/latest/successor_prompt.md",
        "docs/reports/handoff-packages/latest/validation_report.json",
        "docs/reports/terminal/post-pr2468-successor-chat-handoff.md",
    ]
    assert result.stdout.split("\\n") == [
        "Updated operational handoff docs:",
        "- .agentic/handoff_state.yaml",
        "- .agentic/operational_handoff_state.yaml",
        "- docs/STATUS.md",
        "- docs/handoff/CURRENT_HANDOFF.md",
        "- docs/handoff/START_NEW_CHAT_PROMPT.md",
        "- docs/reports/handoff-packages/latest/execution_contract.json",
        "- docs/reports/handoff-packages/latest/source_manifest.json",
        "- docs/reports/handoff-packages/latest/successor_context.yaml",
        "- docs/reports/handoff-packages/latest/successor_prompt.md",
        "- docs/reports/handoff-packages/latest/validation_report.json",
        "- docs/handoff/NEXT_CHAT_BOOTSTRAP.md",
        "- docs/reports/terminal/post-pr2468-successor-chat-handoff.md",
        "",
    ]
    assert "latest_successor_prompt: docs/reports/terminal/post-pr2468-successor-chat-handoff.md" in (
        tmp_path / ".agentic/handoff_state.yaml"
    ).read_text(encoding="utf-8")
    assert "Operational documentation refresh state after PR #2468" in (
        tmp_path / "docs/STATUS.md"
    ).read_text(encoding="utf-8")
    assert (
        tmp_path / "docs/reports/terminal/post-pr2468-successor-chat-handoff.md"
    ).read_text(encoding="utf-8") == "successor prompt contract\n"


def test_admin_refresh_pr_skips_refresh_only_pr(monkeypatch):
    from agentic_project_kit import transfer_repo_actions as actions

    calls = []

    def fake_run(argv, **kwargs):
        calls.append(tuple(argv))
        if tuple(argv[:3]) == ("gh", "pr", "view"):
            return subprocess.CompletedProcess(
                argv,
                0,
                "Refresh successor handoff after PR1279\ndocs/post-pr1279-handoff-refresh\n",
                "",
            )
        raise AssertionError(f"unexpected command after refresh-only detection: {argv!r}")

    monkeypatch.setattr(actions, "_run", fake_run)

    result = actions.admin_refresh_pr(1280)

    assert result.returncode == 0
    assert result.result_status == "PASS"
    assert result.action == "admin-refresh-pr"
    assert result.next_action == "admin_refresh_skipped_refresh_only_pr"
    assert "skipping chained admin refresh" in result.stdout
    assert calls == [
        (
            "gh",
            "pr",
            "view",
            "1280",
            "--json",
            "title,headRefName",
            "--jq",
            ".title + \"\\n\" + .headRefName",
        )
    ]



def test_operational_refresh_marker_uses_real_newlines() -> None:
    source = Path("src/agentic_project_kit/transfer_repo_actions.py").read_text(encoding="utf-8")
    assert 'f"\\\\n## Operational documentation refresh state after PR #' not in source
    assert 'fresh main.\\\\n"' not in source
    assert '.replace("\\\\n", "\\n")' in source


def test_successor_package_freshness_detects_missing_execution_contract(tmp_path, monkeypatch) -> None:
    import json
    import subprocess
    from agentic_project_kit import transfer_repo_actions as actions

    package_dir = tmp_path / "docs" / "reports" / "handoff-packages" / "latest"
    package_dir.mkdir(parents=True)
    (tmp_path / "docs" / "handoff").mkdir(parents=True)

    head = "abc123"
    (package_dir / "validation_report.json").write_text(
        json.dumps({"status": "PASS", "generated_head": head}),
        encoding="utf-8",
    )
    (package_dir / "successor_prompt.md").write_text(
        "Zusätzliche Startbremse nach dem Bootstrap\nRESULT=NEW_CHAT_BOOTSTRAP_DONE\nÜbergabe akzeptiert, keine Admin-Arbeit nötig\n",
        encoding="utf-8",
    )
    (tmp_path / "docs" / "handoff" / "START_NEW_CHAT_PROMPT.md").write_text(
        "Zusätzliche Startbremse nach dem Bootstrap\n",
        encoding="utf-8",
    )

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        actions,
        "_run",
        lambda command: subprocess.CompletedProcess(command, 0, head + "\n", ""),
    )

    findings = actions._successor_package_freshness_findings(tmp_path)
    assert any("missing docs/reports/handoff-packages/latest/execution_contract.json" in item for item in findings)


def test_successor_package_freshness_detects_stale_generated_head(tmp_path, monkeypatch) -> None:
    import json
    import subprocess

    from agentic_project_kit import transfer_repo_actions as actions

    package_dir = tmp_path / "docs" / "reports" / "handoff-packages" / "latest"
    package_dir.mkdir(parents=True)
    (tmp_path / "docs" / "handoff").mkdir(parents=True)

    (package_dir / "validation_report.json").write_text(
        json.dumps({"status": "PASS", "generated_head": "old"}),
        encoding="utf-8",
    )
    (package_dir / "execution_contract.json").write_text(
        json.dumps(
            {
                "kind": "successor_execution_contract",
                "rules": [
                    {"rule_id": "local-copy-paste-protocol"},
                    {"rule_id": "strict-start-decision"},
                    {"rule_id": "protected-file-preservation"},
                    {"rule_id": "bootstrap_acceptance_gate"},
                ],
            }
        ),
        encoding="utf-8",
    )
    (package_dir / "successor_prompt.md").write_text(
        "Zusätzliche Startbremse nach dem Bootstrap\nRESULT=NEW_CHAT_BOOTSTRAP_DONE\nÜbergabe akzeptiert, keine Admin-Arbeit nötig\n",
        encoding="utf-8",
    )
    (tmp_path / "docs" / "handoff" / "START_NEW_CHAT_PROMPT.md").write_text(
        "Zusätzliche Startbremse nach dem Bootstrap\n",
        encoding="utf-8",
    )

    monkeypatch.chdir(tmp_path)
    def fake_run(command, *, cwd=None):
        if command == ["git", "rev-parse", "HEAD"]:
            return subprocess.CompletedProcess(command, 0, "new\n", "")
        if command == ["git", "merge-base", "--is-ancestor", "old", "new"]:
            return subprocess.CompletedProcess(command, 1, "", "not ancestor")
        return subprocess.CompletedProcess(command, 1, "", "unexpected command")

    monkeypatch.setattr(actions, "_run", fake_run)

    findings = actions._successor_package_freshness_findings(tmp_path)
    assert "validation_report.json generated_head does not match HEAD or refresh-only ancestry" in findings


def test_successor_package_freshness_allows_refresh_only_head_drift(monkeypatch, tmp_path):
    from agentic_project_kit import transfer_repo_actions as actions

    package = tmp_path / "docs" / "reports" / "handoff-packages" / "latest"
    package.mkdir(parents=True)
    (package / "validation_report.json").write_text(
        '{"status": "PASS", "generated_head": "old"}',
        encoding="utf-8",
    )
    (package / "execution_contract.json").write_text(
        '{"kind": "successor_execution_contract", "rules": ['
        '{"rule_id": "local-copy-paste-protocol"},'
        '{"rule_id": "strict-start-decision"},'
        '{"rule_id": "protected-file-preservation"},'
        '{"rule_id": "bootstrap_acceptance_gate"}'
        ']}',
        encoding="utf-8",
    )
    (package / "successor_prompt.md").write_text(
        "Zusätzliche Startbremse nach dem Bootstrap\n"
        "RESULT=NEW_CHAT_BOOTSTRAP_DONE\n"
        "Übergabe akzeptiert, keine Admin-Arbeit nötig\n",
        encoding="utf-8",
    )
    start_prompt = tmp_path / "docs" / "handoff" / "START_NEW_CHAT_PROMPT.md"
    start_prompt.parent.mkdir(parents=True)
    start_prompt.write_text("stable start prompt\n", encoding="utf-8")

    def fake_run(command, *, cwd=None):
        import subprocess

        if command == ["git", "rev-parse", "HEAD"]:
            return subprocess.CompletedProcess(command, 0, "new\n", "")
        if command == ["git", "merge-base", "--is-ancestor", "old", "new"]:
            return subprocess.CompletedProcess(command, 0, "", "")
        if command == ["git", "diff", "--name-only", "old..new"]:
            return subprocess.CompletedProcess(
                command,
                0,
                "docs/reports/handoff-packages/latest/validation_report.json\n"
                "docs/reports/handoff-packages/latest/execution_contract.json\n"
                "docs/handoff/NEXT_CHAT_BOOTSTRAP.md\n",
                "",
            )
        return subprocess.CompletedProcess(command, 1, "", "unexpected command")

    monkeypatch.setattr(actions, "_run", fake_run)

    assert actions._successor_package_freshness_findings(tmp_path) == []
    check = actions._successor_package_freshness_check(tmp_path)
    assert check.findings == ()
    assert "successor_package_head_status=refresh_only_descendant" in check.notes
    assert "successor_package_generated_head=old" in check.notes
    assert "successor_package_current_head=new" in check.notes


def test_successor_package_freshness_rejects_project_direction_head_drift(monkeypatch, tmp_path):
    from agentic_project_kit import transfer_repo_actions as actions

    package = tmp_path / "docs" / "reports" / "handoff-packages" / "latest"
    package.mkdir(parents=True)
    (package / "validation_report.json").write_text(
        '{"status": "PASS", "generated_head": "old"}',
        encoding="utf-8",
    )
    (package / "execution_contract.json").write_text(
        '{"kind": "successor_execution_contract", "rules": ['
        '{"rule_id": "local-copy-paste-protocol"},'
        '{"rule_id": "strict-start-decision"},'
        '{"rule_id": "protected-file-preservation"},'
        '{"rule_id": "bootstrap_acceptance_gate"}'
        ']}',
        encoding="utf-8",
    )
    (package / "successor_prompt.md").write_text(
        "Zusätzliche Startbremse nach dem Bootstrap\n"
        "RESULT=NEW_CHAT_BOOTSTRAP_DONE\n"
        "Übergabe akzeptiert, keine Admin-Arbeit nötig\n",
        encoding="utf-8",
    )

    def fake_run(command, *, cwd=None):
        import subprocess

        if command == ["git", "rev-parse", "HEAD"]:
            return subprocess.CompletedProcess(command, 0, "new\n", "")
        if command == ["git", "merge-base", "--is-ancestor", "old", "new"]:
            return subprocess.CompletedProcess(command, 0, "", "")
        if command == ["git", "diff", "--name-only", "old..new"]:
            return subprocess.CompletedProcess(
                command,
                0,
                "docs/planning/project_direction.yaml\n",
                "",
            )
        return subprocess.CompletedProcess(command, 1, "", "unexpected command")

    monkeypatch.setattr(actions, "_run", fake_run)

    assert "validation_report.json generated_head does not match HEAD or refresh-only ancestry" in (
        actions._successor_package_freshness_findings(tmp_path)
    )


def test_successor_package_freshness_rejects_product_head_drift(monkeypatch, tmp_path):
    from agentic_project_kit import transfer_repo_actions as actions

    package = tmp_path / "docs" / "reports" / "handoff-packages" / "latest"
    package.mkdir(parents=True)
    (package / "validation_report.json").write_text(
        '{"status": "PASS", "generated_head": "old"}',
        encoding="utf-8",
    )
    (package / "execution_contract.json").write_text(
        '{"kind": "successor_execution_contract", "rules": ['
        '{"rule_id": "local-copy-paste-protocol"},'
        '{"rule_id": "strict-start-decision"},'
        '{"rule_id": "protected-file-preservation"},'
        '{"rule_id": "bootstrap_acceptance_gate"}'
        ']}',
        encoding="utf-8",
    )
    (package / "successor_prompt.md").write_text(
        "Zusätzliche Startbremse nach dem Bootstrap\n"
        "RESULT=NEW_CHAT_BOOTSTRAP_DONE\n"
        "Übergabe akzeptiert, keine Admin-Arbeit nötig\n",
        encoding="utf-8",
    )
    start_prompt = tmp_path / "docs" / "handoff" / "START_NEW_CHAT_PROMPT.md"
    start_prompt.parent.mkdir(parents=True)
    start_prompt.write_text("stable start prompt\n", encoding="utf-8")

    def fake_run(command, *, cwd=None):
        import subprocess

        if command == ["git", "rev-parse", "HEAD"]:
            return subprocess.CompletedProcess(command, 0, "new\n", "")
        if command == ["git", "merge-base", "--is-ancestor", "old", "new"]:
            return subprocess.CompletedProcess(command, 0, "", "")
        if command == ["git", "diff", "--name-only", "old..new"]:
            return subprocess.CompletedProcess(command, 0, "src/agentic_project_kit/product.py\n", "")
        return subprocess.CompletedProcess(command, 1, "", "unexpected command")

    monkeypatch.setattr(actions, "_run", fake_run)

    findings = actions._successor_package_freshness_findings(tmp_path)
    assert findings == ["validation_report.json generated_head does not match HEAD or refresh-only ancestry"]

def test_remote_mutation_preflight_blocks_unreachable_remote_directly(monkeypatch):
    calls = []

    def fake_run(command, cwd=None):
        calls.append(command)
        if command == ["git", "branch", "--show-current"]:
            return subprocess.CompletedProcess(command, 0, "feature/example\n", "")
        if command == ["git", "ls-remote", "--exit-code", "origin", "HEAD"]:
            return subprocess.CompletedProcess(command, 128, "", "fatal: unable to access remote\n")
        return subprocess.CompletedProcess(command, 99, "", "unexpected command\n")

    monkeypatch.setattr(transfer_repo_actions, "_run", fake_run)

    result = transfer_repo_actions._remote_mutation_preflight(
        action="pr-create",
        mutation="pr-create",
        required_branch="feature/example",
    )

    assert result is not None
    assert result.result_status == "FAIL"
    assert result.returncode == 2
    assert "STATE=REMOTE_UNREACHABLE" in result.next_action
    assert calls == [
        ["git", "branch", "--show-current"],
        ["git", "ls-remote", "--exit-code", "origin", "HEAD"],
    ]


def test_remote_mutation_preflight_blocks_branch_drift_directly(monkeypatch):
    calls = []

    def fake_run(command, cwd=None):
        calls.append(command)
        if command == ["git", "ls-remote", "--exit-code", "origin", "HEAD"]:
            return subprocess.CompletedProcess(command, 0, "ref\tHEAD\n", "")
        if command == ["git", "branch", "--show-current"]:
            return subprocess.CompletedProcess(command, 0, "feature/other\n", "")
        return subprocess.CompletedProcess(command, 99, "", "unexpected command\n")

    monkeypatch.setattr(transfer_repo_actions, "_run", fake_run)

    result = transfer_repo_actions._remote_mutation_preflight(
        action="pr-create",
        mutation="pr-create",
        required_branch="feature/example",
    )

    assert result is not None
    assert result.result_status == "FAIL"
    assert result.returncode == 2
    assert "STATE=REMOTE_DRIFT" in result.next_action
    assert calls == [["git", "branch", "--show-current"]]



def test_pr_create_recovers_existing_pull_request(monkeypatch):
    calls = []

    class ContinueMonitor:
        decision = transfer_repo_actions.MonitorDecision.CONTINUE
        actual_branch = "feature/example"
        required_branch = "feature/example"
        reason = "test_continue"

    def fake_run(command, cwd=None):
        calls.append(command)
        if command == ["git", "branch", "--show-current"]:
            return subprocess.CompletedProcess(command, 0, "feature/example\n", "")
        if command == ["git", "ls-remote", "--exit-code", "origin", "HEAD"]:
            return subprocess.CompletedProcess(command, 0, "ref\tHEAD\n", "")
        if command == ["git", "rev-parse", "HEAD"]:
            return subprocess.CompletedProcess(command, 0, "abc123\n", "")
        if command == ["git", "ls-remote", "--exit-code", "--heads", "origin", "feature/example"]:
            return subprocess.CompletedProcess(command, 0, "abc123\trefs/heads/feature/example\n", "")
        if command[:3] == ["gh", "pr", "create"]:
            return subprocess.CompletedProcess(command, 1, "", "a pull request already exists for feature/example\n")
        if command[:3] == ["gh", "pr", "list"]:
            return subprocess.CompletedProcess(
                command,
                0,
                '[{"number": 42, "state": "OPEN", "url": "https://example.invalid/pr/42", "headRefName": "feature/example", "baseRefName": "main", "title": "Existing"}]\n',
                "",
            )
        return subprocess.CompletedProcess(command, 99, "", f"unexpected command: {command}\n")

    monkeypatch.setattr(transfer_repo_actions, "_run", fake_run)
    monkeypatch.setattr(transfer_repo_actions, "guard_pr_create", lambda **kwargs: ContinueMonitor())

    result = transfer_repo_actions.pr_create(
        base="main",
        head="feature/example",
        title="Example",
        body="Body",
    )

    assert result.result_status == "PASS"
    assert result.returncode == 0
    assert "STATE=PR_EXISTS" in result.stdout
    assert "STATE=PR_EXISTS" in result.next_action
    assert any(command[:3] == ["gh", "pr", "list"] for command in calls)


def test_pr_create_blocks_stale_remote_head_before_gh_call(monkeypatch):
    calls = []

    class ContinueMonitor:
        decision = transfer_repo_actions.MonitorDecision.CONTINUE
        actual_branch = "feature/example"
        required_branch = "feature/example"
        reason = "test_continue"

    def fake_run(command, cwd=None):
        calls.append(command)
        if command == ["git", "branch", "--show-current"]:
            return subprocess.CompletedProcess(command, 0, "feature/example\n", "")
        if command == ["git", "ls-remote", "--exit-code", "origin", "HEAD"]:
            return subprocess.CompletedProcess(command, 0, "ref\tHEAD\n", "")
        if command == ["git", "rev-parse", "HEAD"]:
            return subprocess.CompletedProcess(command, 0, "local123\n", "")
        if command == ["git", "ls-remote", "--exit-code", "--heads", "origin", "feature/example"]:
            return subprocess.CompletedProcess(command, 0, "remote456\trefs/heads/feature/example\n", "")
        return subprocess.CompletedProcess(command, 99, "", f"unexpected command: {command}\n")

    monkeypatch.setattr(transfer_repo_actions, "_run", fake_run)
    monkeypatch.setattr(transfer_repo_actions, "guard_pr_create", lambda **kwargs: ContinueMonitor())

    result = transfer_repo_actions.pr_create(
        base="main",
        head="feature/example",
        title="Example",
        body="Body",
    )

    assert result.returncode == 2
    assert result.result_status == "FAIL"
    assert "does not match local HEAD" in result.stderr
    assert not any(command[:3] == ["gh", "pr", "create"] for command in calls)


def test_pr_create_auto_pushes_missing_remote_head_before_gh_call(monkeypatch):
    calls = []
    head_lookup_count = 0
    push_calls = []

    class ContinueMonitor:
        decision = transfer_repo_actions.MonitorDecision.CONTINUE
        actual_branch = "feature/example"
        required_branch = "feature/example"
        reason = "test_continue"

    def fake_run(command, cwd=None):
        nonlocal head_lookup_count
        calls.append(command)
        if command == ["git", "branch", "--show-current"]:
            return subprocess.CompletedProcess(command, 0, "feature/example\n", "")
        if command == ["git", "ls-remote", "--exit-code", "origin", "HEAD"]:
            return subprocess.CompletedProcess(command, 0, "ref\tHEAD\n", "")
        if command == ["git", "rev-parse", "HEAD"]:
            return subprocess.CompletedProcess(command, 0, "local123\n", "")
        if command == ["git", "ls-remote", "--exit-code", "--heads", "origin", "feature/example"]:
            head_lookup_count += 1
            if head_lookup_count == 1:
                return subprocess.CompletedProcess(command, 2, "", "missing\n")
            return subprocess.CompletedProcess(command, 0, "local123\trefs/heads/feature/example\n", "")
        if command[:3] == ["gh", "pr", "create"]:
            return subprocess.CompletedProcess(command, 0, "https://example.invalid/pr/42\n", "")
        return subprocess.CompletedProcess(command, 99, "", f"unexpected command: {command}\n")

    def fake_push_current(required_branch=""):
        push_calls.append(required_branch)
        return transfer_repo_actions.RepoActionResult(
            "push-current",
            "PASS",
            0,
            ["push-current"],
            "pushed\n",
            "",
            "Create or inspect pull request.",
        )

    monkeypatch.setattr(transfer_repo_actions, "_run", fake_run)
    monkeypatch.setattr(transfer_repo_actions, "guard_pr_create", lambda **kwargs: ContinueMonitor())
    monkeypatch.setattr(transfer_repo_actions, "push_current", fake_push_current)

    result = transfer_repo_actions.pr_create(
        base="main",
        head="feature/example",
        title="Example",
        body="Body",
    )

    assert result.returncode == 0
    assert result.result_status == "PASS"
    assert push_calls == ["feature/example"]
    assert any(command[:3] == ["gh", "pr", "create"] for command in calls)


def test_already_merged_pr_result_returns_idempotent_pass(monkeypatch):
    calls = []

    def fake_run(command, cwd=None):
        calls.append(command)
        if command[:4] == ["gh", "pr", "view", "42"]:
            return subprocess.CompletedProcess(
                command,
                0,
                '{"number": 42, "state": "MERGED", "merged": true, "headRefOid": "%s", "url": "https://example.invalid/pr/42", "title": "Merged"}\n' % ("a" * 40),
                "",
            )
        return subprocess.CompletedProcess(command, 99, "", f"unexpected command: {command}\n")

    monkeypatch.setattr(transfer_repo_actions, "_run", fake_run)

    command = ["agentic-kit", "pr", "merge-if-green", "42"]
    result = transfer_repo_actions._already_merged_pr_result(
        42,
        action="pr-merge-safe",
        command=command,
    )

    assert result is not None
    assert result.result_status == "PASS"
    assert result.returncode == 0
    assert result.command == command
    assert "STATE=ALREADY_MERGED" in result.stdout
    assert "STATE=ALREADY_MERGED" in result.next_action
    assert calls == [["gh", "pr", "view", "42", "--json", "number,state,merged,headRefOid,url,title"]]


def test_pr_complete_auto_runs_admin_refresh_when_successor_package_is_stale():
    """The PR lifecycle must not leave successor handoff refresh as manual follow-up."""
    import inspect
    import agentic_project_kit.cli_commands.transfer as transfer_cli
    source = inspect.getsource(transfer_cli.pr_complete_command)
    assert "NEEDS_SUCCESSOR_PACKAGE_REFRESH" in source
    assert "admin-refresh-pr" in source
    assert "admin-refresh-pr-complete" in source
    assert "post-merge-check-after-admin-refresh-complete" in source
    assert "post-merge-check_still_requires_successor_refresh" in source
    assert "Run transfer post-merge-check and admin-refresh-pr if requested" not in source
def test_admin_refresh_pr_command_signature_stays_canonical():
    """The canonical admin refresh wrapper must remain the small safe interface."""
    import inspect
    import agentic_project_kit.cli_commands.transfer as transfer_cli
    source = inspect.getsource(transfer_cli.admin_refresh_pr_command)
    assert "--after-pr" in source
    assert "--main-branch" in source
    assert "--json" in source
    assert "--merge-method" not in source
    assert "--title" not in source
    assert "--body" not in source


def test_pr_create_complete_skips_outer_followup_when_inner_pr_complete_verified_admin_refresh():
    """Outer pr-create-complete must not turn red after inner auto admin refresh succeeded."""
    import inspect

    import agentic_project_kit.cli_commands.transfer as transfer_cli

    source = inspect.getsource(transfer_cli.pr_create_complete_command)

    assert "post_merge_complete_verified_by_inner_pr_complete" in source
    assert "post_merge_complete_followup_required" in source
    assert "created, completed, and verified" in source
    assert "and not inner_post_merge_followup_verified" in source
    assert "post-pr-sync-main-after-complete" in source


def test_pr_create_complete_clears_outer_sync_false_red_when_pr_merged_and_post_merge_check_green():
    """Outer pr-create-complete may clear non-fatal follow-up blockers after green post-merge-check."""
    import inspect

    import agentic_project_kit.cli_commands.transfer as transfer_cli

    source = inspect.getsource(transfer_cli.pr_create_complete_command)

    assert "outer_followup_false_red_is_safe_to_clear" in source
    assert "outer-followup-pr-merged-check" in source
    assert "outer-followup-sync-main-before-post-merge-check" in source
    assert "outer-followup-post-merge-check-green-check" in source
    assert "outer_followup_false_red_cleared" in source
    assert "isMerged" not in source
    assert "mergedAt" in source
    assert "non-fatal sync/restore failure" in source
    assert "post-merge-check is green" in source
