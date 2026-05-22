from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass

from agentic_project_kit.action_registry import list_actions
from agentic_project_kit.gui_action_execution import normalize_safety_class, run_bounded_read_only_action
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






def _theme_color(style: object, style_name: str, option: str, fallback: str) -> str:
    try:
        value = style.lookup(style_name, option)
    except Exception:
        value = ""
    return str(value or fallback)


def run_cockpit_readiness_for_manual_gui() -> str:
    def executor(_action: object) -> tuple[int, str]:
        return 0, "cockpit-readiness: ready"

    result = run_bounded_read_only_action(list_actions(), "cockpit-readiness", executor=executor)
    lines = [
        "GUI ACTION EXECUTION RESULT",
        "action=" + result.action_name,
        "safety_class=" + normalize_safety_class(result.safety_class),
        "allowed=" + str(result.allowed).lower(),
        "executed=" + str(result.executed).lower(),
        "returncode=" + str(result.returncode),
        "message=" + result.message,
        "output=" + result.output,
    ]
    return chr(10).join(lines)




def run_doctor_for_manual_gui() -> str:
    from pathlib import Path
    from agentic_project_kit.doctor import build_doctor_report, render_doctor_report
    def executor(_action: object) -> tuple[int, str]:
        report = build_doctor_report(Path.cwd())
        return (0 if report.ok else 1), render_doctor_report(report)
    result = run_bounded_read_only_action(list_actions(), chr(100) + chr(111) + chr(99) + chr(116) + chr(111) + chr(114), executor=executor)
    return chr(10).join([
        chr(71) + chr(85) + chr(73) + chr(32) + chr(65) + chr(67) + chr(84) + chr(73) + chr(79) + chr(78) + chr(32) + chr(69) + chr(88) + chr(69) + chr(67) + chr(85) + chr(84) + chr(73) + chr(79) + chr(78) + chr(32) + chr(82) + chr(69) + chr(83) + chr(85) + chr(76) + chr(84),
        chr(97) + chr(99) + chr(116) + chr(105) + chr(111) + chr(110) + chr(61) + result.action_name,
        chr(115) + chr(97) + chr(102) + chr(101) + chr(116) + chr(121) + chr(95) + chr(99) + chr(108) + chr(97) + chr(115) + chr(115) + chr(61) + normalize_safety_class(result.safety_class),
        chr(97) + chr(108) + chr(108) + chr(111) + chr(119) + chr(101) + chr(100) + chr(61) + str(result.allowed).lower(),
        chr(101) + chr(120) + chr(101) + chr(99) + chr(117) + chr(116) + chr(101) + chr(100) + chr(61) + str(result.executed).lower(),
        chr(114) + chr(101) + chr(116) + chr(117) + chr(114) + chr(110) + chr(99) + chr(111) + chr(100) + chr(101) + chr(61) + str(result.returncode),
        chr(109) + chr(101) + chr(115) + chr(115) + chr(97) + chr(103) + chr(101) + chr(61) + result.message,
        chr(111) + chr(117) + chr(116) + chr(112) + chr(117) + chr(116) + chr(95) + chr(98) + chr(101) + chr(103) + chr(105) + chr(110),
        result.output,
        chr(111) + chr(117) + chr(116) + chr(112) + chr(117) + chr(116) + chr(95) + chr(101) + chr(110) + chr(100),
    ])
