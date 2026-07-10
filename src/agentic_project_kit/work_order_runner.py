from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from agentic_project_kit.work_order_validator import (
    WORK_ORDER_PATH,
    default_local_result_log_path,
    default_result_log_path,
    render_work_order_validation,
    validate_work_order_file,
)


@dataclass(frozen=True)
class WorkOrderRunResult:
    validation_ok: bool
    executed: bool
    returncode: int
    local_log: Path
    remote_log: Path
    message: str


def run_validated_work_order(
    *,
    work_order_path: Path = WORK_ORDER_PATH,
    local_log_path: Path | None = None,
    remote_log_path: Path | None = None,
) -> WorkOrderRunResult:
    root = Path.cwd()
    local_log_path = local_log_path or default_local_result_log_path(root)
    remote_log_path = remote_log_path or default_result_log_path(root)
    validation = validate_work_order_file(work_order_path)
    local_log_path.parent.mkdir(parents=True, exist_ok=True)

    if not validation.ok:
        output = render_work_order_validation(validation)
        body = chr(10).join(
            [
                "WORK_ORDER_RUN",
                "repo_root=" + str(Path.cwd().resolve()),
                "path=" + str(work_order_path),
                "validation_ok=false",
                "executed=false",
                "returncode=1",
                "local_log=" + str(local_log_path),
                "remote_log=" + str(remote_log_path),
                "validation_report_begin",
                output,
                "validation_report_end",
                "### RESULT: FAIL ###",
            ]
        )
        local_log_path.write_text(body + chr(10), encoding="utf-8")
        return WorkOrderRunResult(
            validation_ok=False,
            executed=False,
            returncode=1,
            local_log=local_log_path,
            remote_log=remote_log_path,
            message="work order validation failed; execution blocked; remote log not written",
        )

    completed = subprocess.run(
        [sys.executable, str(work_order_path)],
        cwd=Path.cwd(),
        text=True,
        capture_output=True,
        check=False,
    )
    body = chr(10).join(
        [
            "WORK_ORDER_RUN",
            "repo_root=" + str(Path.cwd().resolve()),
            "path=" + str(work_order_path),
            "validation_ok=true",
            "executed=true",
            "returncode=" + str(completed.returncode),
            "local_log=" + str(local_log_path),
            "remote_log=" + str(remote_log_path),
            "stdout_begin",
            completed.stdout.rstrip(),
            "stdout_end",
            "stderr_begin",
            completed.stderr.rstrip(),
            "stderr_end",
            "### RESULT: PASS ###" if completed.returncode == 0 else "### RESULT: FAIL ###",
        ]
    )
    local_log_path.write_text(body + chr(10), encoding="utf-8")
    return WorkOrderRunResult(
        validation_ok=True,
        executed=True,
        returncode=completed.returncode,
        local_log=local_log_path,
        remote_log=remote_log_path,
        message=(
            "work order executed; remote log pending explicit upload"
            if completed.returncode == 0
            else "work order executed with failure; remote log pending explicit upload"
        ),
    )


def render_work_order_run_result(result: WorkOrderRunResult) -> str:
    return chr(10).join(
        [
            "WORK_ORDER_RUN_RESULT",
            "validation_ok=" + str(result.validation_ok).lower(),
            "executed=" + str(result.executed).lower(),
            "returncode=" + str(result.returncode),
            "local_log=" + str(result.local_log),
            "remote_log=" + str(result.remote_log),
            "message=" + result.message,
            "### RESULT: PASS ###" if result.returncode == 0 else "### RESULT: FAIL ###",
        ]
    )
