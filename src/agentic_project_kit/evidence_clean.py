from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil
import subprocess


TRACKED_WORKFLOW_EVIDENCE: tuple[str, ...] = (
    ".agentic/workflow_state",
    "docs/reports/CURRENT_WORKFLOW_OUTPUT.md",
)


@dataclass(frozen=True)
class CleanCheckResult:
    ok: bool
    expected_log: str
    unexpected_lines: tuple[str, ...]
    raw_lines: tuple[str, ...]


@dataclass(frozen=True)
class EvidenceCleanResult:
    ok: bool
    before_status: tuple[str, ...]
    restore_lines: tuple[str, ...]
    removed_tmp_evidence: bool
    untracked_doc_reports: tuple[str, ...]
    after_status: tuple[str, ...]
    errors: tuple[str, ...]


def normalize_expected_log(repo_root: Path, expected_log: str | Path) -> str:
    expected = Path(expected_log)
    if expected.is_absolute():
        expected = expected.resolve().relative_to(repo_root.resolve())
    return expected.as_posix()


def unexpected_status_lines(status_lines: list[str] | tuple[str, ...], expected_log: str) -> tuple[str, ...]:
    allowed = "?? " + expected_log
    unexpected: list[str] = []
    for line in status_lines:
        stripped = line.rstrip()
        if stripped == "":
            continue
        if stripped == allowed:
            continue
        unexpected.append(stripped)
    return tuple(unexpected)


def _run_git(repo_root: Path, args: list[str]) -> tuple[int, str]:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    return completed.returncode, completed.stdout.strip()


def read_git_status(repo_root: Path, *paths: str) -> tuple[str, ...]:
    completed = subprocess.run(
        ["git", "status", "--short", *paths],
        cwd=repo_root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if completed.returncode != 0:
        return (completed.stdout.strip() or "git status failed",)
    return tuple(line for line in completed.stdout.splitlines() if line.strip())


def check_clean_except_expected_log(repo_root: Path, expected_log: str | Path) -> CleanCheckResult:
    normalized = normalize_expected_log(repo_root, expected_log)
    raw = read_git_status(repo_root)
    unexpected = unexpected_status_lines(raw, normalized)
    return CleanCheckResult(
        ok=len(unexpected) == 0,
        expected_log=normalized,
        unexpected_lines=unexpected,
        raw_lines=raw,
    )


def _path_is_tracked(repo_root: Path, path: str) -> bool:
    returncode, _ = _run_git(repo_root, ["ls-files", "--error-unmatch", path])
    return returncode == 0


def _path_is_dirty(repo_root: Path, path: str) -> bool:
    worktree_rc, _ = _run_git(repo_root, ["diff", "--quiet", "--", path])
    index_rc, _ = _run_git(repo_root, ["diff", "--cached", "--quiet", "--", path])
    return worktree_rc != 0 or index_rc != 0


def _restore_known_tracked_workflow_evidence(repo_root: Path) -> tuple[tuple[str, ...], tuple[str, ...]]:
    lines: list[str] = []
    errors: list[str] = []
    for path in TRACKED_WORKFLOW_EVIDENCE:
        if not _path_is_tracked(repo_root, path):
            lines.append(f"skip_untracked_path={path}")
            continue
        if not _path_is_dirty(repo_root, path):
            lines.append(f"clean_tracked={path}")
            continue
        lines.append(f"restore_tracked={path}")
        returncode, output = _run_git(repo_root, ["restore", "--staged", "--worktree", path])
        if returncode != 0:
            errors.append(output or f"git restore failed for {path}")
    return tuple(lines), tuple(errors)


def _remove_ignored_tmp_evidence(repo_root: Path) -> bool:
    target = repo_root / "tmp" / "agent-evidence"
    if not target.exists():
        return False
    shutil.rmtree(target)
    return True


def _untracked_doc_reports(repo_root: Path) -> tuple[str, ...]:
    return tuple(line for line in read_git_status(repo_root, "docs/reports") if line.startswith("?? "))


def clean_local_evidence(repo_root: Path) -> EvidenceCleanResult:
    before = read_git_status(repo_root)
    restore_lines, restore_errors = _restore_known_tracked_workflow_evidence(repo_root)
    errors = list(restore_errors)
    try:
        removed_tmp = _remove_ignored_tmp_evidence(repo_root)
    except OSError as exc:
        removed_tmp = False
        errors.append(str(exc))
    untracked_reports = _untracked_doc_reports(repo_root)
    after = read_git_status(repo_root)
    ok = not errors and not untracked_reports
    return EvidenceCleanResult(
        ok=ok,
        before_status=before,
        restore_lines=restore_lines,
        removed_tmp_evidence=removed_tmp,
        untracked_doc_reports=untracked_reports,
        after_status=after,
        errors=tuple(errors),
    )
