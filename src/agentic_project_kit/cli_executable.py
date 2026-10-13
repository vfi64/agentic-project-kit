from __future__ import annotations

from pathlib import Path
import shlex
import shutil
import sys


def default_agentic_kit(root: Path) -> str:
    owned = owned_agentic_kit(root)
    if owned:
        return owned
    current = current_agentic_kit()
    if current:
        return current
    found = shutil.which("agentic-kit")
    return found or "agentic-kit"


def owned_agentic_kit(root: Path, *, allow_declared: bool = True) -> str:
    for python in _owned_interpreters(root, allow_declared=allow_declared):
        local = python.parent / (
            "agentic-kit.exe" if python.name.endswith(".exe") else "agentic-kit"
        )
        if local_agentic_kit_is_runnable(local):
            return _display_path(local)
    return ""


def default_python(root: Path) -> str:
    for local in _owned_interpreters(root):
        if local_executable_is_runnable(local):
            return _display_path(local)
    return sys.executable


def _owned_interpreters(root: Path, *, allow_declared: bool = True) -> tuple[Path, ...]:
    """Use GF-021 candidate order without repeating metadata subprocess probes."""
    from agentic_project_kit.kit_installation import installation_candidates
    from agentic_project_kit.workspace import load_workspace
    import yaml

    try:
        declared = (
            (load_workspace(root, suppress_legacy_profile_warning=True).kit.interpreter or None)
            if allow_declared
            else None
        )
    except (RuntimeError, ValueError, OSError, yaml.YAMLError):
        # Diagnostics retain their own invalid-manifest gate. Discovery must
        # still be able to launch that diagnostic from the running interpreter.
        declared = None
    candidates = installation_candidates(root, declared_interpreter=declared)
    return tuple(
        root / item.python.relative_to(root.absolute())
        if item.source == "workspace_venv" and not root.is_absolute()
        else item.python
        for item in candidates
    )


def current_agentic_kit() -> str:
    current = Path(sys.executable).parent / (
        "agentic-kit.exe" if Path(sys.executable).suffix.lower() == ".exe" else "agentic-kit"
    )
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
