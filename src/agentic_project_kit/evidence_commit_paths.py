from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess


@dataclass(frozen=True)
class EvidenceCommitPathsResult:
    success: bool
    branch: str
    head_before: str
    commit_sha: str
    paths: tuple[str, ...]
    log_path: str | None
    findings: tuple[str, ...]


def _run_git(root: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=root, text=True, capture_output=True, check=False)


def _git_stdout(root: Path, args: list[str]) -> str:
    result = _run_git(root, args)
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def _status_lines(root: Path) -> tuple[str, ...]:
    result = _run_git(root, ["status", "--short", "--untracked-files=all"])
    if result.returncode != 0:
        return ()
    return tuple(line for line in result.stdout.splitlines() if line.strip())


def _path_is_dirty(status_line: str, rel_path: str) -> bool:
    return status_line.strip().endswith(rel_path)


def commit_paths(
    *,
    root: Path | str = Path("."),
    paths: tuple[str, ...],
    message: str,
    log_path: str | None = None,
    push: bool = False,
) -> EvidenceCommitPathsResult:
    root_path = Path(root).resolve()
    if not paths:
        raise ValueError("at least one path is required")
    if log_path:
        if Path(log_path).is_absolute():
            raise ValueError("log_path must be repository-relative")
        if not log_path.startswith("docs/reports/terminal/"):
            raise ValueError("log_path must start with docs/reports/terminal/")
        if log_path not in paths:
            paths = (*paths, log_path)

    normalized_paths = tuple(dict.fromkeys(paths))
    for rel in normalized_paths:
        if Path(rel).is_absolute():
            raise ValueError(f"path must be repository-relative: {rel}")
        if rel.startswith(".git/") or rel == ".git":
            raise ValueError(".git paths are not allowed")
        if rel.startswith(".venv/") or rel == ".venv":
            raise ValueError(".venv paths are not allowed")

    branch = _git_stdout(root_path, ["branch", "--show-current"]) or "UNKNOWN"
    head_before = _git_stdout(root_path, ["rev-parse", "HEAD"]) or "UNKNOWN"
    status_before = _status_lines(root_path)

    unexpected = [
        line for line in status_before
        if not any(_path_is_dirty(line, rel) for rel in normalized_paths)
    ]
    if unexpected:
        return EvidenceCommitPathsResult(
            False,
            branch,
            head_before,
            "",
            normalized_paths,
            log_path,
            tuple(["unexpected dirty paths before commit", *unexpected]),
        )

    deletion_lines = {line[3:] for line in status_before if line.startswith(" D ") or line.startswith("D  ")}
    missing = [
        rel for rel in normalized_paths
        if not (root_path / rel).exists() and rel not in deletion_lines
    ]
    if missing:
        return EvidenceCommitPathsResult(
            False,
            branch,
            head_before,
            "",
            normalized_paths,
            log_path,
            tuple(f"missing path: {rel}" for rel in missing),
        )

    add_result = _run_git(root_path, ["add", "-A", "--", *normalized_paths])
    if add_result.returncode != 0:
        return EvidenceCommitPathsResult(
            False,
            branch,
            head_before,
            "",
            normalized_paths,
            log_path,
            (add_result.stderr.strip() or add_result.stdout.strip() or "git add failed",),
        )

    diff_result = _run_git(root_path, ["diff", "--cached", "--quiet"])
    if diff_result.returncode == 0:
        return EvidenceCommitPathsResult(
            True,
            branch,
            head_before,
            head_before,
            normalized_paths,
            log_path,
            ("no staged diff; no commit created",),
        )

    commit_result = _run_git(root_path, ["commit", "-m", message])
    if commit_result.returncode != 0:
        return EvidenceCommitPathsResult(
            False,
            branch,
            head_before,
            "",
            normalized_paths,
            log_path,
            (commit_result.stderr.strip() or commit_result.stdout.strip() or "git commit failed",),
        )

    commit_sha = _git_stdout(root_path, ["rev-parse", "HEAD"]) or "UNKNOWN"
    if push:
        push_result = _run_git(root_path, ["push", "origin", branch])
        if push_result.returncode != 0:
            return EvidenceCommitPathsResult(
                False,
                branch,
                head_before,
                commit_sha,
                normalized_paths,
                log_path,
                (push_result.stderr.strip() or push_result.stdout.strip() or "git push failed",),
            )

    status_after = _status_lines(root_path)
    if status_after:
        return EvidenceCommitPathsResult(
            False,
            branch,
            head_before,
            commit_sha,
            normalized_paths,
            log_path,
            tuple(["dirty worktree after commit", *status_after]),
        )

    return EvidenceCommitPathsResult(True, branch, head_before, commit_sha, normalized_paths, log_path, ())


def render_commit_paths_result(result: EvidenceCommitPathsResult) -> str:
    lines = [
        "EVIDENCE_COMMIT_PATHS",
        f"success={'yes' if result.success else 'no'}",
        f"branch={result.branch}",
        f"head_before={result.head_before}",
        f"commit_sha={result.commit_sha or 'NONE'}",
    ]
    if result.log_path:
        lines.append(f"log_path={result.log_path}")
    for path in result.paths:
        lines.append(f"path={path}")
    for finding in result.findings:
        lines.append(f"finding={finding}")
    lines.append(f"### RESULT: {'PASS' if result.success else 'FAIL'} ###")
    return "\n".join(lines)
