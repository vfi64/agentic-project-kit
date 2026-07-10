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

from agentic_project_kit.workspace import LEGACY_DEFAULTS, load_workspace

TERMINAL_DIR = Path(LEGACY_DEFAULTS.terminal_reports_root)
LATEST_POINTER = TERMINAL_DIR / "LATEST_TERMINAL_LOG.txt"


def _safe_name(name: str) -> str:
    safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in name.strip())
    return safe or "run"


def _terminal_dir(root: Path = Path(".")) -> Path:
    if TERMINAL_DIR != Path(LEGACY_DEFAULTS.terminal_reports_root):
        return TERMINAL_DIR
    return load_workspace(root).terminal_reports_dir()


def _latest_pointer(root: Path = Path(".")) -> Path:
    if LATEST_POINTER != TERMINAL_DIR / "LATEST_TERMINAL_LOG.txt":
        return LATEST_POINTER
    return load_workspace(root).latest_terminal_log_pointer()


def make_log_path(name: str, now: _dt.datetime | None = None) -> Path:
    current = now or _dt.datetime.now()
    stamp = current.strftime("%Y%m%d-%H%M%S")
    return _terminal_dir() / f"{stamp}_{_safe_name(name)}.log"


def write_latest_pointer(log_path: Path) -> None:
    pointer = _latest_pointer()
    pointer.parent.mkdir(parents=True, exist_ok=True)
    pointer.write_text(log_path.as_posix() + "\n", encoding="utf-8")


def read_latest_pointer() -> Path | None:
    pointer = _latest_pointer()
    if not pointer.exists():
        return None
    value = pointer.read_text(encoding="utf-8").strip()
    if not value:
        return None
    return Path(value)


def _is_allowed_terminal_artifact(path_text: str) -> bool:
    workspace = load_workspace(Path("."))
    latest = workspace.path_text(_latest_pointer())
    terminal_dir = workspace.path_text(_terminal_dir())
    return path_text == latest or (path_text.startswith(terminal_dir + "/") and path_text.endswith(".log"))


def git_dirty_paths() -> list[str]:
    proc = subprocess.run(["git", "status", "--porcelain"], text=True, capture_output=True, check=False)
    paths: list[str] = []
    for line in proc.stdout.splitlines():
        if not line.strip():
            continue
        paths.append(line[3:])
    return paths




def terminal_clean_check() -> tuple[str, str]:
    """Classify dirty state while allowing terminal-log artifacts."""

    dirty = git_dirty_paths()
    if not dirty:
        return "PASS_CLEAN", "Working tree is clean."
    forbidden = [path for path in dirty if not _is_allowed_terminal_artifact(path)]
    if forbidden:
        return "FAIL_DIRTY_NON_LOG_FILES", chr(10).join(forbidden)
    return "PASS_ONLY_TERMINAL_LOG_DIRTY", chr(10).join(dirty)


def remote_mutation_preflight() -> tuple[str, str]:
    """Require a fully clean worktree before remote mutations or merge/sync verification."""

    dirty = git_dirty_paths()
    if dirty:
        return "FAIL_DIRTY_WORKTREE_BEFORE_REMOTE_MUTATION", chr(10).join(dirty)
    return "PASS_CLEAN_FOR_REMOTE_MUTATION", "Working tree is clean for remote mutation or merge verification."
def terminal_status() -> tuple[str, str]:
    latest = read_latest_pointer()
    if latest is None:
        return "PASS_NO_LOG", "No latest terminal log pointer exists."
    if not latest.exists():
        return "FAIL_INVALID_POINTER", f"Latest terminal log pointer targets missing file: {latest.as_posix()}"
    return "PASS_LOG_READY", f"Latest terminal log: {latest.as_posix()}"


def _has_result_marker(text: str) -> bool:
    return "### RESULT: PASS ###" in text or "### RESULT: FAIL ###" in text or "### RESULT: PENDING ###" in text


def finalize_terminal_log(tmp_log: Path, name: str) -> tuple[str, str]:
    source = Path(tmp_log)
    if not source.exists():
        return "FAIL_SOURCE_MISSING", source.as_posix()
    source_text = source.read_text(encoding="utf-8")
    if not _has_result_marker(source_text):
        return "FAIL_MISSING_RESULT_MARKER", source.as_posix()
    source_resolved = source.resolve()
    terminal_dir = _terminal_dir()
    terminal_resolved = terminal_dir.resolve()
    try:
        source_resolved.relative_to(terminal_resolved)
    except ValueError:
        source_inside_terminal_dir = False
    else:
        source_inside_terminal_dir = True
    if source_inside_terminal_dir:
        return "FAIL_SOURCE_INSIDE_TERMINAL_DIR", source.as_posix()
    terminal_dir.mkdir(parents=True, exist_ok=True)
    target = make_log_path(name)
    target.write_text(source_text, encoding="utf-8")
    write_latest_pointer(target)
    return "PASS_FINALIZED", target.as_posix()


def run_logged(name: str, command: list[str]) -> int:
    if not command:
        print("FAIL_NO_COMMAND")
        return 2
    _terminal_dir().mkdir(parents=True, exist_ok=True)
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


def _current_branch() -> str:
    proc = subprocess.run(["git", "branch", "--show-current"], text=True, capture_output=True, check=False)
    return proc.stdout.strip() if proc.returncode == 0 else ""


def _refuse_unsafe_mutation_branch(required_branch: str = "", allow_main: bool = False) -> tuple[bool, str]:
    branch = _current_branch()
    if required_branch and branch != required_branch:
        return False, f"FAIL_BRANCH_MISMATCH actual={branch or 'UNKNOWN'} required={required_branch}"
    if branch == "main" and not allow_main:
        return False, "FAIL_MAIN_MUTATION_NOT_ALLOWED"
    if not branch:
        return False, "FAIL_NO_CURRENT_BRANCH"
    return True, branch


def upload_terminal_output(required_branch: str = "", allow_main: bool = False) -> int:
    branch_ok, branch_message = _refuse_unsafe_mutation_branch(required_branch=required_branch, allow_main=allow_main)
    if not branch_ok:
        print(branch_message)
        return 1
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
    subprocess.run(["git", "add", latest.as_posix(), _latest_pointer().as_posix()], check=True)
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
    if mode == "terminal-clean-check":
        outcome, message = terminal_clean_check()
        print(outcome)
        print(message)
        return 0 if outcome.startswith("PASS") else 1
    if mode == "terminal-remote-preflight":
        outcome, message = remote_mutation_preflight()
        print(outcome)
        print(message)
        return 0 if outcome.startswith("PASS") else 1
    if mode == "terminal-upload":
        return upload_terminal_output()
    if mode == "terminal-finalize":
        if len(args) != 2:
            print("FAIL_USAGE")
            print("Usage: terminal-finalize <tmp-log> <name>")
            return 2
        outcome, message = finalize_terminal_log(Path(args[0]), args[1])
        print(outcome)
        print(message)
        return 0 if outcome == "PASS_FINALIZED" else 1
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
