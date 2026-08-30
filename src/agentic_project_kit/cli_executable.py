from __future__ import annotations

from pathlib import Path
import shlex
import shutil
import sys


def default_agentic_kit(root: Path) -> str:
    local = root / ".venv" / "bin" / "agentic-kit"
    if local_agentic_kit_is_runnable(local):
        return _display_path(local)
    current = current_agentic_kit()
    if current:
        return current
    found = shutil.which("agentic-kit")
    return found or "agentic-kit"


def default_python(root: Path) -> str:
    local = root / ".venv" / "bin" / "python"
    if local_executable_is_runnable(local):
        return _display_path(local)
    return sys.executable


def current_agentic_kit() -> str:
    current = Path(sys.executable).parent / "agentic-kit"
    if local_agentic_kit_is_runnable(current):
        return _display_path(current)
    return ""


def local_agentic_kit_is_runnable(path: Path) -> bool:
    return local_executable_is_runnable(path)


def local_executable_is_runnable(path: Path) -> bool:
    if not path.exists():
        return False
    try:
        first_line = path.read_text(encoding="utf-8", errors="ignore").splitlines()[0]
    except IndexError:
        return True
    except OSError:
        return False
    if not first_line.startswith("#!"):
        return True
    try:
        executable = shlex.split(first_line[2:])[0]
    except (IndexError, ValueError):
        return False
    if executable == "/usr/bin/env":
        return Path(executable).exists()
    if executable.startswith("/"):
        return Path(executable).exists()
    return True


def _display_path(path: Path) -> str:
    text = path.as_posix()
    if not path.is_absolute() and not text.startswith("./"):
        return f"./{text}"
    return text
