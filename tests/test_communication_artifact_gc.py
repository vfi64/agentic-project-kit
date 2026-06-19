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


def test_gc_collects_untracked_next_turn_working_artifacts(tmp_path: Path) -> None:
    import subprocess

    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=tmp_path, check=True)
    (tmp_path / "README.md").write_text("repo\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=tmp_path, check=True, capture_output=True, text=True)

    terminal = tmp_path / "docs/reports/terminal/next-turn-latest.log"
    report = tmp_path / "docs/reports/command_runs/next-turn-latest.json"
    terminal.parent.mkdir(parents=True)
    report.parent.mkdir(parents=True)
    terminal.write_text("local only\n", encoding="utf-8")
    report.write_text("{}\n", encoding="utf-8")

    outcome, message = execute_gc(tmp_path)

    assert outcome == "PASS_COLLECTED"
    assert "docs/reports/terminal/next-turn-latest.log" in message
    assert "docs/reports/command_runs/next-turn-latest.json" in message
    assert not terminal.exists()
    assert not report.exists()


def test_gc_keeps_tracked_next_turn_working_artifacts(tmp_path: Path) -> None:
    import subprocess

    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=tmp_path, check=True)
    terminal = tmp_path / "docs/reports/terminal/next-turn-latest.log"
    terminal.parent.mkdir(parents=True)
    terminal.write_text("tracked evidence\n", encoding="utf-8")
    subprocess.run(["git", "add", terminal.as_posix()], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-m", "Track log"], cwd=tmp_path, check=True, capture_output=True, text=True)

    outcome, message = execute_gc(tmp_path)

    assert outcome == "PASS_NOTHING_TO_COLLECT"
    assert message == ""
    assert terminal.read_text(encoding="utf-8") == "tracked evidence\n"


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

def test_transfer_run_gc_keeps_latest_and_collects_expired_reports(tmp_path: Path) -> None:
    import os
    from agentic_project_kit.communication_artifact_gc import (
        collect_expired_transfer_run_reports,
        execute_transfer_run_report_gc,
    )

    base = tmp_path / "docs" / "reports" / "transfer_runs"
    base.mkdir(parents=True)
    stale = base / "20260604T000000Z-old.log"
    latest = base / "latest-transfer-report.log"
    fresh = base / "fresh.log"
    stale.write_text("old\n", encoding="utf-8")
    latest.write_text("latest\n", encoding="utf-8")
    fresh.write_text("fresh\n", encoding="utf-8")
    now = 1_000_000.0
    old_time = now - (2 * 24 * 60 * 60)
    fresh_time = now - 60
    os.utime(stale, (old_time, old_time))
    os.utime(latest, (old_time, old_time))
    os.utime(fresh, (fresh_time, fresh_time))

    found = collect_expired_transfer_run_reports(tmp_path, now=now)

    assert found == [stale]

    outcome, message = execute_transfer_run_report_gc(tmp_path, execute=False, now=now)
    assert outcome == "PENDING_EXPIRED_TRANSFER_RUN_REPORTS"
    assert "20260604T000000Z-old.log" in message
    assert stale.exists()

    outcome, message = execute_transfer_run_report_gc(tmp_path, execute=True, now=now)
    assert outcome == "PASS_COLLECTED"
    assert "20260604T000000Z-old.log" in message
    assert not stale.exists()
    assert latest.exists()
    assert fresh.exists()


def test_tmp_log_gc_keeps_protected_names_and_last_n_logs(tmp_path: Path) -> None:
    import os
    from agentic_project_kit.communication_artifact_gc import collect_expired_tmp_logs

    now = 1_000_000.0
    old_time = now - (2 * 24 * 60 * 60)

    protected = tmp_path / "local-gc-last.json"
    protected.write_text("{}\n", encoding="utf-8")
    os.utime(protected, (old_time, old_time))

    logs = []
    for index in range(4):
        log = tmp_path / f"slice-test-{index}.log"
        log.write_text("old\n", encoding="utf-8")
        os.utime(log, (old_time + index, old_time + index))
        logs.append(log)

    found = collect_expired_tmp_logs(tmp_path, now=now, keep_last=2)

    assert protected not in found
    assert logs[0] in found
    assert logs[1] in found
    assert logs[2] not in found
    assert logs[3] not in found

def test_artifact_gc_cli_transfer_runs_dry_run(tmp_path: Path, monkeypatch) -> None:
    import os
    from typer.testing import CliRunner
    from agentic_project_kit.cli import app

    base = tmp_path / "docs" / "reports" / "transfer_runs"
    base.mkdir(parents=True)
    stale = base / "old.log"
    latest = base / "latest-transfer-report.log"
    stale.write_text("old\n", encoding="utf-8")
    latest.write_text("latest\n", encoding="utf-8")
    old_time = 1_000_000.0 - (2 * 24 * 60 * 60)
    os.utime(stale, (old_time, old_time))
    os.utime(latest, (old_time, old_time))

    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["artifact-gc", "--transfer-runs"])

    assert result.exit_code == 0
    assert "PENDING_EXPIRED_TRANSFER_RUN_REPORTS" in result.output
    assert "old.log" in result.output
    assert stale.exists()
    assert latest.exists()


def test_artifact_gc_cli_rejects_two_modes() -> None:
    from typer.testing import CliRunner
    from agentic_project_kit.cli import app

    result = CliRunner().invoke(app, ["artifact-gc", "--tmp-logs", "--transfer-runs"])

    assert result.exit_code == 1
    assert "FAIL_MUTUALLY_EXCLUSIVE_MODES" in result.output

