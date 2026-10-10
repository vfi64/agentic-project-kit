"""Bounded subprocess adapter and immediate evidence for local Kit updates."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import subprocess
import time


class UpdateBlocked(RuntimeError):
    pass


@dataclass
class UpdateRunner:
    root: Path
    log_path: Path

    def __call__(self, argv: list[str], *, timeout: int = 120) -> subprocess.CompletedProcess[str]:
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        start = time.monotonic()
        self._append({"event": "START", "argv": argv})
        try:
            environment = os.environ.copy()
            if "-m" in argv and argv[argv.index("-m") + 1] == "pip":
                # --isolated alone still loads system and venv pip.conf. Those
                # files could add an unsigned extra index or installation scope.
                environment["PIP_CONFIG_FILE"] = os.devnull
            result = subprocess.run(
                argv,
                cwd=self.root,
                env=environment,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            self._append(
                {
                    "event": "ERROR",
                    "argv": argv,
                    "error": type(exc).__name__,
                    "duration": time.monotonic() - start,
                }
            )
            raise UpdateBlocked(f"subprocess_{type(exc).__name__}; inspect update log") from exc
        self._append(
            {
                "event": "END",
                "argv": argv,
                "rc": result.returncode,
                "duration": time.monotonic() - start,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
        )
        return result

    def _append(self, event: dict) -> None:
        with self.log_path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(event, ensure_ascii=False) + "\n")
            stream.flush()


def checked(run, argv: list[str], *, timeout: int = 120) -> str:
    result = run(argv, timeout=timeout)
    if result.returncode:
        raise UpdateBlocked(f"command_failed: {' '.join(argv[:4])}; inspect update log")
    return result.stdout


def json_command(run, argv: list[str]) -> dict:
    try:
        data = json.loads(checked(run, argv))
    except (ValueError, TypeError) as exc:
        raise UpdateBlocked("invalid_command_json") from exc
    if not isinstance(data, dict):
        raise UpdateBlocked("invalid_command_json")
    return data
