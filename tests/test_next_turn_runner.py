from __future__ import annotations

import json

from pathlib import Path

from agentic_project_kit import next_turn_runner
from agentic_project_kit.next_turn_runner import run_fixed_slot, work_result_from_outcome
from agentic_project_kit.next_turn_slot import write_fixed_slot


def _redirect_latest_paths(tmp_path: Path, monkeypatch) -> tuple[Path, Path]:
    terminal = tmp_path / "local" / "next-turn-latest.log"
    report = tmp_path / "local" / "next-turn-latest.json"
    monkeypatch.setattr(next_turn_runner, "LATEST_TERMINAL_LOG", terminal)
    monkeypatch.setattr(next_turn_runner, "LATEST_COMMAND_REPORT", report)
    return terminal, report


def test_run_fixed_slot_reports_missing_slot(tmp_path, monkeypatch):
    terminal, report = _redirect_latest_paths(tmp_path, monkeypatch)
    result = run_fixed_slot(tmp_path)
    assert result.outcome == "FAIL_NO_FIXED_SLOT"
    assert result.exit_code == 2
    assert terminal.exists()
    assert report.exists()
    assert not (tmp_path / "docs/reports/terminal/next-turn-latest.log").exists()


def test_run_fixed_slot_executes_placeholder(tmp_path, monkeypatch):
    terminal, report_path = _redirect_latest_paths(tmp_path, monkeypatch)
    write_fixed_slot(tmp_path, command_id="abc")
    result = run_fixed_slot(tmp_path)
    assert result.outcome == "PASS_EXECUTED"
    assert result.exit_code == 0
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["command_id"] == "abc"
    assert report["outcome"] == "PASS_EXECUTED"
    assert "NEXT_TURN_FIXED_SLOT_PLACEHOLDER" in terminal.read_text(encoding="utf-8")
    assert not (tmp_path / "docs/reports/terminal/next-turn-latest.log").exists()



def test_run_fixed_slot_removes_slot_after_success(tmp_path, monkeypatch):
    terminal, report = _redirect_latest_paths(tmp_path, monkeypatch)
    write_fixed_slot(tmp_path, command_id="cleanup")
    result = run_fixed_slot(tmp_path)
    assert result.outcome == "PASS_EXECUTED"
    assert not (tmp_path / ".agentic/commands/inbox/next-turn.yaml").exists()
    assert not (tmp_path / ".agentic/commands/inbox/next-turn.py").exists()
    assert terminal.exists()
    assert report.exists()
    assert not (tmp_path / "docs/reports/terminal/next-turn-latest.log").exists()



def test_run_fixed_slot_keeps_slot_after_failure(tmp_path, monkeypatch):
    _redirect_latest_paths(tmp_path, monkeypatch)
    write_fixed_slot(tmp_path, command_id="fail")
    script = tmp_path / ".agentic/commands/inbox/next-turn.py"
    script.write_text("raise SystemExit(7)\n", encoding="utf-8")
    result = run_fixed_slot(tmp_path)
    assert result.outcome == "FAIL_EXECUTED"
    assert result.exit_code == 7
    assert (tmp_path / ".agentic/commands/inbox/next-turn.yaml").exists()
    assert (tmp_path / ".agentic/commands/inbox/next-turn.py").exists()



def test_work_result_from_outcome():
    assert work_result_from_outcome("PASS_EXECUTED") == "PASS"
    assert work_result_from_outcome("FAIL_EXECUTED") == "FAIL"
    assert work_result_from_outcome("FAIL_NO_FIXED_SLOT") == "FAIL"



def test_next_turn_run_publish_evidence_no_push_cli(tmp_path):
    import subprocess
    import sys

    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=tmp_path, check=True)
    subprocess.run(["git", "switch", "-c", "feature/publish-cli"], cwd=tmp_path, check=True, capture_output=True, text=True)
    write_fixed_slot(tmp_path, command_id="publish-cli")
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "agentic_project_kit.next_turn_runner",
            "--publish-evidence",
            "--run-id",
            "publish-cli",
            "--no-push",
        ],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0
    assert "NEXT_TURN_EVIDENCE_FINALIZE_RESULT" in completed.stdout
    assert "committed=true" in completed.stdout
    assert "pushed=false" in completed.stdout
    assert (tmp_path / "docs/reports/terminal/publish-cli.log").exists()
    assert (tmp_path / "docs/reports/command_runs/publish-cli.json").exists()
