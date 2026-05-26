from __future__ import annotations

from dataclasses import dataclass
import importlib
import os


@dataclass(frozen=True)
class WindowGuardResult:
    ok: bool
    tkinter_importable: bool
    native_tkinter_importable: bool
    message: str


def check_window_launch_ready() -> WindowGuardResult:
    try:
        importlib.import_module("tkinter")
        tkinter_importable = True
    except Exception as exc:
        return WindowGuardResult(False, False, False, f"tkinter import failed: {exc}")
    try:
        importlib.import_module("_tkinter")
        native_importable = True
    except Exception as exc:
        return WindowGuardResult(False, tkinter_importable, False, f"native _tkinter import failed: {exc}")
    if os.environ.get("AGENTIC_KIT_ALLOW_TK_WINDOW_SMOKE") != "1":
        return WindowGuardResult(
            False,
            tkinter_importable,
            native_importable,
            "real Tk window smoke requires AGENTIC_KIT_ALLOW_TK_WINDOW_SMOKE=1",
        )
    return WindowGuardResult(True, tkinter_importable, native_importable, "window launch guard passed")


def render_window_guard_result(result: WindowGuardResult) -> str:
    status = "READY" if result.ok else "BLOCKED"
    return "\n".join((
        "GUI WINDOW GUARD",
        f"window_launch_ready={str(result.ok).lower()}",
        f"tkinter_importable={str(result.tkinter_importable).lower()}",
        f"native_tkinter_importable={str(result.native_tkinter_importable).lower()}",
        f"message={result.message}",
        f"window_guard_status={status}",
    ))
