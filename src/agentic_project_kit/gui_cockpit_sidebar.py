from __future__ import annotations

from typing import Any

from agentic_project_kit.access_levels import normalize_access_level
from agentic_project_kit.gui_action_views import build_gui_action_views, ordered_action_views
from agentic_project_kit.gui_cockpit_common import THEME
from agentic_project_kit.gui_tk_widgets import (
    access_level_option_values,
    attach_tooltip,
    communication_mode_example,
    communication_mode_explanation,
    communication_mode_option_values,
    selected_communication_mode_option,
    traffic_light_fill,
    traffic_light_state_label,
)
from agentic_project_kit.gui_viewmodel import build_basic_cockpit_view_model


class CockpitSidebarMixin:
    def _section_heading(self, parent: Any, text: str) -> None:
        import tkinter as tk

        tk.Label(
            parent,
            text=text.upper(),
            bg=THEME.color_panel_bg,
            fg=THEME.color_muted_text,
            font=THEME.section_font,
            anchor=tk.W,
        ).pack(fill=tk.X, pady=(0, 7))

    def _detail_row(self, parent: Any, label: str, value: str, *, value_color: str = "#1f1f1f") -> None:
        import tkinter as tk

        row = tk.Frame(parent, bg=THEME.color_panel_bg)
        row.pack(fill=tk.X, pady=2)
        label_widget = tk.Label(row, text=label, bg=THEME.color_panel_bg, fg="#4a4a4a", font=THEME.body_font)
        label_widget.pack(side=tk.LEFT)
        value_widget = tk.Label(row, text=value, bg=THEME.color_panel_bg, fg=value_color, font=THEME.body_font)
        value_widget.pack(side=tk.RIGHT)
        if label == "d2 pending":
            tooltip = (
                "d2 means a communication-rule refresh is pending. The assistant must read "
                "the remote rule capsule and return RULE_REFRESH_ACK before mutation."
            )
            attach_tooltip(label_widget, tooltip)
            attach_tooltip(value_widget, tooltip)

    def _build_sidebar(self, sidebar: Any) -> None:
        import tkinter as tk
        from tkinter import ttk

        ready_card = tk.Frame(
            sidebar,
            bg=THEME.color_ready_bg if self.basic_view.traffic_light_color == "green" else "#fff8dc",
            highlightbackground=THEME.color_ready_border,
            highlightthickness=1,
            padx=12,
            pady=12,
        )
        ready_card.pack(fill=tk.X, pady=(0, 18))

        ready_row = tk.Frame(ready_card, bg=ready_card["bg"])
        ready_row.pack(fill=tk.X)
        light = tk.Canvas(ready_row, width=17, height=17, bg=ready_card["bg"], highlightthickness=0)
        light.create_oval(
            3,
            3,
            14,
            14,
            fill=traffic_light_fill(self.basic_view.traffic_light_color),
            outline=traffic_light_fill(self.basic_view.traffic_light_color),
        )
        light.pack(side=tk.LEFT, padx=(0, 9))
        tk.Label(
            ready_row,
            text=traffic_light_state_label(self.basic_view.traffic_light_state).split(" ")[0],
            bg=ready_card["bg"],
            fg="#08775f",
            font=("TkDefaultFont", 13, "bold"),
        ).pack(side=tk.LEFT)
        tk.Label(
            ready_card,
            text=self.basic_view.reason,
            bg=ready_card["bg"],
            fg="#006b50",
            font=THEME.body_font,
            anchor=tk.W,
            justify=tk.LEFT,
            wraplength=255,
        ).pack(fill=tk.X, pady=(12, 0))

        self._section_heading(sidebar, "Status Detail")
        self._detail_row(sidebar, "Worktree", "dirty" if "dirty" in self.basic_view.reason.lower() else "clean", value_color="#006b00")
        self._detail_row(sidebar, "Mutation", "allowed" if self.basic_view.mutation_allowed else "guarded")
        self._detail_row(sidebar, "d2 pending", "yes" if self.basic_view.required_next_reply == "d2" else "no")
        version = self._package_version()
        self._detail_row(sidebar, "Version", version)

        tk.Frame(sidebar, height=19, bg=THEME.color_panel_bg).pack(fill=tk.X)
        self._section_heading(sidebar, "Transfer Mode")
        self.mode_var = tk.StringVar(
            value=selected_communication_mode_option(self.basic_view.communication_modes)
        )
        mode_select = ttk.Combobox(
            sidebar,
            textvariable=self.mode_var,
            values=communication_mode_option_values(self.basic_view.communication_modes),
            state="readonly",
            width=24,
            font=THEME.body_font,
        )
        mode_select.pack(fill=tk.X)
        attach_tooltip(
            mode_select,
            "Select the communication mode. File Transfer is the standard path; Copy-and-Paste is a recovery fallback.",
        )
        self.mode_explanation_var = tk.StringVar(
            value=communication_mode_explanation(self.basic_view.communication_mode)
        )
        tk.Label(
            sidebar,
            textvariable=self.mode_explanation_var,
            anchor=tk.W,
            justify=tk.LEFT,
            bg=THEME.color_panel_bg,
            fg=THEME.color_muted_text,
            font=THEME.small_font,
            wraplength=255,
        ).pack(fill=tk.X, pady=(7, 0))
        self.mode_example_var = tk.StringVar(
            value=communication_mode_example(self.basic_view.communication_mode)
        )
        tk.Label(
            sidebar,
            textvariable=self.mode_example_var,
            anchor=tk.W,
            justify=tk.LEFT,
            bg=THEME.color_panel_bg,
            fg=THEME.color_muted_text,
            font=THEME.small_font,
            wraplength=255,
        ).pack(fill=tk.X, pady=(5, 0))
        mode_select.bind("<<ComboboxSelected>>", self.update_mode_explanation)

        tk.Frame(sidebar, height=18, bg=THEME.color_panel_bg).pack(fill=tk.X)
        self._section_heading(sidebar, "Access Level")
        self.access_level_var = tk.StringVar(value=self.basic_view.access_level)
        access_select = ttk.Combobox(
            sidebar,
            textvariable=self.access_level_var,
            values=access_level_option_values(),
            state="readonly",
            width=24,
            font=THEME.body_font,
        )
        access_select.pack(fill=tk.X)
        attach_tooltip(
            access_select,
            "Basic shows routine actions. Advanced adds release and rules. Maintainer adds deep audits. Access level does not grant permission.",
        )
        self.access_level_explanation_var = tk.StringVar(
            value=self.basic_view.access_level_explanation
        )
        tk.Label(
            sidebar,
            textvariable=self.access_level_explanation_var,
            anchor=tk.W,
            justify=tk.LEFT,
            bg=THEME.color_panel_bg,
            fg=THEME.color_muted_text,
            font=THEME.small_font,
            wraplength=255,
        ).pack(fill=tk.X, pady=(7, 0))
        access_select.bind("<<ComboboxSelected>>", self.update_access_level)

        tk.Frame(sidebar, height=10, bg=THEME.color_panel_bg).pack(fill=tk.X, expand=True)

    def _build_recommended_card(self, sidebar: Any) -> None:
        import tkinter as tk

        action = self.basic_view.recommended_action
        card = tk.Frame(
            sidebar,
            bg=THEME.color_recommended_bg,
            highlightbackground="#7eb1f1",
            highlightthickness=1,
            padx=11,
            pady=10,
        )
        card.pack(fill=tk.X, pady=(0, 18))
        tk.Label(
            card,
            text="RECOMMENDED NEXT",
            bg=THEME.color_recommended_bg,
            fg="#174ea6",
            font=THEME.section_font,
            anchor=tk.W,
        ).pack(fill=tk.X, pady=(0, 6))
        recommended = tk.Button(
            card,
            text=f"□  {action.label}",
            font=THEME.recommended_font,
            bg="#c5ddfb",
            fg="#174ea6",
            activebackground="#c5ddfb",
            relief=tk.GROOVE,
            bd=1,
            command=self.run_recommended_action,
            anchor=tk.W,
            padx=12,
            pady=8,
        )
        attach_tooltip(recommended, action.tooltip)
        recommended.pack(fill=tk.X)
        tk.Label(
            card,
            text=action.description,
            bg=THEME.color_recommended_bg,
            fg="#174ea6",
            font=THEME.small_font,
            anchor=tk.W,
            justify=tk.LEFT,
            wraplength=255,
        ).pack(fill=tk.X, pady=(7, 0))
        if self.basic_view.recovery_hint:
            tk.Label(
                card,
                text=self.basic_view.recovery_hint,
                bg=THEME.color_recommended_bg,
                fg="#5f2f00" if self.basic_view.traffic_light_color == "yellow" else "#8a1f11",
                font=THEME.small_font,
                anchor=tk.W,
                justify=tk.LEFT,
                wraplength=255,
            ).pack(fill=tk.X, pady=(5, 0))

    def _package_version(self) -> str:
        try:
            from agentic_project_kit import __version__
        except ImportError:
            return "unknown"
        return __version__

    def _recommended_button_label(self) -> str:
        if self.recovery_action_id:
            action = self.action_view_by_id(self.recovery_action_id)
            return action.label if action is not None else self.recovery_action_id
        return "Run next work order"


    def run_recommended_action(self) -> None:
        action = self.basic_view.recommended_action
        if action.kind == "run_button" and action.command_id:
            self.run_basic_action(action.command_id)
            return
        if action.kind == "select_action" and action.cockpit_action_id:
            self._select_action(action.cockpit_action_id)
            label = action.label
            self.write_output(f"\nRecommended action loaded: {label}. Inspect or run read-only manually.\n")
            return
        message = self.basic_view.recovery_hint or action.description
        self.write_output(f"\nRecommended next: {message}\n")

    def update_mode_explanation(self, _event: object | None = None) -> None:
        selected = self.current_communication_mode()
        self.mode_explanation_var.set(communication_mode_explanation(selected))
        self.mode_example_var.set(communication_mode_example(selected))
        self.refresh_task_editor_buttons()

    def current_communication_mode(self) -> str:
        option = self.mode_var.get()
        return next(
            (
                mode.mode_id
                for mode in self.basic_view.communication_modes
                if f"{mode.label}: {mode.role}" == option
            ),
            self.basic_view.communication_mode,
        )

    def update_access_level(self, _event: object | None = None) -> None:
        selected = normalize_access_level(self.access_level_var.get())
        # Access level is a visibility convenience only; safety remains the execution boundary.
        self.basic_view = build_basic_cockpit_view_model(
            self.project_root,
            communication_mode=self.basic_view.communication_mode,
            access_level=selected,
        )
        self.access_level_var.set(self.basic_view.access_level)
        self.access_level_explanation_var.set(self.basic_view.access_level_explanation)
        self.actions = ordered_action_views(build_gui_action_views(access_level=selected))
        self.populate_action_tree()
        self.write_output(f"\nAccess level changed to {self.basic_view.access_level}; action list rebuilt.\n")
