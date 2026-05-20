from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess


@dataclass(frozen=True)
class CleanCheckResult:
    ok: bool
    expected_log: str
    unexpected_lines: tuple[str, ...]
    raw_lines: tuple[str, ...]


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


def read_git_status(repo_root: Path) -> tuple[str, ...]:
    completed = subprocess.run(
        ["git", "status", "--short"],
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
