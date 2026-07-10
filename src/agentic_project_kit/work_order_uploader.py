from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from agentic_project_kit.work_order_validator import default_local_result_log_path, default_result_log_path


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


def _allowed_dirty_lines_for_log_path(log_path: Path) -> set[str]:
    path = str(log_path)
    allowed = {
        "?? " + path,
        " M " + path,
        "M  " + path,
        "A  " + path,
    }

    parts = path.split("/")
    for index in range(1, len(parts)):
        allowed.add("?? " + "/".join(parts[:index]) + "/")

    return allowed


def _local_log_belongs_to_current_repo(local_log_path: Path) -> bool:
    if not local_log_path.exists():
        return False
    expected = "repo_root=" + str(Path.cwd().resolve())
    try:
        return expected in local_log_path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        return False


def _current_branch() -> str:
    return _git_stdout(["branch", "--show-current"])


def upload_next_turn_result_log(
    *,
    log_path: Path | None = None,
    local_log_path: Path | None = None,
    commit_message: str = "Upload next-turn result log",
    required_branch: str = "",
    allow_main: bool = False,
) -> WorkOrderUploadResult:
    log_path = log_path or default_result_log_path(Path.cwd())
    local_log_path = local_log_path or default_local_result_log_path(Path.cwd())
    local_log_ready = _local_log_belongs_to_current_repo(local_log_path)
    if not log_path.exists() and not local_log_ready:
        return WorkOrderUploadResult(
            ok=False,
            committed=False,
            pushed=False,
            returncode=1,
            log_path=log_path,
            message="missing result log: " + str(local_log_path) + " or " + str(log_path),
        )

    dirty = _status_short()
    allowed_dirty = _allowed_dirty_lines_for_log_path(log_path)
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

    branch = _current_branch()
    if required_branch and branch != required_branch:
        return WorkOrderUploadResult(
            ok=False,
            committed=False,
            pushed=False,
            returncode=1,
            log_path=log_path,
            message=f"current branch {branch!r} does not match required branch {required_branch!r}",
        )
    if branch == "main" and not allow_main:
        return WorkOrderUploadResult(
            ok=False,
            committed=False,
            pushed=False,
            returncode=1,
            log_path=log_path,
            message="work-order uploader refuses to commit on main without allow_main=True",
        )
    if not branch:
        return WorkOrderUploadResult(
            ok=False,
            committed=False,
            pushed=False,
            returncode=1,
            log_path=log_path,
            message="work-order uploader refuses to commit without a current branch",
        )

    if local_log_ready:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text(local_log_path.read_text(encoding="utf-8"), encoding="utf-8")

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
