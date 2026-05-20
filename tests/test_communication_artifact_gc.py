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


def test_tmp_log_gc_collects_only_expired_local_tmp_logs(tmp_path: Path) -> None:
    import os
    from agentic_project_kit.communication_artifact_gc import collect_expired_tmp_logs
    expired = tmp_path / "agentic-project-kit-expired.log"
    fresh = tmp_path / "agentic-project-kit-fresh.log"
    other = tmp_path / "other.log"
    expired.write_text("old", encoding="utf-8")
    fresh.write_text("new", encoding="utf-8")
    other.write_text("other", encoding="utf-8")
    now = 1_000_000.0
    old_time = now - (2 * 24 * 60 * 60)
    fresh_time = now - 60
    os.utime(expired, (old_time, old_time))
    os.utime(fresh, (fresh_time, fresh_time))
    found = collect_expired_tmp_logs(tmp_path, now=now)
    assert found == [expired]


def test_tmp_log_gc_dry_run_does_not_delete_expired_log(tmp_path: Path) -> None:
    import os
    from agentic_project_kit.communication_artifact_gc import execute_tmp_log_gc
    expired = tmp_path / "agentic-project-kit-expired.log"
    expired.write_text("old", encoding="utf-8")
    now = 1_000_000.0
    old_time = now - (2 * 24 * 60 * 60)
    os.utime(expired, (old_time, old_time))
    outcome, message = execute_tmp_log_gc(tmp_path, execute=False, now=now)
    assert outcome == "PENDING_EXPIRED_TMP_LOGS"
    assert expired.as_posix() in message
    assert expired.exists()


def test_tmp_log_gc_execute_deletes_only_expired_log(tmp_path: Path) -> None:
    import os
    from agentic_project_kit.communication_artifact_gc import execute_tmp_log_gc
    expired = tmp_path / "agentic-project-kit-expired.log"
    fresh = tmp_path / "agentic-project-kit-fresh.log"
    expired.write_text("old", encoding="utf-8")
    fresh.write_text("new", encoding="utf-8")
    now = 1_000_000.0
    old_time = now - (2 * 24 * 60 * 60)
    fresh_time = now - 60
    os.utime(expired, (old_time, old_time))
    os.utime(fresh, (fresh_time, fresh_time))
    outcome, message = execute_tmp_log_gc(tmp_path, execute=True, now=now)
    assert outcome == "PASS_COLLECTED"
    assert expired.as_posix() in message
    assert not expired.exists()
    assert fresh.exists()


def test_tmp_log_gc_ignores_symlink(tmp_path: Path) -> None:
    from agentic_project_kit.communication_artifact_gc import collect_expired_tmp_logs
    target = tmp_path / "target.log"
    target.write_text("keep", encoding="utf-8")
    link = tmp_path / "agentic-project-kit-link.log"
    link.symlink_to(target)
    assert collect_expired_tmp_logs(tmp_path, now=1_000_000.0) == []
    assert link.is_symlink()
    assert target.exists()
