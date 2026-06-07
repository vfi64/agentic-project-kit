from __future__ import annotations

import json
import subprocess

from typer.testing import CliRunner

from agentic_project_kit.cli import app


def _completed(argv: list[str], stdout: str = "", stderr: str = "", returncode: int = 0):
    return subprocess.CompletedProcess(argv, returncode, stdout, stderr)


def test_restore_known_volatile_restores_only_known_paths(monkeypatch):
    calls: list[list[str]] = []

    def fake_run(argv, cwd=None, text=None, capture_output=None, check=None):
        calls.append(list(argv))
        return _completed(list(argv))

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = CliRunner().invoke(app, ["transfer", "restore-known-volatile", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["result_status"] == "PASS"
    assert calls == [
        [
            "git",
            "restore",
            "--",
            ".agentic/transfer/outbox/last_result.txt",
            "docs/reports/terminal/transfer_handoff_reports/latest-transfer-handoff-report.json",
            "docs/reports/terminal/transfer_handoff_reports/latest-transfer-handoff-report.log",
        ]
    ]


def test_divergence_status_reports_ahead_behind(monkeypatch):
    def fake_run(argv, cwd=None, text=None, capture_output=None, check=None):
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

    def fake_run(argv, cwd=None, text=None, capture_output=None, check=None):
        calls.append(list(argv))
        return _completed(list(argv), stdout="ok\n")

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = CliRunner().invoke(app, ["transfer", "sync-main", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["result_status"] == "PASS"
    assert calls == [
        [
            "git",
            "restore",
            "--",
            ".agentic/transfer/outbox/last_result.txt",
            "docs/reports/terminal/transfer_handoff_reports/latest-transfer-handoff-report.json",
            "docs/reports/terminal/transfer_handoff_reports/latest-transfer-handoff-report.log",
        ],
        ["./.venv/bin/agentic-kit", "rules", "acknowledge"],
        ["./.venv/bin/agentic-kit", "transfer", "branch-switch", "main", "--pull"],
        ["./.venv/bin/agentic-kit", "rules", "acknowledge"],
        ["./.venv/bin/agentic-kit", "transfer", "normalize-session", "--repair-known-volatile"],
    ]


def test_command_reference_refresh_runs_generator_and_reports_changed_files(monkeypatch):
    def fake_run(argv, cwd=None, text=None, capture_output=None, check=None):
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

    def fake_run(argv, cwd=None, text=None, capture_output=None, check=None):
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

    def fake_run(argv, cwd=None, text=None, capture_output=None, check=None):
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

    def fake_run(argv, cwd=None, text=None, capture_output=None, check=None):
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
    def fake_run(argv, cwd=None, text=None, capture_output=None, check=None):
        return _completed(list(argv), stdout="ok\n")

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = CliRunner().invoke(app, ["transfer", "sync-main"])

    assert result.exit_code == 0
    assert "TRANSFER_SYNC_MAIN" in result.stdout
    assert "START SUMMARY" in result.stdout
    assert '"steps"' not in result.stdout
    assert '"argv"' not in result.stdout


def test_sync_main_json_output_keeps_steps(monkeypatch):
    def fake_run(argv, cwd=None, text=None, capture_output=None, check=None):
        return _completed(list(argv), stdout="ok\n")

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = CliRunner().invoke(app, ["transfer", "sync-main", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["action"] == "sync-main"
    assert "steps" in payload


def test_remote_work_start_default_output_is_concise(monkeypatch):
    def fake_run(argv, cwd=None, text=None, capture_output=None, check=None):
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
    def fake_run(argv, cwd=None, text=None, capture_output=None, check=None):
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
