from __future__ import annotations

import json

from agentic_project_kit.next_turn_runner import run_fixed_slot
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
