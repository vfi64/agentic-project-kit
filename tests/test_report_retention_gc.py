from __future__ import annotations

import os
from pathlib import Path

from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.communication_artifact_gc import (
    collect_report_retention_candidates,
    execute_report_retention_gc,
)

OLD_NOW = 2_000_000.0
OLD_MTIME = OLD_NOW - (3 * 24 * 60 * 60)


def _touch(path: Path, *, mtime: float = OLD_MTIME) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("log\n", encoding="utf-8")
    os.utime(path, (mtime, mtime))
    return path


def test_report_retention_gc_dry_run_does_not_delete(tmp_path: Path) -> None:
    target = _touch(tmp_path / "docs/reports/command_runs/old.json")

    outcome, message = execute_report_retention_gc(
        tmp_path,
        execute=False,
        now=OLD_NOW,
        keep_last_per_parent=0,
    )

    assert outcome == "PENDING_EXPIRED_REPORT_RETENTION_FILES"
    assert "docs/reports/command_runs/old.json" in message
    assert target.exists()


def test_report_retention_gc_execute_deletes_candidate(tmp_path: Path) -> None:
    target = _touch(tmp_path / "docs/reports/branch_cleanup/old.log")

    outcome, message = execute_report_retention_gc(
        tmp_path,
        execute=True,
        now=OLD_NOW,
        keep_last_per_parent=0,
    )

    assert outcome == "PASS_COLLECTED"
    assert "docs/reports/branch_cleanup/old.log" in message
    assert not target.exists()


def test_report_retention_gc_keeps_referenced_file(tmp_path: Path) -> None:
    target = _touch(tmp_path / "docs/reports/ns-migration/kept.json")
    reference = tmp_path / "docs/STATUS.md"
    reference.parent.mkdir(parents=True, exist_ok=True)
    reference.write_text("see docs/reports/ns-migration/kept.json\n", encoding="utf-8")

    candidates = collect_report_retention_candidates(
        tmp_path,
        now=OLD_NOW,
        keep_last_per_parent=0,
    )

    assert target.exists()
    assert all(item.path.as_posix() != "docs/reports/ns-migration/kept.json" for item in candidates)


def test_report_retention_gc_keeps_latest_manifest_and_newest_two(tmp_path: Path) -> None:
    old = _touch(tmp_path / "docs/reports/terminal/old.log", mtime=OLD_MTIME)
    newest = _touch(tmp_path / "docs/reports/terminal/newest.log", mtime=OLD_NOW - 100)
    second = _touch(tmp_path / "docs/reports/terminal/second.log", mtime=OLD_NOW - 200)
    latest = _touch(tmp_path / "docs/reports/terminal/latest-terminal.log", mtime=OLD_MTIME)
    manifest = _touch(tmp_path / "docs/reports/terminal/source_manifest.json", mtime=OLD_MTIME)

    candidates = collect_report_retention_candidates(tmp_path, now=OLD_NOW, keep_last_per_parent=2)
    paths = {item.path.as_posix() for item in candidates}

    assert "docs/reports/terminal/old.log" in paths
    assert "docs/reports/terminal/newest.log" not in paths
    assert "docs/reports/terminal/second.log" not in paths
    assert "docs/reports/terminal/latest-terminal.log" not in paths
    assert "docs/reports/terminal/source_manifest.json" not in paths
    assert old.exists() and newest.exists() and second.exists() and latest.exists() and manifest.exists()


def test_artifact_gc_report_retention_cli_is_dry_run_by_default(tmp_path: Path, monkeypatch) -> None:
    oldest = _touch(tmp_path / "docs/terminal/transfer_handoff_reports/oldest.log", mtime=OLD_MTIME)
    newer = _touch(tmp_path / "docs/terminal/transfer_handoff_reports/newer.log", mtime=OLD_MTIME + 1)
    newest = _touch(tmp_path / "docs/terminal/transfer_handoff_reports/newest.log", mtime=OLD_MTIME + 2)
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(app, ["artifact-gc", "--report-retention"])

    assert result.exit_code == 0
    assert "PENDING_EXPIRED_REPORT_RETENTION_FILES" in result.stdout
    assert "docs/terminal/transfer_handoff_reports/oldest.log" in result.stdout
    assert oldest.exists()
    assert newer.exists()
    assert newest.exists()