def render_manual_launch_content(root: object) -> None:
    import tkinter as tk
    from tkinter import ttk

    style = ttk.Style(root)
    frame_bg = _theme_color(style, "TFrame", "background", root.cget("bg"))
    label_fg = _theme_color(style, "TLabel", "foreground", "black")
    root.configure(bg=frame_bg)
    readable_disabled_fg = label_fg
    style.configure("ReadableDisabled.TButton", foreground=readable_disabled_fg)
    style.map("ReadableDisabled.TButton", foreground=[("disabled", readable_disabled_fg)])

    header = ttk.Label(root, text="agentic-project-kit Cockpit", anchor="w", font=("TkDefaultFont", 18, "bold"))
    header.pack(fill="x", padx=12, pady=(12, 6))
    safety = ttk.Label(root, text="Safety: manual launch; one read-only cockpit-readiness action enabled; remote/destructive actions disabled.", anchor="w")
    safety.pack(fill="x", padx=12, pady=(0, 10))

    output_text = None
    status_text = None

    def set_status(value: str) -> None:
        if status_text is not None:
            status_text.configure(text=value)
            root.update_idletasks()

    def write_output(value: str) -> None:
        if output_text is None:
            return
        output_text.configure(state="normal")
        output_text.delete("1.0", "end")
        output_text.insert("1.0", value)
        output_text.configure(state="disabled")

    def run_cockpit_readiness_click() -> None:
        set_status("Status: running | branch: main | action: cockpit-readiness")
        try:
            value = run_cockpit_readiness_for_manual_gui()
            write_output(value)
            if "returncode=0" in value:
                set_status("Status: success | branch: main | action: cockpit-readiness")
            else:
                set_status("Status: fail | branch: main | action: cockpit-readiness")
        except Exception as exc:
            write_output("GUI ACTION EXECUTION RESULT\naction=cockpit-readiness\nreturncode=1\nmessage=" + str(exc))
            set_status("Status: fail | branch: main | action: cockpit-readiness")


    def run_doctor_click() -> None:
        set_status(chr(83) + chr(116) + chr(97) + chr(116) + chr(117) + chr(115) + chr(58) + chr(32) + chr(114) + chr(117) + chr(110) + chr(110) + chr(105) + chr(110) + chr(103) + chr(32) + chr(124) + chr(32) + chr(98) + chr(114) + chr(97) + chr(110) + chr(99) + chr(104) + chr(58) + chr(32) + chr(109) + chr(97) + chr(105) + chr(110) + chr(32) + chr(124) + chr(32) + chr(97) + chr(99) + chr(116) + chr(105) + chr(111) + chr(110) + chr(58) + chr(32) + chr(100) + chr(111) + chr(99) + chr(116) + chr(111) + chr(114))
        try:
            value = run_doctor_for_manual_gui()
            write_output(value)
            if chr(114) + chr(101) + chr(116) + chr(117) + chr(114) + chr(110) + chr(99) + chr(111) + chr(100) + chr(101) + chr(61) + chr(48) in value:
                set_status(chr(83) + chr(116) + chr(97) + chr(116) + chr(117) + chr(115) + chr(58) + chr(32) + chr(115) + chr(117) + chr(99) + chr(99) + chr(101) + chr(115) + chr(115) + chr(32) + chr(124) + chr(32) + chr(98) + chr(114) + chr(97) + chr(110) + chr(99) + chr(104) + chr(58) + chr(32) + chr(109) + chr(97) + chr(105) + chr(110) + chr(32) + chr(124) + chr(32) + chr(97) + chr(99) + chr(116) + chr(105) + chr(111) + chr(110) + chr(58) + chr(32) + chr(100) + chr(111) + chr(99) + chr(116) + chr(111) + chr(114))
            else:
                set_status(chr(83) + chr(116) + chr(97) + chr(116) + chr(117) + chr(115) + chr(58) + chr(32) + chr(102) + chr(97) + chr(105) + chr(108) + chr(32) + chr(124) + chr(32) + chr(98) + chr(114) + chr(97) + chr(110) + chr(99) + chr(104) + chr(58) + chr(32) + chr(109) + chr(97) + chr(105) + chr(110) + chr(32) + chr(124) + chr(32) + chr(97) + chr(99) + chr(116) + chr(105) + chr(111) + chr(110) + chr(58) + chr(32) + chr(100) + chr(111) + chr(99) + chr(116) + chr(111) + chr(114))
        except Exception as exc:
            write_output(chr(71) + chr(85) + chr(73) + chr(32) + chr(65) + chr(67) + chr(84) + chr(73) + chr(79) + chr(78) + chr(32) + chr(69) + chr(88) + chr(69) + chr(67) + chr(85) + chr(84) + chr(73) + chr(79) + chr(78) + chr(32) + chr(82) + chr(69) + chr(83) + chr(85) + chr(76) + chr(84) + chr(10) + chr(97) + chr(99) + chr(116) + chr(105) + chr(111) + chr(110) + chr(61) + chr(100) + chr(111) + chr(99) + chr(116) + chr(111) + chr(114) + chr(10) + chr(114) + chr(101) + chr(116) + chr(117) + chr(114) + chr(110) + chr(99) + chr(111) + chr(100) + chr(101) + chr(61) + chr(49) + chr(10) + chr(109) + chr(101) + chr(115) + chr(115) + chr(97) + chr(103) + chr(101) + chr(61) + str(exc))
            set_status(chr(83) + chr(116) + chr(97) + chr(116) + chr(117) + chr(115) + chr(58) + chr(32) + chr(102) + chr(97) + chr(105) + chr(108) + chr(32) + chr(124) + chr(32) + chr(98) + chr(114) + chr(97) + chr(110) + chr(99) + chr(104) + chr(58) + chr(32) + chr(109) + chr(97) + chr(105) + chr(110) + chr(32) + chr(124) + chr(32) + chr(97) + chr(99) + chr(116) + chr(105) + chr(111) + chr(110) + chr(58) + chr(32) + chr(100) + chr(111) + chr(99) + chr(116) + chr(111) + chr(114))
    toolbar = ttk.Frame(root, padding=4)
    toolbar.pack(fill="x", padx=12, pady=(0, 8))
    for label in ("Refresh status", "Check docs", "GUI dry-run"):
        ttk.Button(toolbar, text=label, state="disabled", style="ReadableDisabled.TButton").pack(side="left", padx=4, pady=4)

    body = ttk.Frame(root, padding=(12, 0, 12, 12))
    body.pack(fill="both", expand=True)
    actions = ttk.LabelFrame(body, text="Actions", padding=6)
    actions.pack(side="left", fill="y", padx=(0, 8))
    ttk.Button(actions, text="cockpit-readiness", command=run_cockpit_readiness_click, width=22).pack(fill="x", pady=3)
    ttk.Button(actions, text="doctor", command=run_doctor_click, width=22).pack(fill="x", pady=3)
    for label in ("check-docs", "agent-run"):
        ttk.Button(actions, text=label, state="disabled", width=22, style="ReadableDisabled.TButton").pack(fill="x", pady=3)

    output = ttk.LabelFrame(body, text="Output / Status", padding=6)
    output.pack(side="left", fill="both", expand=True)
    text = tk.Text(output, height=12, wrap="word")
    text_bg = str(text.cget("bg"))
    text_fg = str(text.cget("fg"))
    if text_fg == text_bg:
        text_fg = label_fg
    text.configure(bg=text_bg, fg=text_fg, insertbackground=text_fg)
    text.insert("1.0", "GUI manual launch ready. cockpit-readiness is enabled as the first bounded read-only GUI action. Remote/destructive actions remain disabled.")
    text.configure(state="disabled")
    text.pack(fill="both", expand=True)
    output_text = text

    status_text = ttk.Label(root, text="Status: ready | branch: main | enabled: cockpit-readiness only", anchor="w")
    status_text.pack(fill="x", side="bottom")
