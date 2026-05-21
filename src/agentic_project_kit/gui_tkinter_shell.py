from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Sequence

from agentic_project_kit.action_registry import list_actions
from agentic_project_kit.gui_presenter import build_no_window_presenter_result

@dataclass(frozen=True)
class MenuItemSpec:
    label: str
    command_id: str
    enabled: bool = True

@dataclass(frozen=True)
class MenuSpec:
    label: str
    items: tuple[MenuItemSpec, ...]

@dataclass(frozen=True)
class ButtonSpec:
    command_id: str
    label: str
    tooltip: str
    icon_text: str
    safety_class: str
    enabled: bool

@dataclass(frozen=True)
class TkinterShellDesignSpec:
    menu_bar: tuple[MenuSpec, ...]
    toolbar: tuple[ButtonSpec, ...]
    action_buttons: tuple[ButtonSpec, ...]

@dataclass(frozen=True)
class TkinterShellSpec:
    title: str
    status: str
    action_count: int
    destructive_actions_enabled: bool
    preview: str
    design: TkinterShellDesignSpec

def _button(command_id: str, label: str, tooltip: str, icon_text: str, safety_class: str, enabled: bool = True) -> ButtonSpec:
    return ButtonSpec(command_id, label, tooltip, icon_text, safety_class, enabled)

def build_windows_style_design_spec() -> TkinterShellDesignSpec:
    menu_bar = (
        MenuSpec("File", (MenuItemSpec("Refresh status", "refresh-status"), MenuItemSpec("Open latest log", "open-latest-log"), MenuItemSpec("Exit", "exit"))),
        MenuSpec("Actions", (MenuItemSpec("Doctor", "doctor"), MenuItemSpec("Check docs", "check-docs"), MenuItemSpec("GUI dry-run", "gui-dry-run"))),
        MenuSpec("View", (MenuItemSpec("Show output log", "show-output-log"), MenuItemSpec("Show last summary", "show-last-summary"))),
        MenuSpec("Help", (MenuItemSpec("GUI help", "gui-help"), MenuItemSpec("About", "about"))),
    )
    toolbar = (
        _button("refresh-status", "Refresh", "Refresh repository status without changing files.", "Refresh", "read_only"),
        _button("doctor", "Doctor", "Run the deterministic project doctor.", "Check", "read_only"),
        _button("check-docs", "Docs", "Run documentation gates.", "Docs", "read_only"),
        _button("gui-dry-run", "Dry Run", "Validate GUI readiness without opening a window.", "Run", "read_only"),
    )
    action_buttons = (
        _button("status", "Status", "Show branch, dirty state, and latest summary.", "S", "read_only"),
        _button("actions-list", "Actions", "List registered actions and their safety classes.", "A", "read_only"),
        _button("doctor", "Doctor", "Run project doctor; no repository mutation.", "D", "read_only"),
        _button("check-docs", "Check Docs", "Validate documentation coverage and lifecycle rules.", "C", "read_only"),
        _button("release-verify", "Release Verify", "Verify an already published release. Requires a version parameter.", "R", "read_only"),
        _button("release-publish", "Release Publish", "Disabled in the initial GUI until explicit release guards exist.", "!", "destructive", False),
    )
    return TkinterShellDesignSpec(menu_bar, toolbar, action_buttons)

def build_tkinter_shell_spec() -> TkinterShellSpec:
    presenter = build_no_window_presenter_result(list_actions())
    return TkinterShellSpec("agentic-project-kit Cockpit", "tkinter-shell-ready" if presenter.ok else "tkinter-shell-blocked", presenter.action_count, False, presenter.rendered, build_windows_style_design_spec())

def create_tkinter_root(tk_factory: Callable[[], object] | None = None) -> object:
    if tk_factory is not None:
        return tk_factory()
    import tkinter as tk
    return tk.Tk()

def configure_tkinter_root(root: object, spec: TkinterShellSpec) -> None:
    if hasattr(root, "title"):
        root.title(spec.title)
    if hasattr(root, "geometry"):
        root.geometry("1000x650")

def render_tkinter_shell_summary(spec: TkinterShellSpec) -> str:
    return "\n".join(("TKINTER SHELL", f"title={spec.title}", f"status={spec.status}", f"action_count={spec.action_count}", f"menu_count={len(spec.design.menu_bar)}", f"toolbar_button_count={len(spec.design.toolbar)}", f"action_button_count={len(spec.design.action_buttons)}", f"destructive_actions_enabled={str(spec.destructive_actions_enabled).lower()}"))

def main(argv: Sequence[str] | None = None) -> int:
    args = list(argv or [])
    if args == ["--no-window-smoke"]:
        print(render_tkinter_shell_summary(build_tkinter_shell_spec()))
        print("### RESULT: PASS ###")
        return 0
    print("ERROR: usage: python -m agentic_project_kit.gui_tkinter_shell --no-window-smoke")
    print("### RESULT: FAIL ###")
    return 2

if __name__ == "__main__":
    import sys
    raise SystemExit(main(sys.argv[1:]))
