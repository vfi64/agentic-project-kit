from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from agentic_project_kit.work_order_validator import RESULT_LOG_PATH


@dataclass(frozen=True)
class WorkOrderUploadResult:
    ok: bool
    committed: bool
    pushed: bool
    returncode: int
    log_path: Path
    message: str
    commit_sha: str | None = None


def _run_git(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=Path.cwd(),
        text=True,
        capture_output=True,
        check=False,
    )


def _git_stdout(args: list[str]) -> str:
    completed = _run_git(args)
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip())
    return completed.stdout.strip()


def _status_short() -> list[str]:
    output = _git_stdout(["status", "--short"])
    return [line for line in output.splitlines() if line.strip()]


def upload_next_turn_result_log(
    *,
    log_path: Path = RESULT_LOG_PATH,
    commit_message: str = "Upload next-turn result log",
) -> WorkOrderUploadResult:
    if not log_path.exists():
        return WorkOrderUploadResult(
            ok=False,
            committed=False,
            pushed=False,
            returncode=1,
            log_path=log_path,
            message="missing result log: " + str(log_path),
        )

    dirty = _status_short()
    allowed_dirty = {"?? " + str(log_path), " M " + str(log_path), "M  " + str(log_path), "A  " + str(log_path)}
    disallowed = [line for line in dirty if line not in allowed_dirty]
    if disallowed:
        return WorkOrderUploadResult(
            ok=False,
            committed=False,
            pushed=False,
            returncode=1,
            log_path=log_path,
            message="refusing upload because other worktree changes exist: " + "; ".join(disallowed),
        )

    add = _run_git(["add", str(log_path)])
    if add.returncode != 0:
        return WorkOrderUploadResult(False, False, False, add.returncode, log_path, add.stderr.strip() or add.stdout.strip())

    cached = _git_stdout(["diff", "--cached", "--name-only"])
    cached_paths = [line.strip() for line in cached.splitlines() if line.strip()]
    if cached_paths != [str(log_path)]:
        _run_git(["reset", "--", str(log_path)])
        return WorkOrderUploadResult(
            ok=False,
            committed=False,
            pushed=False,
            returncode=1,
            log_path=log_path,
            message="refusing upload because staged paths are not exactly the result log: " + repr(cached_paths),
        )

    commit = _run_git(["commit", "-m", commit_message])
    if commit.returncode != 0:
        _run_git(["reset", "--", str(log_path)])
        return WorkOrderUploadResult(False, False, False, commit.returncode, log_path, commit.stderr.strip() or commit.stdout.strip())

    commit_sha = _git_stdout(["rev-parse", "HEAD"])
    push = _run_git(["push"])
    if push.returncode != 0:
        return WorkOrderUploadResult(
            ok=False,
            committed=True,
            pushed=False,
            returncode=push.returncode,
            log_path=log_path,
            message=push.stderr.strip() or push.stdout.strip(),
            commit_sha=commit_sha,
        )

    return WorkOrderUploadResult(
        ok=True,
        committed=True,
        pushed=True,
        returncode=0,
        log_path=log_path,
        message="uploaded next-turn result log",
        commit_sha=commit_sha,
    )


def render_work_order_upload_result(result: WorkOrderUploadResult) -> str:
    lines = [
        "WORK_ORDER_UPLOAD_RESULT",
        "ok=" + str(result.ok).lower(),
        "committed=" + str(result.committed).lower(),
        "pushed=" + str(result.pushed).lower(),
        "returncode=" + str(result.returncode),
        "log_path=" + str(result.log_path),
        "message=" + result.message,
    ]
    if result.commit_sha:
        lines.append("commit_sha=" + result.commit_sha)
    lines.append("### RESULT: PASS ###" if result.ok else "### RESULT: FAIL ###")
    return chr(10).join(lines)
