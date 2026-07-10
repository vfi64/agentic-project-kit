from __future__ import annotations

import os
from pathlib import Path

from agentic_project_kit.local_garbage_collector import run_local_garbage_collector


def _write_manifest(root: Path) -> None:
    manifest = root / ".agentic" / "config.yaml"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(
        "kit_schema_version: 1\n"
        "project:\n"
        "  name: fixture\n"
        "  type: generic\n"
        "profile: generic\n",
        encoding="utf-8",
    )


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


def test_local_gc_uses_manifest_tmp_namespace(tmp_path: Path) -> None:
    _write_manifest(tmp_path)
    target = tmp_path / ".agentic/tmp/old.log"
    target.parent.mkdir(parents=True)
    target.write_text("old", encoding="utf-8")
    os.utime(target, (100, 100))
    evidence = tmp_path / ".agentic/tmp/agent-evidence/old.log"
    evidence.parent.mkdir(parents=True)
    evidence.write_text("keep", encoding="utf-8")
    os.utime(evidence, (100, 100))

    result = run_local_garbage_collector(
        tmp_path,
        now=100 + 25 * 60 * 60,
        retention_seconds=24 * 60 * 60,
        tracked_predicate=_never_tracked,
    )

    assert result["result_status"] == "PASS"
    assert result["allowed_roots"] == [".agentic/tmp"]
    assert result["skipped_roots"] == [".agentic/tmp/agent-evidence"]
    assert result["deleted"] == [".agentic/tmp/old.log"]
    assert not target.exists()
    assert evidence.exists()
    assert (tmp_path / ".agentic/tmp/local-gc-last.json").exists()


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


def test_local_gc_deletes_old_untracked_tmp_files_regardless_of_suffix(tmp_path: Path) -> None:
    suffixes = [".py", ".md", ".diff", ".json", ".sh", ".txt", ".bin", ""]
    for suffix in suffixes:
        name = f"old{suffix}" if suffix else "old-no-suffix"
        target = tmp_path / "tmp" / name
        target.parent.mkdir(exist_ok=True)
        target.write_text("old", encoding="utf-8")
        os.utime(target, (100, 100))

    result = run_local_garbage_collector(
        tmp_path,
        now=100 + 25 * 60 * 60,
        retention_seconds=24 * 60 * 60,
        tracked_predicate=_never_tracked,
    )

    for suffix in suffixes:
        rel = f"tmp/old{suffix}" if suffix else "tmp/old-no-suffix"
        assert rel in result["deleted"]
        assert not (tmp_path / rel).exists()
    assert result["allowed_file_policy"] == "all_untracked_file_types_below_repo_tmp"


def test_local_gc_preserves_reserved_tmp_state_files(tmp_path: Path) -> None:
    reserved = [
        "tmp/local-gc-last.json",
        "tmp/local-gc-last-run-id.txt",
        "tmp/local-command-stack-state.json",
    ]
    for name in reserved:
        target = tmp_path / name
        target.parent.mkdir(exist_ok=True)
        target.write_text("state", encoding="utf-8")
        os.utime(target, (100, 100))

    result = run_local_garbage_collector(
        tmp_path,
        now=100 + 365 * 24 * 60 * 60,
        retention_seconds=24 * 60 * 60,
        tracked_predicate=_never_tracked,
    )

    for name in reserved:
        assert name not in result["deleted"]
        assert (tmp_path / name).exists()


def test_local_gc_deletes_old_empty_tmp_directories(tmp_path: Path) -> None:
    directory = tmp_path / "tmp" / "old-empty-dir"
    directory.mkdir(parents=True)
    os.utime(directory, (100, 100))

    result = run_local_garbage_collector(
        tmp_path,
        now=100 + 25 * 60 * 60,
        retention_seconds=24 * 60 * 60,
        tracked_predicate=_never_tracked,
    )

    assert "tmp/old-empty-dir" in result["deleted_directories"]
    assert not directory.exists()


def test_local_gc_deletes_old_tmp_directories_after_old_children_are_removed(tmp_path: Path) -> None:
    directory = tmp_path / "tmp" / "old-nonempty-dir"
    directory.mkdir(parents=True)
    child = directory / "old.bin"
    child.write_text("old", encoding="utf-8")
    os.utime(directory, (100, 100))
    os.utime(child, (100, 100))

    result = run_local_garbage_collector(
        tmp_path,
        now=100 + 25 * 60 * 60,
        retention_seconds=24 * 60 * 60,
        tracked_predicate=_never_tracked,
    )

    assert "tmp/old-nonempty-dir/old.bin" in result["deleted"]
    assert "tmp/old-nonempty-dir" in result["deleted_directories"]
    assert not directory.exists()


def test_local_gc_preserves_tmp_directories_with_fresh_children(tmp_path: Path) -> None:
    directory = tmp_path / "tmp" / "mixed-dir"
    directory.mkdir(parents=True)
    child = directory / "fresh.bin"
    child.write_text("fresh", encoding="utf-8")
    os.utime(directory, (100, 100))
    os.utime(child, (100 + 25 * 60 * 60 - 60, 100 + 25 * 60 * 60 - 60))

    result = run_local_garbage_collector(
        tmp_path,
        now=100 + 25 * 60 * 60,
        retention_seconds=24 * 60 * 60,
        tracked_predicate=_never_tracked,
    )

    assert "tmp/mixed-dir" not in result["deleted_directories"]
    assert directory.exists()
    assert child.exists()


def test_local_gc_skips_symlinks(tmp_path: Path) -> None:
    target = tmp_path / "target.txt"
    target.write_text("keep", encoding="utf-8")
    link = tmp_path / "tmp" / "old-link.txt"
    link.parent.mkdir()
    link.symlink_to(target)
    os.utime(link.parent, (100, 100))

    result = run_local_garbage_collector(
        tmp_path,
        now=100 + 25 * 60 * 60,
        retention_seconds=24 * 60 * 60,
        tracked_predicate=_never_tracked,
    )

    assert result["deleted"] == []
    assert link.is_symlink()
    assert target.exists()
