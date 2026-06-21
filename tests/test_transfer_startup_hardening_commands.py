from __future__ import annotations

import json
import subprocess
from pathlib import Path

from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.cli_commands.transfer import _restore_known_volatile_paths


def _completed(argv: list[str], stdout: str = "", stderr: str = "", returncode: int = 0):
    return subprocess.CompletedProcess(argv, returncode, stdout, stderr)


def test_restore_known_volatile_restores_only_known_paths(monkeypatch):
    calls: list[list[str]] = []

    def fake_run(argv, *args, **kwargs):
        calls.append(list(argv))
        return _completed(list(argv))

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = CliRunner().invoke(app, ["transfer", "restore-known-volatile", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["result_status"] == "PASS"
    assert calls == [
        ["git", "ls-files", "--error-unmatch", ".agentic/transfer/inbox/next_command.py.txt"],
        ["git", "ls-files", "--error-unmatch", ".agentic/transfer/outbox/last_result.txt"],
        [
            "git",
            "ls-files",
            "--error-unmatch",
            "docs/reports/terminal/transfer_handoff_reports/latest-transfer-handoff-report.json",
        ],
        [
            "git",
            "ls-files",
            "--error-unmatch",
            "docs/reports/terminal/transfer_handoff_reports/latest-transfer-handoff-report.log",
        ],
        [
            "git",
            "restore",
            "--",
            ".agentic/transfer/inbox/next_command.py.txt",
            ".agentic/transfer/outbox/last_result.txt",
            "docs/reports/terminal/transfer_handoff_reports/latest-transfer-handoff-report.json",
            "docs/reports/terminal/transfer_handoff_reports/latest-transfer-handoff-report.log",
        ]
    ]


def test_restore_known_volatile_removes_untracked_outbox_and_restores_tracked_reports(tmp_path: Path):
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True, text=True)
    report_dir = tmp_path / "docs/reports/terminal/transfer_handoff_reports"
    report_dir.mkdir(parents=True)
    latest_json = report_dir / "latest-transfer-handoff-report.json"
    latest_log = report_dir / "latest-transfer-handoff-report.log"
    latest_json.write_text('{"state": "old"}\n', encoding="utf-8")
    latest_log.write_text("old\n", encoding="utf-8")
    subprocess.run(["git", "add", str(latest_json), str(latest_log)], cwd=tmp_path, check=True)

    latest_json.write_text('{"state": "new"}\n', encoding="utf-8")
    latest_log.write_text("new\n", encoding="utf-8")
    outbox = tmp_path / ".agentic/transfer/outbox/last_result.txt"
    outbox.parent.mkdir(parents=True)
    outbox.write_text('{"result_status": "PASS"}\n', encoding="utf-8")

    payload = _restore_known_volatile_paths(tmp_path)

    assert payload["ok"] is True
    assert "docs/reports/terminal/transfer_handoff_reports/latest-transfer-handoff-report.json" in payload["tracked_paths"]
    assert ".agentic/transfer/outbox/last_result.txt" in payload["removed_untracked"]
    assert latest_json.read_text(encoding="utf-8") == '{"state": "old"}\n'
    assert latest_log.read_text(encoding="utf-8") == "old\n"
    assert not outbox.exists()


def test_divergence_status_reports_ahead_behind(monkeypatch):
    def fake_run(argv, *args, **kwargs):
        command = list(argv)
        if command == ["git", "branch", "--show-current"]:
            return _completed(command, stdout="feature/demo\n")
        if command == ["git", "rev-parse", "HEAD"]:
            return _completed(command, stdout="abc123\n")
        if command == ["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"]:
            return _completed(command, stdout="origin/feature/demo\n")
        if command == ["git", "rev-parse", "@{u}"]:
            return _completed(command, stdout="def456\n")
        if command == ["git", "rev-list", "--left-right", "--count", "HEAD...@{u}"]:
            return _completed(command, stdout="2\t3\n")
        raise AssertionError(f"unexpected command: {command}")

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = CliRunner().invoke(app, ["transfer", "divergence-status", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["repo"]["branch"] == "feature/demo"
    assert payload["repo"]["head"] == "abc123"
    assert payload["repo"]["upstream"] == "origin/feature/demo"
    assert payload["repo"]["upstream_head"] == "def456"
    assert payload["repo"]["head_matches_upstream"] is False
    assert payload["repo"]["ahead"] == 2
    assert payload["repo"]["behind"] == 3


def test_sync_main_orchestrates_safe_startup_sequence(monkeypatch):
    calls: list[list[str]] = []

    def fake_run(argv, *args, **kwargs):
        calls.append(list(argv))
        return _completed(list(argv), stdout="ok\n")

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = CliRunner().invoke(app, ["transfer", "sync-main", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["result_status"] == "PASS"
    assert calls == [
        ["./.venv/bin/agentic-kit", "transfer", "restore-known-volatile", "--json"],
        ["./.venv/bin/agentic-kit", "rules", "acknowledge"],
        ["./.venv/bin/agentic-kit", "transfer", "branch-switch", "main", "--pull"],
        ["./.venv/bin/agentic-kit", "rules", "acknowledge"],
        ["./.venv/bin/agentic-kit", "transfer", "normalize-session", "--repair-known-volatile"],
    ]


def test_command_reference_refresh_runs_generator_and_reports_changed_files(monkeypatch):
    def fake_run(argv, *args, **kwargs):
        command = list(argv)
        if command == ["./.venv/bin/python", "scripts/generate_agentic_kit_command_reference.py"]:
            return _completed(command, stdout="generated\n")
        if command == ["git", "status", "--short"]:
            return _completed(command, stdout=" M docs/reference/agentic-kit-commands.json\n")
        if command == [
            "git",
            "diff",
            "--name-only",
            "--",
            "docs/reference/agentic-kit-commands.json",
            "docs/reference/AGENTIC_KIT_COMMANDS.md",
        ]:
            return _completed(
                command,
                stdout="docs/reference/agentic-kit-commands.json\ndocs/reference/AGENTIC_KIT_COMMANDS.md\n",
            )
        raise AssertionError(f"unexpected command: {command}")

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = CliRunner().invoke(app, ["transfer", "command-reference-refresh", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["result_status"] == "PASS"
    assert payload["changed_files"] == [
        "docs/reference/agentic-kit-commands.json",
        "docs/reference/AGENTIC_KIT_COMMANDS.md",
    ]


def test_command_reference_check_runs_drift_test(monkeypatch):
    calls: list[list[str]] = []

    def fake_run(argv, *args, **kwargs):
        calls.append(list(argv))
        return _completed(list(argv), stdout="1 passed\n")

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = CliRunner().invoke(app, ["transfer", "command-reference-check", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["result_status"] == "PASS"
    assert calls == [
        [
            "./.venv/bin/python",
            "-m",
            "pytest",
            "-q",
            "tests/test_agentic_kit_command_reference_is_current.py",
        ]
    ]


def test_evidence_inspect_latest_requires_summary(monkeypatch):
    calls: list[list[str]] = []

    def fake_run(argv, *args, **kwargs):
        calls.append(list(argv))
        return _completed(list(argv), stdout="PASS\n")

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = CliRunner().invoke(app, ["transfer", "evidence-inspect-latest", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["result_status"] == "PASS"
    assert calls == [["./.venv/bin/agentic-kit", "evidence", "inspect", "--require-summary"]]


def test_evidence_finalize_current_transfer_builds_finalize_log_command(monkeypatch):
    calls: list[list[str]] = []

    def fake_run(argv, *args, **kwargs):
        calls.append(list(argv))
        return _completed(list(argv), stdout="finalized\n")

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = CliRunner().invoke(
        app,
        [
            "transfer",
            "evidence-finalize-current-transfer",
            "--slice",
            "demo slice",
            "--run-log",
            "docs/reports/transfer_runs/latest-transfer-report.log",
            "--remote-log",
            "docs/reports/terminal/demo.log",
            "--pr",
            "123",
            "--ci",
            "green",
            "--merge",
            "merged",
            "--branch",
            "feature/demo",
            "--json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["result_status"] == "PASS"
    assert calls == [
        [
            "./.venv/bin/agentic-kit",
            "evidence",
            "finalize-log",
            "--run-log",
            "docs/reports/transfer_runs/latest-transfer-report.log",
            "--remote-log",
            "docs/reports/terminal/demo.log",
            "--slice",
            "demo slice",
            "--scope",
            "transfer",
            "--mode-check",
            "standard",
            "--pr",
            "123",
            "--ci",
            "green",
            "--merge",
            "merged",
            "--command-report",
            "transfer lifecycle completed",
            "--interpretation",
            "Evidence finalized through transfer wrapper.",
            "--safe-step",
            "Continue with the next planned slice.",
            "--branch",
            "feature/demo",
        ]
    ]



def test_sync_main_default_output_is_concise(monkeypatch):
    def fake_run(argv, *args, **kwargs):
        return _completed(list(argv), stdout="ok\n")

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = CliRunner().invoke(app, ["transfer", "sync-main"])

    assert result.exit_code == 0
    assert "TRANSFER_SYNC_MAIN" in result.stdout
    assert "START SUMMARY" in result.stdout
    assert '"steps"' not in result.stdout
    assert '"argv"' not in result.stdout


def test_sync_main_json_output_keeps_steps(monkeypatch):
    def fake_run(argv, *args, **kwargs):
        return _completed(list(argv), stdout="ok\n")

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = CliRunner().invoke(app, ["transfer", "sync-main", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["action"] == "sync-main"
    assert "steps" in payload


def test_remote_work_start_default_output_is_concise(monkeypatch):
    def fake_run(argv, *args, **kwargs):
        command = list(argv)
        if command[:3] == ["./.venv/bin/agentic-kit", "transfer", "branch-create"]:
            return _completed(command, stdout='{"result_status":"PASS"}\n')
        return _completed(command, stdout="ok\n")

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = CliRunner().invoke(app, ["transfer", "remote-work-start", "feature/output-test"])

    assert result.exit_code == 0
    assert "TRANSFER_REMOTE_WORK_START" in result.stdout
    assert "START SUMMARY" in result.stdout
    assert '"steps"' not in result.stdout
    assert '"argv"' not in result.stdout


def test_remote_work_start_json_output_keeps_steps(monkeypatch):
    def fake_run(argv, *args, **kwargs):
        command = list(argv)
        if command[:3] == ["./.venv/bin/agentic-kit", "transfer", "branch-create"]:
            return _completed(command, stdout='{"result_status":"PASS"}\n')
        return _completed(command, stdout="ok\n")

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = CliRunner().invoke(app, ["transfer", "remote-work-start", "feature/output-test", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["action"] == "remote-work-start"
    assert "steps" in payload

def test_evidence_pr_complete_orchestrates_finalize_push_pr_sync_and_post_merge(monkeypatch):
    calls: list[list[str]] = []

    def fake_run(argv, *args, **kwargs):
        command = list(argv)
        calls.append(command)
        if command == ["git", "branch", "--show-current"]:
            return _completed(command, stdout="evidence/demo\n")
        return _completed(command, stdout="ok\n")

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(
        "agentic_project_kit.cli_commands.transfer._require_transfer_capability",
        lambda capability: None,
    )

    result = CliRunner().invoke(
        app,
        [
            "transfer",
            "evidence-pr-complete",
            "--slice",
            "demo",
            "--evidence-branch",
            "evidence/demo",
            "--title",
            "Evidence demo",
            "--body",
            "Evidence body",
            "--source-pr",
            "123",
            "--remote-log",
            "docs/reports/terminal/demo-evidence.log",
            "--json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["result_status"] == "PASS"
    assert payload["action"] == "evidence-pr-complete"
    assert [
        "./.venv/bin/agentic-kit",
        "transfer",
        "evidence-finalize-current-transfer",
        "--slice",
        "demo",
        "--run-log",
        "docs/reports/transfer_runs/latest-transfer-report.log",
        "--scope",
        "transfer",
        "--mode-check",
        "standard",
        "--pr",
        "123",
        "--ci",
        "not-required",
        "--merge",
        "not-required",
        "--command-report",
        "transfer lifecycle completed",
        "--interpretation",
        "Evidence finalized through transfer evidence-pr-complete wrapper.",
        "--safe-step",
        "Continue with the next planned slice.",
        "--branch",
        "evidence/demo",
        "--remote-log",
        "docs/reports/terminal/demo-evidence.log",
    ] in calls
    assert ["./.venv/bin/agentic-kit", "transfer", "evidence-inspect-latest"] in calls
    assert ["./.venv/bin/agentic-kit", "transfer", "push-current", "--branch", "evidence/demo"] in calls
    assert any(call[:3] == ["./.venv/bin/agentic-kit", "transfer", "pr-create-complete"] for call in calls)
    assert ["./.venv/bin/agentic-kit", "transfer", "sync-main"] in calls
    assert ["./.venv/bin/agentic-kit", "transfer", "post-merge-check"] in calls


def test_evidence_pr_complete_switches_or_creates_evidence_branch(monkeypatch):
    calls: list[list[str]] = []

    switch_attempts = 0

    def fake_run(argv, *args, **kwargs):
        nonlocal switch_attempts
        command = list(argv)
        calls.append(command)
        if command == ["git", "branch", "--show-current"]:
            return _completed(command, stdout="feature/source\n")
        if command == ["./.venv/bin/agentic-kit", "transfer", "branch-switch", "evidence/demo"]:
            switch_attempts += 1
            if switch_attempts == 1:
                return _completed(command, returncode=1, stderr="missing branch\n")
            return _completed(command, stdout="switched\n")
        return _completed(command, stdout="ok\n")

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(
        "agentic_project_kit.cli_commands.transfer._require_transfer_capability",
        lambda capability: None,
    )

    result = CliRunner().invoke(
        app,
        [
            "transfer",
            "evidence-pr-complete",
            "--slice",
            "demo",
            "--evidence-branch",
            "evidence/demo",
            "--title",
            "Evidence demo",
        ],
    )

    assert result.exit_code == 0
    assert ["./.venv/bin/agentic-kit", "transfer", "branch-create", "evidence/demo"] in calls
    assert ["./.venv/bin/agentic-kit", "transfer", "branch-switch", "evidence/demo"] in calls


def test_evidence_pr_complete_refuses_main_branch(monkeypatch):
    def fake_run(argv, *args, **kwargs):
        command = list(argv)
        if command == ["git", "branch", "--show-current"]:
            return _completed(command, stdout="main\n")
        return _completed(command, stdout="ok\n")

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(
        "agentic_project_kit.cli_commands.transfer._require_transfer_capability",
        lambda capability: None,
    )

    result = CliRunner().invoke(
        app,
        [
            "transfer",
            "evidence-pr-complete",
            "--slice",
            "demo",
            "--evidence-branch",
            "main",
            "--title",
            "Evidence demo",
        ],
    )

    assert result.exit_code == 2
    assert "refuse_main_branch" in result.stdout


def test_evidence_pr_complete_blocks_on_finalize_failure(monkeypatch):
    calls: list[list[str]] = []

    def fake_run(argv, *args, **kwargs):
        command = list(argv)
        calls.append(command)
        if command == ["git", "branch", "--show-current"]:
            return _completed(command, stdout="evidence/demo\n")
        if command[:3] == ["./.venv/bin/agentic-kit", "transfer", "evidence-finalize-current-transfer"]:
            return _completed(command, returncode=1, stderr="finalize failed\n")
        return _completed(command, stdout="ok\n")

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(
        "agentic_project_kit.cli_commands.transfer._require_transfer_capability",
        lambda capability: None,
    )

    result = CliRunner().invoke(
        app,
        [
            "transfer",
            "evidence-pr-complete",
            "--slice",
            "demo",
            "--evidence-branch",
            "evidence/demo",
            "--title",
            "Evidence demo",
        ],
    )

    assert result.exit_code == 2
    assert "evidence-finalize-current-transfer_failed" in result.stdout
    assert not any(call[:3] == ["./.venv/bin/agentic-kit", "transfer", "pr-create-complete"] for call in calls)

def test_transfer_pr_existing_for_branch_finds_single_pr(monkeypatch):
    calls: list[list[str]] = []

    def fake_run(argv, *args, **kwargs):
        command = list(argv)
        calls.append(command)
        if command[:3] == ["gh", "pr", "list"]:
            return _completed(
                command,
                stdout=json.dumps(
                    [
                        {
                            "number": 123,
                            "url": "https://github.com/example/repo/pull/123",
                            "state": "OPEN",
                            "headRefName": "feature/demo",
                            "baseRefName": "main",
                            "isDraft": False,
                            "mergeStateStatus": "CLEAN",
                        }
                    ]
                ),
            )
        return _completed(command, returncode=99, stderr=f"unexpected command: {command}\n")

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = CliRunner().invoke(
        app,
        [
            "transfer",
            "pr-existing-for-branch",
            "--head",
            "feature/demo",
            "--base",
            "main",
            "--json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["result_status"] == "PASS"
    assert payload["pr_number"] == 123
    assert payload["head"] == "feature/demo"
    assert any(call[:3] == ["gh", "pr", "list"] for call in calls)


def test_transfer_pr_existing_for_branch_resolves_current_branch(monkeypatch):
    calls: list[list[str]] = []

    def fake_run(argv, *args, **kwargs):
        command = list(argv)
        calls.append(command)
        if command == ["git", "branch", "--show-current"]:
            return _completed(command, stdout="feature/current\n")
        if command[:3] == ["gh", "pr", "list"]:
            return _completed(command, stdout="[]")
        return _completed(command, returncode=99, stderr=f"unexpected command: {command}\n")

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = CliRunner().invoke(app, ["transfer", "pr-existing-for-branch", "--head", "current", "--json"])

    assert result.exit_code == 2
    payload = json.loads(result.stdout)
    assert payload["result_status"] == "MISS"
    assert payload["head"] == "feature/current"
    assert "existing_pr_not_found" in payload["blockers"]
    assert ["git", "branch", "--show-current"] in calls


def test_transfer_pr_existing_for_branch_blocks_multiple_matches(monkeypatch):
    def fake_run(argv, *args, **kwargs):
        command = list(argv)
        if command[:3] == ["gh", "pr", "list"]:
            return _completed(command, stdout=json.dumps([{"number": 1}, {"number": 2}]))
        return _completed(command, returncode=99, stderr=f"unexpected command: {command}\n")

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = CliRunner().invoke(
        app,
        ["transfer", "pr-existing-for-branch", "--head", "feature/demo", "--json"],
    )

    assert result.exit_code == 2
    payload = json.loads(result.stdout)
    assert payload["result_status"] == "BLOCKED"
    assert "multiple_existing_prs_found" in payload["blockers"]


def test_transfer_pr_existing_for_branch_reports_gh_failure(monkeypatch):
    def fake_run(argv, *args, **kwargs):
        command = list(argv)
        if command[:3] == ["gh", "pr", "list"]:
            return _completed(command, returncode=1, stderr="gh failed\n")
        return _completed(command, returncode=99, stderr=f"unexpected command: {command}\n")

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = CliRunner().invoke(
        app,
        ["transfer", "pr-existing-for-branch", "--head", "feature/demo", "--json"],
    )

    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert payload["result_status"] == "FAIL"
    assert "gh_pr_list_failed" in payload["blockers"]


def test_command_composition_check_blocks_missing_test_paths(tmp_path: Path):
    existing = tmp_path / "tests" / "test_existing.py"
    existing.parent.mkdir()
    existing.write_text("def test_ok():\n    assert True\n", encoding="utf-8")
    reference = tmp_path / "docs/reference/agentic-kit-commands.json"
    reference.parent.mkdir(parents=True)
    reference.write_text('{"commands": []}\n', encoding="utf-8")

    result = CliRunner().invoke(
        app,
        [
            "transfer",
            "command-composition-check",
            "--root",
            str(tmp_path),
            "--test-path",
            "tests/test_existing.py",
            "--test-path",
            "tests/test_missing.py",
            "--json",
        ],
    )

    assert result.exit_code == 2
    payload = json.loads(result.stdout)
    assert payload["result_status"] == "BLOCKED"
    assert payload["blockers"] == ["missing_test_paths"]
    assert payload["test_paths"]["existing"] == ["tests/test_existing.py"]
    assert payload["test_paths"]["missing"] == ["tests/test_missing.py"]


def test_command_composition_check_blocks_invalid_agentic_kit_command(tmp_path: Path):
    reference = tmp_path / "docs/reference/agentic-kit-commands.json"
    reference.parent.mkdir(parents=True)
    reference.write_text(
        json.dumps(
            {
                "commands": [
                    {"qualified_name": "agentic-kit transfer command-reference-refresh"},
                    {"qualified_name": "agentic-kit release-status"},
                ]
            }
        )
        + "\n",
        encoding="utf-8",
    )

    result = CliRunner().invoke(
        app,
        [
            "transfer",
            "command-composition-check",
            "--root",
            str(tmp_path),
            "--command",
            "agentic-kit transfer command-reference-refresh",
            "--command",
            "agentic-kit " + "command-reference-refresh",
            "--json",
        ],
    )

    assert result.exit_code == 2
    payload = json.loads(result.stdout)
    assert payload["result_status"] == "BLOCKED"
    assert payload["commands"]["valid"] == ["agentic-kit transfer command-reference-refresh"]
    assert payload["commands"]["invalid"] == ["agentic-kit " + "command-reference-refresh"]


def test_command_composition_check_accepts_existing_paths_and_known_commands(tmp_path: Path):
    existing = tmp_path / "tests" / "test_existing.py"
    existing.parent.mkdir()
    existing.write_text("def test_ok():\n    assert True\n", encoding="utf-8")
    reference = tmp_path / "docs/reference/agentic-kit-commands.json"
    reference.parent.mkdir(parents=True)
    reference.write_text(
        json.dumps({"commands": [{"qualified_name": "agentic-kit transfer command-reference-refresh"}]}) + "\n",
        encoding="utf-8",
    )

    result = CliRunner().invoke(
        app,
        [
            "transfer",
            "command-composition-check",
            "--root",
            str(tmp_path),
            "--test-path",
            "tests/test_existing.py",
            "--command",
            "./.venv/bin/agentic-kit transfer command-reference-refresh",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["result_status"] == "PASS"


def test_standard_error_scan_reports_pass_when_guard_steps_pass(monkeypatch, tmp_path: Path):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "docs/reference").mkdir(parents=True)
    (tmp_path / ".agentic").mkdir()
    (tmp_path / "docs/reference/agentic-kit-commands.json").write_text('{"commands": []}\n', encoding="utf-8")

    calls: list[list[str]] = []

    def fake_run(argv, *args, **kwargs):
        command = list(argv)
        calls.append(command)
        if command[:3] == ["./.venv/bin/agentic-kit", "transfer", "require-fresh-llm-context"] and "--allow-clean-post-merge-carrier-staleness" not in command:
            return _completed(command, stdout='{"result_status": "BLOCKED"}\n', returncode=2)
        return _completed(command, stdout='{"result_status": "PASS"}\n')

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = CliRunner().invoke(
        app,
        [
            "transfer",
            "standard-error-scan",
            "--root",
            str(tmp_path),
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["result_status"] == "WARN"
    assert "strict_fresh_context_blocked_but_clean_post_merge_allowance_passed" in payload["warnings"]
    assert any(call[:3] == ["./.venv/bin/agentic-kit", "transfer", "command-composition-check"] for call in calls)


def test_standard_error_scan_blocks_failed_required_step(monkeypatch, tmp_path: Path):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "docs/reference").mkdir(parents=True)
    (tmp_path / ".agentic").mkdir()
    (tmp_path / "docs/reference/agentic-kit-commands.json").write_text('{"commands": []}\n', encoding="utf-8")

    def fake_run(argv, *args, **kwargs):
        command = list(argv)
        if command[:3] == ["./.venv/bin/agentic-kit", "transfer", "repo-status"]:
            return _completed(command, stdout="dirty\n", returncode=1)
        return _completed(command, stdout='{"result_status": "PASS"}\n')

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = CliRunner().invoke(
        app,
        [
            "transfer",
            "standard-error-scan",
            "--root",
            str(tmp_path),
            "--json",
        ],
    )

    assert result.exit_code == 2
    payload = json.loads(result.stdout)
    assert payload["result_status"] == "BLOCKED"
    assert "repo-status" in payload["blockers"]


def test_standard_error_scan_ignores_historical_planning_docs(monkeypatch, tmp_path: Path):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "docs/reference").mkdir(parents=True)
    (tmp_path / "docs/planning").mkdir(parents=True)
    (tmp_path / "docs/planning/ARCHIVE.md").write_text(
        "`./" + "ns merge-if-green <pr>` is an archived legacy example.\n",
        encoding="utf-8",
    )
    (tmp_path / ".agentic").mkdir()
    (tmp_path / "docs/reference/agentic-kit-commands.json").write_text('{"commands": []}\n', encoding="utf-8")

    def fake_run(argv, *args, **kwargs):
        command = list(argv)
        if command[:3] == ["./.venv/bin/agentic-kit", "transfer", "require-fresh-llm-context"] and "--allow-clean-post-merge-carrier-staleness" not in command:
            return _completed(command, stdout='{"result_status": "BLOCKED"}\n', returncode=2)
        return _completed(command, stdout='{"result_status": "PASS"}\n')

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = CliRunner().invoke(
        app,
        [
            "transfer",
            "standard-error-scan",
            "--root",
            str(tmp_path),
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["known_bad_pattern_scan"]["matches"] == []


def test_standard_error_scan_without_before_release_does_not_require_post_merge_check(monkeypatch, tmp_path: Path):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "docs/reference").mkdir(parents=True)
    (tmp_path / ".agentic").mkdir()
    (tmp_path / "docs/reference/agentic-kit-commands.json").write_text('{"commands": []}\n', encoding="utf-8")

    calls: list[list[str]] = []

    def fake_run(argv, *args, **kwargs):
        command = list(argv)
        calls.append(command)
        if command[:3] == ["./.venv/bin/agentic-kit", "transfer", "require-fresh-llm-context"]:
            return _completed(command, stdout='{"result_status": "BLOCKED"}\n', returncode=2)
        return _completed(command, stdout='{"result_status": "PASS"}\n')

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = CliRunner().invoke(
        app,
        [
            "transfer",
            "standard-error-scan",
            "--root",
            str(tmp_path),
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["result_status"] == "WARN"
    assert "fresh_context_stale_in_feature_branch_diagnostic" in payload["warnings"]
    assert not any(call[:3] == ["./.venv/bin/agentic-kit", "transfer", "post-merge-check"] for call in calls)


def test_standard_error_scan_before_release_requires_post_merge_check(monkeypatch, tmp_path: Path):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "docs/reference").mkdir(parents=True)
    (tmp_path / ".agentic").mkdir()
    (tmp_path / "docs/reference/agentic-kit-commands.json").write_text('{"commands": []}\n', encoding="utf-8")

    calls: list[list[str]] = []

    def fake_run(argv, *args, **kwargs):
        command = list(argv)
        calls.append(command)
        return _completed(command, stdout='{"result_status": "PASS"}\n')

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = CliRunner().invoke(
        app,
        [
            "transfer",
            "standard-error-scan",
            "--root",
            str(tmp_path),
            "--before-release",
            "--version",
            "1.2.3",
            "--from-tag",
            "v1.2.2",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    assert any(call[:3] == ["./.venv/bin/agentic-kit", "transfer", "post-merge-check"] for call in calls)
