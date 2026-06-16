from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path
from typing import Callable, Iterable

LOCAL_GC_REPORT = Path("tmp/local-gc-last.json")
DEFAULT_RETENTION_SECONDS = 24 * 60 * 60

# Intentionally narrow. Broader cleanup belongs to explicit GC rules, not ad-hoc deletion.
ALLOWED_ROOTS = (Path("tmp"),)
SKIPPED_ROOTS = (Path("tmp/agent-evidence"),)
ALLOWED_SUFFIXES = {".log", ".tmp", ".out", ".err"}


def _relative_to_root(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _is_under(path: Path, root: Path, candidate_root: Path) -> bool:
    try:
        path.resolve().relative_to((root / candidate_root).resolve())
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


def _iter_candidates(root: Path) -> Iterable[Path]:
    for allowed_root in ALLOWED_ROOTS:
        directory = root / allowed_root
        if not directory.exists():
            continue
        for path in directory.rglob("*"):
            if not path.is_file():
                continue
            if any(_is_under(path, root, skipped) for skipped in SKIPPED_ROOTS):
                continue
            if path.suffix.lower() not in ALLOWED_SUFFIXES:
                continue
            yield path


def run_local_garbage_collector(
    project_root: Path = Path("."),
    *,
    dry_run: bool = False,
    now: float | None = None,
    retention_seconds: int = DEFAULT_RETENTION_SECONDS,
    write_report: bool = True,
    tracked_predicate: Callable[[Path, Path], bool] = _is_tracked,
) -> dict[str, object]:
    """Delete only deterministic, local, untracked runtime artefacts.

    This is intentionally conservative:
    - only allowlisted roots,
    - only allowlisted suffixes,
    - never tracked files,
    - never workflow evidence under tmp/agent-evidence,
    - age-gated by retention_seconds.
    """

    root = project_root.resolve()
    effective_now = time.time() if now is None else now
    deleted: list[str] = []
    kept: list[dict[str, object]] = []
    errors: list[dict[str, str]] = []

    for path in sorted(_iter_candidates(root)):
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

    result_status = "PASS" if not errors else "BLOCKED"
    result = {
        "schema_version": 1,
        "kind": "local_garbage_collector_result",
        "result_status": result_status,
        "returncode": 0 if result_status == "PASS" else 2,
        "dry_run": dry_run,
        "allowed_roots": [path.as_posix() for path in ALLOWED_ROOTS],
        "skipped_roots": [path.as_posix() for path in SKIPPED_ROOTS],
        "allowed_suffixes": sorted(ALLOWED_SUFFIXES),
        "retention_seconds": retention_seconds,
        "deleted": deleted,
        "kept": kept,
        "errors": errors,
        "next_action": (
            "Local deterministic garbage collection completed."
            if result_status == "PASS"
            else "Inspect local garbage collector errors before continuing."
        ),
    }

    if write_report:
        report_path = root / LOCAL_GC_REPORT
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    return result
