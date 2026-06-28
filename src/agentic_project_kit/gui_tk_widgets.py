from __future__ import annotations

from typing import Any

from agentic_project_kit.access_levels import ACCESS_LEVEL_ORDER
from agentic_project_kit.gui_viewmodel import CommunicationModeViewModel


TRAFFIC_LIGHT_FILL_BY_COLOR = {
    "green": "#1f883d",
    "yellow": "#bf8700",
    "red": "#cf222e",
    "gray": "#6e7781",
}

TRAFFIC_LIGHT_LABEL_BY_STATE = {
    "READY": "READY (green)",
    "WAIT_FOR_D2": "WAIT_FOR_D2 (yellow)",
    "WAIT": "WAIT (yellow)",
    "BLOCKED": "BLOCKED (red)",
    "FAILED": "FAILED (red)",
}

COMMUNICATION_MODE_EXPLANATIONS = {
    "file_transfer": (
        "Normal mode. Write the task to the repo-backed transfer task, send g/go in chat, "
        "then read the result. Minimizes copy-and-paste."
    ),
    "remote": (
        "PR/CI/GitHub focused mode. Use safe read-only checks and bounded wrappers; "
        "do not bypass governance."
    ),
    "copy_paste": (
        "Recovery fallback only for terminal loss or missing remote access. "
        "Not the normal operating mode."
    ),
}


def traffic_light_fill(color: str) -> str:
    return TRAFFIC_LIGHT_FILL_BY_COLOR.get(color.lower(), TRAFFIC_LIGHT_FILL_BY_COLOR["gray"])


def traffic_light_state_label(state: str) -> str:
    normalized = state.strip().upper().replace("-", "_")
    return TRAFFIC_LIGHT_LABEL_BY_STATE.get(normalized, f"{normalized or 'UNKNOWN'} (gray)")


def communication_mode_explanation(mode: str) -> str:
    return COMMUNICATION_MODE_EXPLANATIONS.get(mode, COMMUNICATION_MODE_EXPLANATIONS["file_transfer"])


def communication_mode_option_label(mode: CommunicationModeViewModel) -> str:
    return f"{mode.label}: {mode.role}"


def communication_mode_option_values(
    modes: tuple[CommunicationModeViewModel, ...],
) -> tuple[str, ...]:
    return tuple(communication_mode_option_label(mode) for mode in modes)


def selected_communication_mode_option(
    modes: tuple[CommunicationModeViewModel, ...],
) -> str:
    selected = next((mode for mode in modes if mode.selected), modes[0])
    return communication_mode_option_label(selected)


def access_level_option_values() -> tuple[str, ...]:
    return tuple(ACCESS_LEVEL_ORDER)


class TkTooltip:
    def __init__(self, widget: Any, text: str) -> None:
        self.widget = widget
        self.text = text
        self.window: Any | None = None
        if hasattr(widget, "bind"):
            widget.bind("<Enter>", self.show)
            widget.bind("<Leave>", self.hide)

    def show(self, _event: object | None = None) -> None:
        if self.window is not None or not self.text:
            return
        import tkinter as tk

        x = self.widget.winfo_rootx() + 18
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 8
        self.window = tk.Toplevel(self.widget)
        self.window.wm_overrideredirect(True)
        self.window.wm_geometry(f"+{x}+{y}")
        label = tk.Label(
            self.window,
            text=self.text,
            justify="left",
            background="#ffffe0",
            relief="solid",
            borderwidth=1,
            padx=6,
            pady=3,
        )
        label.pack()

    def hide(self, _event: object | None = None) -> None:
        if self.window is None:
            return
        self.window.destroy()
        self.window = None

    def update_text(self, text: str) -> None:
        self.text = text


def attach_tooltip(widget: Any, text: str) -> Any:
    existing = getattr(widget, "_agentic_tooltip", None)
    if isinstance(existing, TkTooltip):
        existing.hide()
        existing.update_text(text)
        widget._agentic_tooltip_text = text
        return widget
    if existing is not None and hasattr(existing, "hide"):
        existing.hide()
    widget._agentic_tooltip_text = text
    widget._agentic_tooltip = TkTooltip(widget, text)
    return widget
