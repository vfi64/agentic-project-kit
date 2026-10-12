"""Guided work controls; all actions remain existing Kit handlers."""

from __future__ import annotations

from typing import Any

from agentic_project_kit.gui_cockpit_common import THEME
from agentic_project_kit.gui_tk_widgets import attach_tooltip
from agentic_project_kit.work_cycle import build_work_cycle_views


def build_guided_workbar(gui: Any, parent: Any) -> None:
    import tkinter as tk
    from tkinter import ttk

    frame = tk.Frame(parent, bg=THEME.color_panel_bg, padx=12, pady=10)
    frame.pack(fill=tk.X)
    gui._register_group_frame("work_cycle", frame)
    tk.Label(
        frame, text="WORK CYCLE", bg=THEME.color_panel_bg, font=THEME.section_font,
    ).pack(anchor=tk.W)
    row = tk.Frame(frame, bg=THEME.color_panel_bg)
    row.pack(fill=tk.X, pady=6)
    phase = gui.current_work_phase()
    for index, view in enumerate(build_work_cycle_views(phase)):
        button = ttk.Button(
            row, text=view.label, command=gui._work_cycle_command_for(view.phase_id),
            state=tk.NORMAL if view.is_available else tk.DISABLED,
        )
        # Grid permits a second row on smaller windows without clipping controls.
        button.grid(row=index // 3, column=index % 3, sticky="ew", padx=4, pady=4)
        row.columnconfigure(index % 3, weight=1)
        attach_tooltip(button, view.tooltip)

    options = tk.Frame(frame, bg=THEME.color_panel_bg)
    options.pack(fill=tk.X, pady=4)
    tk.Label(options, text="Start from", bg=THEME.color_panel_bg).pack(side=tk.LEFT)
    gui.start_from_ref_picker = ttk.Combobox(
        options, textvariable=gui.start_from_ref_value,
        values=gui._start_from_ref_options(), state="readonly", width=24,
    )
    gui.start_from_ref_picker.pack(side=tk.LEFT, padx=8)
    gui.work_finish_confirm_button = ttk.Button(
        options, text="Confirm publish", command=gui.confirm_work_finish,
        state=tk.NORMAL if gui.pending_finish_preview else tk.DISABLED,
    )
    gui.work_finish_confirm_button.pack(side=tk.RIGHT)
    attach_tooltip(
        gui.work_finish_confirm_button,
        "Execute the existing Kit work-finish workflow only after a passing preview and unchanged state.",
    )
    ttk.Button(options, text="Chat handoff", command=gui.show_chat_handoff).pack(side=tk.RIGHT, padx=8)
