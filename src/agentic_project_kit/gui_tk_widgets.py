from __future__ import annotations

from typing import Any

from agentic_project_kit.gui_viewmodel import CommunicationModeViewModel


TRAFFIC_LIGHT_FILL_BY_COLOR = {
    "green": "#1f883d",
    "yellow": "#bf8700",
    "red": "#cf222e",
    "gray": "#6e7781",
}


def traffic_light_fill(color: str) -> str:
    return TRAFFIC_LIGHT_FILL_BY_COLOR.get(color.lower(), TRAFFIC_LIGHT_FILL_BY_COLOR["gray"])


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


def attach_tooltip(widget: Any, text: str) -> Any:
    widget._agentic_tooltip_text = text
    widget._agentic_tooltip = TkTooltip(widget, text)
    return widget