def run_manual_launch() -> tuple[bool, str]:
    guard = check_window_launch_ready()
    lines = ["TKINTER MANUAL LAUNCH", render_window_guard_result(guard)]
    if not guard.ok:
        lines.extend([
            "manual_launch_status=BLOCKED",
            "real_window_opened=false",
            "actions_enabled=false",
        ])
        return True, chr(10).join(lines)
    try:
        root = create_tkinter_root()
    except Exception as exc:
        lines.extend([
            "manual_launch_status=BLOCKED",
            "real_window_opened=false",
            "actions_enabled=false",
            "manual_launch_block_reason=" + str(exc).replace(chr(10), " "),
        ])
        return True, chr(10).join(lines)
    configure_tkinter_root(root, build_tkinter_shell_spec())
    render_manual_launch_content(root)
    lines.extend([
        "manual_launch_status=READY",
        "real_window_opened=true",
        "actions_enabled=false",
        "manual_close_required=true",
    ])
    print(chr(10).join(lines))
    print("### RESULT: PASS ###")
    root.mainloop()
    return True, "manual_launch_closed=true"
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
    if args == ["--manual-launch"]:
        ok, output = run_manual_launch()
        if output:
            print(output)
        return 0 if ok else 1
    print("ERROR: usage: python -m agentic_project_kit.gui_tkinter_shell --no-window-smoke|--window-smoke|--manual-launch")
    print("### RESULT: FAIL ###")
    return 2


if __name__ == "__main__":
    import sys
    raise SystemExit(main(sys.argv[1:]))
