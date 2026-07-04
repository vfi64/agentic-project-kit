from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timezone
import json
import logging
import os
from pathlib import Path
from typing import Any

from agentic_project_kit.workspace import KitConfig


LOGGER = logging.getLogger(__name__)


class WorkspaceLockBusy(RuntimeError):
    pass


def _workspace_lock_path(root: Path) -> Path:
    config = KitConfig()
    return Path(root) / config.agentic_tmp_root / config.workspace_lock_file


def _pid_is_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _read_lock_payload(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if isinstance(payload, dict):
        return payload
    return {}


def _holder_field(payload: dict[str, Any], key: str, fallback: str) -> str:
    value = payload.get(key)
    return str(value) if value not in (None, "") else fallback


@contextmanager
def acquire_workspace_lock(root: Path, command: str) -> Iterator[Path]:
    path = _workspace_lock_path(Path(root))
    payload = {
        "pid": os.getpid(),
        "command": command,
        "acquired_at": datetime.now(timezone.utc).isoformat(),
    }
    acquired = False
    while True:
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            holder = _read_lock_payload(path)
            holder_pid = int(holder.get("pid") or -1)
            holder_command = _holder_field(holder, "command", "unknown")
            holder_acquired_at = _holder_field(holder, "acquired_at", "unknown")
            if holder_pid > 0 and _pid_is_alive(holder_pid):
                raise WorkspaceLockBusy(
                    f"workspace is busy: {holder_command} pid {holder_pid} since {holder_acquired_at}"
                )
            LOGGER.warning(
                "stale workspace lock takeover: %s pid %s since %s",
                holder_command,
                holder_pid,
                holder_acquired_at,
            )
            try:
                path.unlink()
            except FileNotFoundError as exc:
                LOGGER.debug("stale workspace lock already removed before takeover: %s", exc)
            continue
        else:
            with os.fdopen(fd, "w", encoding="utf-8") as lock_file:
                lock_file.write(json.dumps(payload, sort_keys=True) + "\n")
            acquired = True
            break

    try:
        yield path
    finally:
        if acquired:
            try:
                path.unlink()
            except FileNotFoundError as exc:
                LOGGER.debug("workspace lock already removed before release: %s", exc)
