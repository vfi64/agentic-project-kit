from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from agentic_project_kit.transfer_state import build_transfer_state
from agentic_project_kit.workspace import LEGACY_DEFAULTS, load_workspace


LATEST_COMMAND_RUN = Path(LEGACY_DEFAULTS.command_runs_root) / "LATEST_COMMAND_RUN.txt"
TRANSFER_ROOT = Path(".agentic/transfer")


@dataclass(frozen=True)
class TransferCloseout:
    schema_version: int
    removed_transfer_dir: bool
    latest_command_run_path: str | None
    latest_report_exists: bool
    allowed_dirty_paths: list[str]
    blocked_dirty_paths: list[str]
    state: dict[str, Any]
    result_status: str
    returncode: int
    next_action: str

    def as_json_data(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "removed_transfer_dir": self.removed_transfer_dir,
            "latest_command_run_path": self.latest_command_run_path,
            "latest_report_exists": self.latest_report_exists,
            "allowed_dirty_paths": self.allowed_dirty_paths,
            "blocked_dirty_paths": self.blocked_dirty_paths,
            "state": self.state,
            "result_status": self.result_status,
            "returncode": self.returncode,
            "next_action": self.next_action,
        }


def _git_status_short(root: Path) -> list[str]:
    process = subprocess.run(
        ["git", "status", "--short", "--untracked-files=all"],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if process.returncode != 0:
        raise RuntimeError(f"git status failed: {process.stderr.strip()}")
    return [line.rstrip() for line in process.stdout.splitlines() if line.strip()]


def _status_path(line: str) -> str:
    # Handles normal short status lines. Rename lines are intentionally treated by their final token.
    return line[3:].strip().split(" -> ")[-1]


def _is_allowed_dirty(path: str, latest_report_path: str | None, latest_command_run: str) -> bool:
    if path == latest_command_run:
        return True
    if latest_report_path and path == latest_report_path:
        return True
    return False


def _read_latest_report_path(root: Path) -> tuple[str | None, bool]:
    latest = load_workspace(root).latest_command_run_pointer()
    if not latest.exists():
        return None, False
    value = latest.read_text(encoding="utf-8").strip()
    if not value:
        return None, False
    report_path = value.splitlines()[-1].strip()
    return report_path, (root / report_path).exists()


def closeout_transfer(project_root: Path = Path("."), remove_transfer_dir: bool = True) -> TransferCloseout:
    root = project_root.resolve()
    removed = False

    if remove_transfer_dir and (root / TRANSFER_ROOT).exists():
        shutil.rmtree(root / TRANSFER_ROOT)
        removed = True

    latest_report_path, latest_report_exists = _read_latest_report_path(root)
    workspace = load_workspace(root)
    latest_command_run = workspace.path_text(workspace.latest_command_run_pointer())

    status_lines = _git_status_short(root)
    allowed: list[str] = []
    blocked: list[str] = []
    for line in status_lines:
        path = _status_path(line)
        if _is_allowed_dirty(path, latest_report_path, latest_command_run):
            allowed.append(path)
        else:
            blocked.append(path)

    state = build_transfer_state(root).as_json_data()

    if blocked:
        result_status = "BLOCKED"
        returncode = 1
        next_action = "Review blocked dirty paths before committing or running another transfer."
    else:
        result_status = "PASS"
        returncode = 0
        next_action = "Review allowed dirty evidence paths, then run project gates before commit."

    return TransferCloseout(
        schema_version=1,
        removed_transfer_dir=removed,
        latest_command_run_path=latest_report_path,
        latest_report_exists=latest_report_exists,
        allowed_dirty_paths=allowed,
        blocked_dirty_paths=blocked,
        state=state,
        result_status=result_status,
        returncode=returncode,
        next_action=next_action,
    )


def closeout_transfer_json(project_root: Path = Path("."), remove_transfer_dir: bool = True) -> str:
    return json.dumps(
        closeout_transfer(project_root, remove_transfer_dir=remove_transfer_dir).as_json_data(),
        indent=2,
        sort_keys=True,
    )
