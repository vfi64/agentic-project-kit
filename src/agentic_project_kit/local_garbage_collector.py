from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path
from typing import Callable, Iterable

from agentic_project_kit.workspace import LEGACY_DEFAULTS, Workspace, load_workspace

LOCAL_GC_REPORT_FILE = "local-gc-last.json"
LOCAL_GC_RUN_MARKER_FILE = "local-gc-last-run-id.txt"
LOCAL_COMMAND_STACK_STATE_FILE = "local-command-stack-state.json"
AGENT_EVIDENCE_DIR_NAME = "agent-evidence"
LOCAL_GC_REPORT = Path(LEGACY_DEFAULTS.tmp_root) / LOCAL_GC_REPORT_FILE
LOCAL_GC_RUN_MARKER = Path(LEGACY_DEFAULTS.tmp_root) / LOCAL_GC_RUN_MARKER_FILE
DEFAULT_RETENTION_SECONDS = 24 * 60 * 60

# Intentionally narrow by root. This collector may clean all old untracked file
# types, but only below the repository-local workspace tmp root.
ALLOWED_FILE_POLICY = "all_untracked_file_types_below_repo_tmp"


def _relative_to_root(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _is_under(path: Path, candidate_root: Path) -> bool:
    try:
        path.resolve().relative_to(candidate_root.resolve())
    except ValueError:
        return False
    return True


def _run_git(root: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=root.resolve(),
        text=True,
        capture_output=True,
        check=False,
    )


def _is_git_work_tree(root: Path) -> bool:
    result = _run_git(root, ["rev-parse", "--is-inside-work-tree"])
    return result.returncode == 0 and result.stdout.strip() == "true"


def _is_tracked(root: Path, path: Path) -> bool:
    if not _is_git_work_tree(root):
        return False
    rel = _relative_to_root(path, root)
    result = _run_git(root, ["ls-files", "--error-unmatch", "--", rel])
    return result.returncode == 0


def _allowed_roots(workspace: Workspace) -> tuple[Path, ...]:
    return (workspace.tmp(),)


def _skipped_roots(workspace: Workspace) -> tuple[Path, ...]:
    return (workspace.agent_evidence_dir(),)


def _reserved_tmp_files(workspace: Workspace) -> tuple[Path, ...]:
    return (
        workspace.local_gc_report_path(),
        workspace.local_gc_run_marker_path(),
        workspace.local_command_stack_state_path(),
    )


def _path_texts(workspace: Workspace, paths: Iterable[Path]) -> list[str]:
    return [workspace.path_text(path) for path in paths]


def _is_reserved_tmp_file(path: Path, workspace: Workspace) -> bool:
    for reserved in _reserved_tmp_files(workspace):
        if path.resolve() == reserved.resolve():
            return True
    return False


def _iter_file_candidates(workspace: Workspace) -> Iterable[Path]:
    for directory in _allowed_roots(workspace):
        if not directory.exists():
            continue
        for path in directory.rglob("*"):
            if not path.is_file():
                continue
            if path.is_symlink():
                continue
            if any(_is_under(path, skipped) for skipped in _skipped_roots(workspace)):
                continue
            if _is_reserved_tmp_file(path, workspace):
                continue
            yield path


def _iter_directory_candidates(workspace: Workspace) -> Iterable[Path]:
    for directory in _allowed_roots(workspace):
        if not directory.exists():
            continue
        candidates = [path for path in directory.rglob("*") if path.is_dir()]
        for path in sorted(candidates, key=lambda item: len(item.parts), reverse=True):
            if path.resolve() == directory.resolve():
                continue
            if any(_is_under(path, skipped) for skipped in _skipped_roots(workspace)):
                continue
            yield path


def run_local_garbage_collector(
    project_root: Path = Path("."),
    *,
    dry_run: bool = False,
    now: float | None = None,
    retention_seconds: int = DEFAULT_RETENTION_SECONDS,
    write_report: bool = True,
    run_id: str | None = None,
    skip_if_run_id_seen: bool = True,
    tracked_predicate: Callable[[Path, Path], bool] = _is_tracked,
) -> dict[str, object]:
    """Delete only deterministic, local, untracked runtime artefacts.

    This is intentionally conservative:
    - only allowlisted roots,
    - only allowlisted suffixes,
    - never tracked files,
    - never workflow evidence under tmp/agent-evidence,
    - age-gated by retention_seconds,
    - optionally once per local command stack via run_id.
    """

    root = project_root.resolve()
    workspace = load_workspace(root)
    normalized_run_id = (run_id or "").strip()
    marker_path = workspace.local_gc_run_marker_path()
    if normalized_run_id and skip_if_run_id_seen and marker_path.exists():
        seen_run_id = marker_path.read_text(encoding="utf-8").strip()
        if seen_run_id == normalized_run_id:
            result = {
                "schema_version": 1,
                "kind": "local_garbage_collector_result",
                "result_status": "PASS",
                "returncode": 0,
                "dry_run": dry_run,
                "run_id": normalized_run_id,
                "skipped": True,
                "skip_reason": "already_ran_for_command_stack",
                "allowed_roots": _path_texts(workspace, _allowed_roots(workspace)),
                "skipped_roots": _path_texts(workspace, _skipped_roots(workspace)),
                "allowed_file_policy": ALLOWED_FILE_POLICY,
                "retention_seconds": retention_seconds,
                "candidate_count": 0,
                "deleted": [],
                "deleted_directories": [],
                "kept": [],
                "errors": [],
                "next_action": "Local deterministic garbage collection already ran for this command stack.",
            }
            if write_report:
                report_path = workspace.local_gc_report_path()
                report_path.parent.mkdir(parents=True, exist_ok=True)
                report_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            return result

    effective_now = time.time() if now is None else now
    deleted: list[str] = []
    deleted_directories: list[str] = []
    kept: list[dict[str, object]] = []
    errors: list[dict[str, str]] = []
    directory_age_seconds: dict[Path, int] = {}

    for directory in _iter_directory_candidates(workspace):
        try:
            stat = directory.stat()
        except FileNotFoundError:
            continue
        directory_age_seconds[directory] = max(0, int(effective_now - stat.st_mtime))

    for path in sorted(_iter_file_candidates(workspace)):
        rel = _relative_to_root(path, root)
        try:
            stat = path.stat()
        except FileNotFoundError:
            continue

        age_seconds = max(0, int(effective_now - stat.st_mtime))
        if tracked_predicate(root, path):
            kept.append({"path": rel, "reason": "tracked_file", "age_seconds": age_seconds})
            continue
        if age_seconds < retention_seconds:
            kept.append({"path": rel, "reason": "retention_not_reached", "age_seconds": age_seconds})
            continue

        if dry_run:
            deleted.append(rel)
            continue

        try:
            path.unlink()
            deleted.append(rel)
        except OSError as exc:
            errors.append({"path": rel, "error": str(exc)})

    for directory in _iter_directory_candidates(workspace):
        rel = _relative_to_root(directory, root)
        age_seconds = directory_age_seconds.get(directory)
        if age_seconds is None:
            try:
                stat = directory.stat()
            except FileNotFoundError:
                continue
            age_seconds = max(0, int(effective_now - stat.st_mtime))
        if age_seconds < retention_seconds:
            kept.append({"path": rel, "reason": "directory_retention_not_reached", "age_seconds": age_seconds})
            continue
        try:
            next(directory.iterdir())
        except StopIteration:
            if dry_run:
                deleted_directories.append(rel)
                continue
            try:
                directory.rmdir()
                deleted_directories.append(rel)
            except OSError as exc:
                errors.append({"path": rel, "error": str(exc)})
        except OSError as exc:
            errors.append({"path": rel, "error": str(exc)})

    result_status = "PASS" if not errors else "BLOCKED"
    result = {
        "schema_version": 1,
        "kind": "local_garbage_collector_result",
        "result_status": result_status,
        "returncode": 0 if result_status == "PASS" else 2,
        "dry_run": dry_run,
        "run_id": normalized_run_id,
        "skipped": False,
        "allowed_roots": _path_texts(workspace, _allowed_roots(workspace)),
        "skipped_roots": _path_texts(workspace, _skipped_roots(workspace)),
        "allowed_file_policy": ALLOWED_FILE_POLICY,
        "retention_seconds": retention_seconds,
        "candidate_count": len(deleted) + len(deleted_directories),
        "deleted": deleted,
        "deleted_directories": deleted_directories,
        "kept": kept,
        "errors": errors,
        "next_action": (
            "Local deterministic garbage collection completed."
            if result_status == "PASS"
            else "Inspect local garbage collector errors before continuing."
        ),
    }

    if normalized_run_id and result_status == "PASS" and not dry_run:
        marker_path.parent.mkdir(parents=True, exist_ok=True)
        marker_path.write_text(normalized_run_id + "\n", encoding="utf-8")

    if write_report:
        report_path = workspace.local_gc_report_path()
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    return result
