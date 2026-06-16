from __future__ import annotations

import os
from pathlib import Path

from agentic_project_kit.local_garbage_collector import run_local_garbage_collector


def _never_tracked(root: Path, path: Path) -> bool:
    return False


def _always_tracked(root: Path, path: Path) -> bool:
    return True


def test_local_gc_deletes_old_untracked_tmp_log(tmp_path: Path) -> None:
    target = tmp_path / "tmp" / "old.log"
    target.parent.mkdir()
    target.write_text("old", encoding="utf-8")
    os.utime(target, (100, 100))

    result = run_local_garbage_collector(
        tmp_path,
        now=100 + 25 * 60 * 60,
        retention_seconds=24 * 60 * 60,
        tracked_predicate=_never_tracked,
    )

    assert result["result_status"] == "PASS"
    assert result["deleted"] == ["tmp/old.log"]
    assert not target.exists()
    assert (tmp_path / "tmp" / "local-gc-last.json").exists()


def test_local_gc_keeps_new_tmp_log_until_retention(tmp_path: Path) -> None:
    target = tmp_path / "tmp" / "new.log"
    target.parent.mkdir()
    target.write_text("new", encoding="utf-8")
    os.utime(target, (100, 100))

    result = run_local_garbage_collector(
        tmp_path,
        now=100 + 60,
        retention_seconds=24 * 60 * 60,
        tracked_predicate=_never_tracked,
    )

    assert result["deleted"] == []
    assert target.exists()
    assert result["kept"][0]["reason"] == "retention_not_reached"


def test_local_gc_never_deletes_tracked_files(tmp_path: Path) -> None:
    target = tmp_path / "tmp" / "tracked.log"
    target.parent.mkdir()
    target.write_text("tracked", encoding="utf-8")
    os.utime(target, (100, 100))

    result = run_local_garbage_collector(
        tmp_path,
        now=100 + 365 * 24 * 60 * 60,
        retention_seconds=24 * 60 * 60,
        tracked_predicate=_always_tracked,
    )

    assert result["deleted"] == []
    assert target.exists()
    assert result["kept"][0]["reason"] == "tracked_file"


def test_local_gc_skips_workflow_evidence(tmp_path: Path) -> None:
    target = tmp_path / "tmp" / "agent-evidence" / "old.log"
    target.parent.mkdir(parents=True)
    target.write_text("evidence", encoding="utf-8")
    os.utime(target, (100, 100))

    result = run_local_garbage_collector(
        tmp_path,
        now=100 + 365 * 24 * 60 * 60,
        retention_seconds=24 * 60 * 60,
        tracked_predicate=_never_tracked,
    )

    assert result["deleted"] == []
    assert target.exists()


def test_local_gc_runs_at_most_once_per_command_stack_id(tmp_path: Path) -> None:
    first = tmp_path / "tmp" / "first.log"
    first.parent.mkdir()
    first.write_text("first", encoding="utf-8")
    os.utime(first, (100, 100))

    first_result = run_local_garbage_collector(
        tmp_path,
        now=100 + 25 * 60 * 60,
        retention_seconds=24 * 60 * 60,
        run_id="stack-1",
        tracked_predicate=_never_tracked,
    )

    assert first_result["skipped"] is False
    assert first_result["deleted"] == ["tmp/first.log"]
    assert not first.exists()

    second = tmp_path / "tmp" / "second.log"
    second.write_text("second", encoding="utf-8")
    os.utime(second, (100, 100))

    second_result = run_local_garbage_collector(
        tmp_path,
        now=100 + 25 * 60 * 60,
        retention_seconds=24 * 60 * 60,
        run_id="stack-1",
        tracked_predicate=_never_tracked,
    )

    assert second_result["skipped"] is True
    assert second_result["skip_reason"] == "already_ran_for_command_stack"
    assert second_result["deleted"] == []
    assert second.exists()


def test_local_gc_new_command_stack_id_runs_again(tmp_path: Path) -> None:
    first = tmp_path / "tmp" / "first.log"
    first.parent.mkdir()
    first.write_text("first", encoding="utf-8")
    os.utime(first, (100, 100))

    run_local_garbage_collector(
        tmp_path,
        now=100 + 25 * 60 * 60,
        retention_seconds=24 * 60 * 60,
        run_id="stack-1",
        tracked_predicate=_never_tracked,
    )

    second = tmp_path / "tmp" / "second.log"
    second.write_text("second", encoding="utf-8")
    os.utime(second, (100, 100))

    second_result = run_local_garbage_collector(
        tmp_path,
        now=100 + 25 * 60 * 60,
        retention_seconds=24 * 60 * 60,
        run_id="stack-2",
        tracked_predicate=_never_tracked,
    )

    assert second_result["skipped"] is False
    assert second_result["deleted"] == ["tmp/second.log"]
    assert not second.exists()
