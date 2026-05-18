"""Terminal log wrapper utilities for local workflow runs.

The module supports a deterministic handoff protocol:
- run a command while teeing stdout/stderr to a terminal log,
- keep a pointer to the latest terminal log,
- inspect upload readiness,
- upload only terminal-log artifacts on failure handoff.
"""

from __future__ import annotations

import datetime as _dt
import os
import subprocess
import sys
from pathlib import Path

TERMINAL_DIR = Path("docs/reports/terminal")
LATEST_POINTER = TERMINAL_DIR / "LATEST_TERMINAL_LOG.txt"


def _safe_name(name: str) -> str:
    safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in name.strip())
    return safe or "run"


def make_log_path(name: str, now: _dt.datetime | None = None) -> Path:
    current = now or _dt.datetime.now()
    stamp = current.strftime("%Y%m%d-%H%M%S")
    return TERMINAL_DIR / f"{stamp}_{_safe_name(name)}.log"


def write_latest_pointer(log_path: Path) -> None:
    TERMINAL_DIR.mkdir(parents=True, exist_ok=True)
    LATEST_POINTER.write_text(log_path.as_posix() + "\n", encoding="utf-8")


def read_latest_pointer() -> Path | None:
    if not LATEST_POINTER.exists():
        return None
    value = LATEST_POINTER.read_text(encoding="utf-8").strip()
    if not value:
        return None
    return Path(value)


def _is_allowed_terminal_artifact(path_text: str) -> bool:
    return path_text == LATEST_POINTER.as_posix() or (path_text.startswith(TERMINAL_DIR.as_posix() + "/") and path_text.endswith(".log"))


def git_dirty_paths() -> list[str]:
    proc = subprocess.run(["git", "status", "--porcelain"], text=True, capture_output=True, check=False)
    paths: list[str] = []
    for line in proc.stdout.splitlines():
        if not line.strip():
            continue
        paths.append(line[3:])
    return paths


def terminal_status() -> tuple[str, str]:
    latest = read_latest_pointer()
    if latest is None:
        return "PASS_NO_LOG", "No latest terminal log pointer exists."
    if not latest.exists():
        return "FAIL_INVALID_POINTER", f"Latest terminal log pointer targets missing file: {latest.as_posix()}"
    return "PASS_LOG_READY", f"Latest terminal log: {latest.as_posix()}"


def run_logged(name: str, command: list[str]) -> int:
    if not command:
        print("FAIL_NO_COMMAND")
        return 2
    TERMINAL_DIR.mkdir(parents=True, exist_ok=True)
    log_path = make_log_path(name)
    write_latest_pointer(log_path)
    with log_path.open("w", encoding="utf-8") as log:
        def emit(line: str) -> None:
            print(line)
            log.write(line + "\n")
            log.flush()
        emit(f"terminal_log={log_path.as_posix()}")
        emit("### RUN: " + " ".join(command))
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=os.environ.copy())
        assert proc.stdout is not None
        for raw in proc.stdout:
            line = raw.rstrip("\n")
            print(line)
            log.write(line + "\n")
        code = proc.wait()
        emit(f"### EXIT: {code}")
        emit("### RESULT: PASS ###" if code == 0 else "### RESULT: FAIL ###")
    return code


def upload_terminal_output() -> int:
    outcome, message = terminal_status()
    print(outcome)
    print(message)
    if outcome != "PASS_LOG_READY":
        return 1
    dirty = git_dirty_paths()
    forbidden = [p for p in dirty if not _is_allowed_terminal_artifact(p)]
    if forbidden:
        print("FAIL_DIRTY_NON_LOG_FILES")
        for item in forbidden:
            print(item)
        return 1
    latest = read_latest_pointer()
    assert latest is not None
    subprocess.run(["git", "add", latest.as_posix(), LATEST_POINTER.as_posix()], check=True)
    diff = subprocess.run(["git", "diff", "--cached", "--quiet"], check=False)
    if diff.returncode == 0:
        print("PASS_ALREADY_UPLOADED")
        return 0
    subprocess.run(["git", "commit", "-m", "Upload terminal output log"], check=True)
    pushed = subprocess.run(["git", "push"], check=False)
    if pushed.returncode != 0:
        print("FAIL_PUSH_FAILED")
        return pushed.returncode
    print("PASS_UPLOADED")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        print("Usage: terminal_logging.py run-logged <name> -- <command...> | terminal-status | terminal-upload")
        return 2
    mode = args.pop(0)
    if mode == "terminal-status":
        outcome, message = terminal_status()
        print(outcome)
        print(message)
        return 0 if outcome.startswith("PASS") else 1
    if mode == "terminal-upload":
        return upload_terminal_output()
    if mode == "run-logged":
        if "--" not in args:
            print("FAIL_MISSING_SEPARATOR")
            return 2
        sep = args.index("--")
        name = args[0] if sep > 0 else "run"
        command = args[sep + 1:]
        return run_logged(name, command)
    print("FAIL_UNKNOWN_MODE")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
