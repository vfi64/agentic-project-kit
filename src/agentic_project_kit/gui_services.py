"""GUI-independent execution boundary shared by both desktop presentations."""

from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import Future
import json
from pathlib import Path
import subprocess
import sys
from threading import Thread
from typing import Any, TypeVar

from agentic_project_kit.kit_installation import CLI_MODULE, discover_kit_installation
from agentic_project_kit.workspace import load_workspace


T = TypeVar("T")


def completed_gui_status(completed: subprocess.CompletedProcess[str]) -> str:
    try:
        payload = json.loads(completed.stdout)
    except ValueError:
        payload = None
    raw = str(payload.get("result_status", payload.get("STATE", payload.get("state", "")))) if isinstance(payload, dict) else ""
    if completed.returncode != 0:
        return raw if raw.upper() in {"BLOCK", "BLOCKED", "FAIL", "FAILED", "ERROR", "HARD-FAIL"} else "ERROR"
    return raw or "PASS"


def gui_cli_argv(root: Path) -> tuple[str, ...]:
    """Prefer workspace ownership; otherwise use the GUI's own Python, never PATH."""
    workspace = load_workspace(root, suppress_legacy_profile_warning=True)
    declared = workspace.kit.interpreter or None
    resolution = discover_kit_installation(root, declared_interpreter=declared)
    if resolution.status == "FOUND":
        return resolution.cli_argv
    if declared or resolution.status == "BLOCKED":
        reasons = ", ".join(item.reason for item in resolution.observations)
        raise RuntimeError(f"Workspace Kit installation is unavailable: {reasons}")
    return (sys.executable, "-m", CLI_MODULE)


def run_gui_command(root: Path, parts: tuple[str, ...]) -> subprocess.CompletedProcess[str]:
    try:
        command = [*gui_cli_argv(root), *parts]
        completed = subprocess.run(
            command, cwd=root, text=True, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, check=False,
        )
        if "--json" in parts and completed.returncode == 0:
            try:
                payload = json.loads(completed.stdout)
            except ValueError:
                payload = None
            if not isinstance(payload, dict):
                return subprocess.CompletedProcess(
                    command, 65, completed.stdout,
                    completed.stderr + "\nInvalid structured Kit result; success was not verified.",
                )
            if str(payload.get("result_status", "")).upper() in {"BLOCK", "BLOCKED", "FAIL", "FAILED", "ERROR", "HARD-FAIL"}:
                return subprocess.CompletedProcess(command, 2, completed.stdout, completed.stderr)
        return completed
    except (OSError, RuntimeError) as exc:
        return subprocess.CompletedProcess(list(parts), 127, "", str(exc))


def invoke_gui_service(owner: Any, operation: Callable[[], T], *, label: str) -> T:
    """Legacy adapter stays synchronous; the guided adapter supplies a Tk bridge."""
    bridge = getattr(owner, "service_bridge", None)
    return operation() if bridge is None else bridge.call(operation, label=label)


def run_gui_action_command(command: tuple[str, ...], root: Path) -> subprocess.CompletedProcess[str]:
    """Executor adapter for already registry-validated read-only actions."""
    if command and command[0] == "agentic-kit":
        return run_gui_command(root, command[1:])
    try:
        return subprocess.run(list(command), cwd=root, text=True, capture_output=True, check=False)
    except OSError as exc:
        return subprocess.CompletedProcess(list(command), 127, "", str(exc))


class BackgroundOperation:
    """One operation at a time; completion/failure stays observable until consumed.

    Worker threads receive only application functions, never widgets or Tk calls.
    No cancellation is exposed: terminating a thread would not undo side effects.
    """

    def __init__(self) -> None:
        self.pending: Future[Any] | None = None

    def start(self, operation: Callable[[], T]) -> Future[T]:
        if self.pending is not None:
            raise RuntimeError("A GUI operation is already pending; inspect its result first.")
        future: Future[T] = Future()
        self.pending = future

        def run() -> None:
            try:
                future.set_result(operation())
            except BaseException as exc:
                future.set_exception(exc)

        Thread(target=run, name="kit-gui-operation", daemon=True).start()
        return future

    def consume(self) -> Any:
        if self.pending is None or not self.pending.done():
            raise RuntimeError("No completed GUI operation is available.")
        future = self.pending
        self.pending = None
        return future.result()
