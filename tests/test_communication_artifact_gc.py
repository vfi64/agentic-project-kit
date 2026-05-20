from __future__ import annotations

from pathlib import Path

from agentic_project_kit.communication_artifact_gc import collect_candidates, execute_gc, render_plan


def test_gc_plan_reports_nothing_for_clean_tree(tmp_path: Path) -> None:
    assert render_plan(collect_candidates(tmp_path)) == "PASS_NOTHING_TO_COLLECT"


def test_gc_collects_only_transient_agent_command_files(tmp_path: Path) -> None:
    commands = tmp_path / ".agentic" / "commands"
    commands.mkdir(parents=True)
    current_yaml = commands / "current.yaml"
    current_sh = commands / "current.sh"
    current_yaml.write_text("stale", encoding="utf-8")
    current_sh.write_text("stale", encoding="utf-8")
    outcome, message = execute_gc(tmp_path)
    assert outcome == "PASS_COLLECTED"
    assert ".agentic/commands/current.yaml" in message
    assert ".agentic/commands/current.sh" in message
    assert not current_yaml.exists()
    assert not current_sh.exists()


def test_gc_does_not_collect_latest_terminal_log_pointer(tmp_path: Path) -> None:
    terminal = tmp_path / "docs" / "reports" / "terminal"
    terminal.mkdir(parents=True)
    pointer = terminal / "LATEST_TERMINAL_LOG.txt"
    pointer.write_text("docs/reports/terminal/example.log\n", encoding="utf-8")
    outcome, message = execute_gc(tmp_path)
    assert outcome == "PASS_NOTHING_TO_COLLECT"
    assert message == ""
    assert pointer.exists()


def test_gc_refuses_to_delete_symlinked_transient_file(tmp_path: Path) -> None:
    commands = tmp_path / ".agentic" / "commands"
    commands.mkdir(parents=True)
    target = tmp_path / "outside.txt"
    target.write_text("keep", encoding="utf-8")
    current_yaml = commands / "current.yaml"
    current_yaml.symlink_to(target)
    outcome, message = execute_gc(tmp_path)
    assert outcome == "FAIL_SYMLINK_ARTIFACT"
    assert ".agentic/commands/current.yaml" in message
    assert current_yaml.is_symlink()
    assert target.read_text(encoding="utf-8") == "keep"


def test_gc_does_not_collect_repo_terminal_logs(tmp_path: Path) -> None:
    terminal = tmp_path / "docs" / "reports" / "terminal"
    terminal.mkdir(parents=True)
    log_file = terminal / "example.log"
    log_file.write_text("evidence", encoding="utf-8")
    outcome, message = execute_gc(tmp_path)
    assert outcome == "PASS_NOTHING_TO_COLLECT"
    assert message == ""
    assert log_file.read_text(encoding="utf-8") == "evidence"


def test_gc_does_not_collect_command_run_reports(tmp_path: Path) -> None:
    reports = tmp_path / "docs" / "reports" / "command_runs"
    reports.mkdir(parents=True)
    report = reports / "example.md"
    report.write_text("# evidence", encoding="utf-8")
    outcome, message = execute_gc(tmp_path)
    assert outcome == "PASS_NOTHING_TO_COLLECT"
    assert message == ""
    assert report.read_text(encoding="utf-8") == "# evidence"


def test_gc_does_not_collect_command_inbox_files(tmp_path: Path) -> None:
    inbox = tmp_path / ".agentic" / "commands" / "inbox"
    inbox.mkdir(parents=True)
    metadata = inbox / "queued.yaml"
    script = inbox / "queued.sh"
    metadata.write_text("name: queued", encoding="utf-8")
    script.write_text("printf queued\n", encoding="utf-8")
    outcome, message = execute_gc(tmp_path)
    assert outcome == "PASS_NOTHING_TO_COLLECT"
    assert message == ""
    assert metadata.exists()
    assert script.exists()
