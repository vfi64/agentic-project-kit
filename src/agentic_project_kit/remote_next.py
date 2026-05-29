from __future__ import annotations

import dataclasses
import subprocess
from pathlib import Path

from agentic_project_kit.typed_work_order_queue import (
    TypedNextResult,
    run_typed_next,
    typed_next_result_as_json_data,
)

STATUS_SYNC_FAIL = "sync_fail"


@dataclasses.dataclass(frozen=True)
class RemoteNextResult:
    sync_status: str
    returncode: int
    message: str
    typed_next: TypedNextResult | None = None


def _run_git(project_root: Path, argv: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        argv,
        cwd=project_root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def _sync_main(project_root: Path) -> tuple[bool, str]:
    fetch = _run_git(project_root, ["git", "fetch", "origin", "main"])
    if fetch.returncode != 0:
        return False, (fetch.stderr or fetch.stdout or "git fetch origin main failed").strip()
    branch = _run_git(project_root, ["git", "branch", "--show-current"])
    if branch.returncode != 0:
        return False, (branch.stderr or branch.stdout or "git branch --show-current failed").strip()
    if branch.stdout.strip() != "main":
        switch = _run_git(project_root, ["git", "switch", "main"])
        if switch.returncode != 0:
            return False, (switch.stderr or switch.stdout or "git switch main failed").strip()
    pull = _run_git(project_root, ["git", "pull", "--ff-only", "origin", "main"])
    if pull.returncode != 0:
        return False, (pull.stderr or pull.stdout or "git pull --ff-only origin main failed").strip()
    return True, "main synced"


def run_remote_next(project_root: Path = Path(".")) -> RemoteNextResult:
    root = project_root.resolve()
    ok, message = _sync_main(root)
    if not ok:
        return RemoteNextResult(STATUS_SYNC_FAIL, 2, message)
    typed_result = run_typed_next(root)
    return RemoteNextResult("synced", typed_result.returncode, typed_result.message, typed_result)


def remote_next_result_as_json_data(result: RemoteNextResult) -> dict[str, object]:
    return {
        "schema_version": 1,
        "sync_status": result.sync_status,
        "returncode": result.returncode,
        "message": result.message,
        "typed_next": typed_next_result_as_json_data(result.typed_next) if result.typed_next else None,
    }


def render_remote_next_result(result: RemoteNextResult) -> str:
    lines = [
        "REMOTE_NEXT_RESULT",
        f"sync_status={result.sync_status}",
        f"returncode={result.returncode}",
        f"message={result.message}",
    ]
    if result.typed_next is not None:
        lines.extend(
            [
                f"typed_queue_status={result.typed_next.queue_status}",
                f"typed_result_status={result.typed_next.result_status}",
            ]
        )
        if result.typed_next.terminal_log:
            lines.append(f"terminal_log={result.typed_next.terminal_log}")
        for path in result.typed_next.expected_closeout_paths:
            lines.append(f"expected_closeout_path={path}")
    return "\n".join(lines)
