from __future__ import annotations

import json

from agentic_project_kit.next_turn_runner import run_fixed_slot, work_result_from_outcome
from agentic_project_kit.next_turn_slot import write_fixed_slot


def test_run_fixed_slot_reports_missing_slot(tmp_path):
    result = run_fixed_slot(tmp_path)
    assert result.outcome == "FAIL_NO_FIXED_SLOT"
    assert result.exit_code == 2
    assert (tmp_path / "docs/reports/terminal/next-turn-latest.log").exists()
    assert (tmp_path / "docs/reports/command_runs/next-turn-latest.json").exists()


def test_run_fixed_slot_executes_placeholder(tmp_path):
    write_fixed_slot(tmp_path, command_id="abc")
    result = run_fixed_slot(tmp_path)
    assert result.outcome == "PASS_EXECUTED"
    assert result.exit_code == 0
    report = json.loads((tmp_path / "docs/reports/command_runs/next-turn-latest.json").read_text(encoding="utf-8"))
    assert report["command_id"] == "abc"
    assert report["outcome"] == "PASS_EXECUTED"
    assert "NEXT_TURN_FIXED_SLOT_PLACEHOLDER" in (tmp_path / "docs/reports/terminal/next-turn-latest.log").read_text(encoding="utf-8")



def test_run_fixed_slot_removes_slot_after_success(tmp_path):
    write_fixed_slot(tmp_path, command_id="cleanup")
    result = run_fixed_slot(tmp_path)
    assert result.outcome == "PASS_EXECUTED"
    assert not (tmp_path / ".agentic/commands/inbox/next-turn.yaml").exists()
    assert not (tmp_path / ".agentic/commands/inbox/next-turn.py").exists()
    assert (tmp_path / "docs/reports/terminal/next-turn-latest.log").exists()
    assert (tmp_path / "docs/reports/command_runs/next-turn-latest.json").exists()



def test_run_fixed_slot_keeps_slot_after_failure(tmp_path):
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
