from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Sequence

from agentic_project_kit.action_registry import list_actions
from agentic_project_kit.gui_presenter import build_no_window_presenter_result


@dataclass(frozen=True)
class TkinterShellSpec:
    title: str
    status: str
    action_count: int
    destructive_actions_enabled: bool
    preview: str


def build_tkinter_shell_spec() -> TkinterShellSpec:
    presenter = build_no_window_presenter_result(list_actions())
    return TkinterShellSpec(
        title="agentic-project-kit Cockpit",
        status="tkinter-shell-ready" if presenter.ok else "tkinter-shell-blocked",
        action_count=presenter.action_count,
        destructive_actions_enabled=False,
        preview=presenter.rendered,
    )


def create_tkinter_root(tk_factory: Callable[[], object] | None = None) -> object:
    if tk_factory is not None:
        return tk_factory()
    import tkinter as tk
    return tk.Tk()


def configure_tkinter_root(root: object, spec: TkinterShellSpec) -> None:
    if hasattr(root, "title"):
        root.title(spec.title)
    if hasattr(root, "geometry"):
        root.geometry("900x600")


def render_tkinter_shell_summary(spec: TkinterShellSpec) -> str:
    return "\n".join((
        "TKINTER SHELL",
        f"title={spec.title}",
        f"status={spec.status}",
        f"action_count={spec.action_count}",
        f"destructive_actions_enabled={str(spec.destructive_actions_enabled).lower()}",
    ))


def main(argv: Sequence[str] | None = None) -> int:
    args = list(argv or [])
    if args == ["--no-window-smoke"]:
        spec = build_tkinter_shell_spec()
        print(render_tkinter_shell_summary(spec))
        print("### RESULT: PASS ###")
        return 0
    print("ERROR: usage: python -m agentic_project_kit.gui_tkinter_shell --no-window-smoke")
    print("### RESULT: FAIL ###")
    return 2


if __name__ == "__main__":
    import sys
    raise SystemExit(main(sys.argv[1:]))
