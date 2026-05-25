from pathlib import Path

from agentic_project_kit.next_turn_status import (
    detect_next_turn_status,
    render_last_result,
    render_status,
)


def test_next_turn_status_empty_slot(tmp_path: Path) -> None:
    status = detect_next_turn_status(tmp_path)
    assert status.state == "empty"
    assert status.overwrite_allowed is True
    rendered = render_status(status)
    assert "state=empty" in rendered
    assert "docs/reports/command_runs/next-turn-latest.json" in rendered


def test_next_turn_status_blocks_partial_slot(tmp_path: Path) -> None:
    commands = tmp_path / ".agentic" / "commands"
    commands.mkdir(parents=True)
    (commands / "next-turn.yaml").write_text("state: prepared\n", encoding="utf-8")
    status = detect_next_turn_status(tmp_path)
    assert status.state == "blocked"
    assert status.overwrite_allowed is False
    assert status.reason == "partial fixed-slot state"


def test_next_turn_status_reads_declared_state(tmp_path: Path) -> None:
    commands = tmp_path / ".agentic" / "commands"
    commands.mkdir(parents=True)
    (commands / "next-turn.yaml").write_text("id: next-turn\nstate: running\n", encoding="utf-8")
    (commands / "next-turn.py").write_text("pass\n", encoding="utf-8")
    status = detect_next_turn_status(tmp_path)
    assert status.state == "running"
    assert status.overwrite_allowed is False
    assert "running slot must not be overwritten" in status.reason


def test_next_turn_last_result_no_result_is_clean_state(tmp_path: Path) -> None:
    rendered = render_last_result(tmp_path)
    assert "status=NO_RESULT_FOUND" in rendered
    assert "docs/reports/terminal/next-turn-latest.log" in rendered
    assert "### RESULT: PASS ###" in rendered


def test_next_turn_last_result_prefers_json(tmp_path: Path) -> None:
    result_dir = tmp_path / "docs" / "reports" / "command_runs"
    result_dir.mkdir(parents=True)
    (result_dir / "next-turn-latest.json").write_text("{\"overall_result\": \"PASS\"}", encoding="utf-8")
    rendered = render_last_result(tmp_path)
    assert "status=FOUND" in rendered
    assert "next-turn-latest.json" in rendered
    assert "\"overall_result\": \"PASS\"" in rendered
