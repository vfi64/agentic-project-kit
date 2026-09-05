from __future__ import annotations

import subprocess
from collections.abc import Mapping


def _timeout_output_text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode(errors="replace")
    return value


def run_observed_subprocess(
    name: str,
    argv: list[str],
    *,
    timeout_seconds: int,
    env: Mapping[str, str] | None = None,
) -> dict[str, object]:
    try:
        kwargs: dict[str, object] = {}
        if env is not None:
            kwargs["env"] = dict(env)
        completed = subprocess.run(
            argv,
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            **kwargs,
        )
        return {
            "name": name,
            "argv": argv,
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "ok": completed.returncode == 0,
            "timeout_seconds": timeout_seconds,
            "timed_out": False,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "name": name,
            "argv": argv,
            "returncode": 124,
            "stdout": _timeout_output_text(exc.stdout),
            "stderr": _timeout_output_text(exc.stderr) or f"Timed out after {timeout_seconds} seconds.",
            "ok": False,
            "timeout_seconds": timeout_seconds,
            "timed_out": True,
        }
