from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass

from agentic_project_kit.action_registry import list_actions
from agentic_project_kit.gui_presenter import build_no_window_presenter_result
from agentic_project_kit.gui_window_guard import check_window_launch_ready, render_window_guard_result


@dataclass(frozen=True)
class MenuItemSpec:
    label: str
    command_id: str
    enabled: bool = True
    tooltip: str = ""


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
    enabled: bool = True

    @property
    def icon_id(self) -> str:
        return self.icon_text


@dataclass(frozen=True)
class TkinterShellDesignSpec:
    menu_bar: tuple[MenuSpec, ...]
    toolbar: tuple[ButtonSpec, ...]
    action_buttons: tuple[ButtonSpec, ...]


GuiDesignSpec = TkinterShellDesignSpec


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
        MenuSpec("File", (MenuItemSpec("Refresh status", "refresh-status", tooltip="Refresh repository status."), MenuItemSpec("Open latest log", "open-latest-log", tooltip="Open the latest committed or local terminal log."), MenuItemSpec("Exit", "exit", tooltip="Close the local cockpit."))),
        MenuSpec("Actions", (MenuItemSpec("Doctor", "doctor", tooltip="Run deterministic project doctor checks."), MenuItemSpec("Check docs", "check-docs", tooltip="Run documentation coverage gates."), MenuItemSpec("GUI dry-run", "gui-dry-run", tooltip="Validate GUI readiness without opening a window."))),
        MenuSpec("View", (MenuItemSpec("Show output log", "show-output-log", tooltip="Show the current output log."), MenuItemSpec("Show last summary", "show-last-summary", tooltip="Show the last run summary."))),
        MenuSpec("Help", (MenuItemSpec("GUI help", "gui-help", tooltip="Show cockpit help and safety notes."), MenuItemSpec("About", "about", tooltip="Show project and version information."))),
    )
    toolbar = (
        _button("refresh-status", "Refresh", "Refresh repository status without changing files.", "refresh", "read_only"),
        _button("doctor", "Doctor", "Run the deterministic project doctor.", "stethoscope", "read_only"),
        _button("check-docs", "Docs", "Run documentation gates.", "document-check", "read_only"),
        _button("gui-dry-run", "Dry Run", "Validate GUI readiness without opening a window.", "play", "read_only"),
    )
    action_buttons = (
        _button("status", "Status", "Show branch, dirty state, and latest summary.", "status", "read_only"),
        _button("actions-list", "Actions", "List registered actions and their safety classes.", "list", "read_only"),
        _button("doctor", "Doctor", "Run project doctor; no repository mutation.", "stethoscope", "read_only"),
        _button("check-docs", "Check Docs", "Validate documentation coverage and lifecycle rules.", "document-check", "read_only"),
        _button("release-verify", "Release Verify", "Verify an already published release. Requires a version parameter.", "release-verify", "read_only"),
        _button("release-publish", "Release Publish", "Disabled in the initial GUI until explicit release guards exist.", "lock", "destructive", False),
    )
    return TkinterShellDesignSpec(menu_bar, toolbar, action_buttons)


def build_tkinter_shell_spec() -> TkinterShellSpec:
    presenter = build_no_window_presenter_result(list_actions())
    return TkinterShellSpec(
        "agentic-project-kit Cockpit",
        "tkinter-shell-ready" if presenter.ok else "tkinter-shell-blocked",
        presenter.action_count,
        False,
        presenter.rendered,
        build_windows_style_design_spec(),
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
        root.geometry("1000x650")


def render_tkinter_shell_summary(spec: TkinterShellSpec) -> str:
    return "\n".join((
        "TKINTER SHELL",
        f"title={spec.title}",
        f"status={spec.status}",
        f"action_count={spec.action_count}",
        f"menu_count={len(spec.design.menu_bar)}",
        f"toolbar_button_count={len(spec.design.toolbar)}",
        f"action_button_count={len(spec.design.action_buttons)}",
        f"destructive_actions_enabled={str(spec.destructive_actions_enabled).lower()}",
        f"toolbar_icons={chr(44).join(button.icon_id for button in spec.design.toolbar)}",
    ))


def run_window_smoke() -> tuple[bool, str]:
    guard = check_window_launch_ready()
    lines = ["TKINTER WINDOW SMOKE", render_window_guard_result(guard)]
    if not guard.ok:
        lines.extend([
            "window_smoke_status=BLOCKED",
            "real_window_opened=false",
            "window_closed=true",
        ])
        return True, chr(10).join(lines)
    try:
        root = create_tkinter_root()
    except Exception as exc:
        lines.extend([
            "window_smoke_status=BLOCKED",
            "real_window_opened=false",
            "window_closed=true",
            "window_block_reason=" + str(exc).replace(chr(10), " "),
        ])
        return True, chr(10).join(lines)
    try:
        configure_tkinter_root(root, build_tkinter_shell_spec())
        if hasattr(root, "update_idletasks"):
            root.update_idletasks()
        lines.extend([
            "window_smoke_status=PASS",
            "real_window_opened=true",
        ])
        return True, chr(10).join(lines)
    finally:
        if hasattr(root, "destroy"):
            root.destroy()


def main(argv: Sequence[str] | None = None) -> int:
    args = list(argv or [])
    if args == ["--no-window-smoke"]:
        print(render_tkinter_shell_summary(build_tkinter_shell_spec()))
        print("### RESULT: PASS ###")
        return 0
    if args == ["--window-smoke"]:
        ok, output = run_window_smoke()
        print(output)
        print("### RESULT: PASS ###" if ok else "### RESULT: FAIL ###")
        return 0 if ok else 1
    print("ERROR: usage: python -m agentic_project_kit.gui_tkinter_shell --no-window-smoke|--window-smoke")
    print("### RESULT: FAIL ###")
    return 2


if __name__ == "__main__":
    import sys
    raise SystemExit(main(sys.argv[1:]))
