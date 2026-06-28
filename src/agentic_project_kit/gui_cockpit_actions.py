from __future__ import annotations

from typing import Any

from agentic_project_kit.cockpit import READ_ONLY, run_cockpit_action
from agentic_project_kit.gui_action_views import (
    GuiActionGroupView,
    GuiActionView,
    explain_safety,
    format_action_details,
    format_action_result,
    grouped_action_views,
)
from agentic_project_kit.gui_cockpit_common import THEME, action_tree_tag_colors
from agentic_project_kit.gui_tk_widgets import attach_tooltip, traffic_light_fill
from agentic_project_kit.gui_tkinter_shell import run_basic_cockpit_button


class CockpitActionsMixin:
    def _build_action_cards(self, parent: Any) -> None:
        import tkinter as tk
        from tkinter import ttk

        self._section_heading(parent, "Actions")
        action_scroll_shell = tk.Frame(parent, bg=THEME.color_panel_bg)
        action_scroll_shell.pack(fill=tk.X)
        self.action_card_canvas = tk.Canvas(
            action_scroll_shell,
            bg=THEME.color_panel_bg,
            height=THEME.action_rows_visible * THEME.action_card_height,
            highlightthickness=0,
        )
        self.action_card_scrollbar = ttk.Scrollbar(
            action_scroll_shell,
            orient=tk.VERTICAL,
            command=self.action_card_canvas.yview,
        )
        self.action_card_canvas.configure(yscrollcommand=self.action_card_scrollbar.set)
        self.action_card_container = tk.Frame(self.action_card_canvas, bg=THEME.color_panel_bg)
        self.action_card_window = self.action_card_canvas.create_window(
            (0, 0),
            window=self.action_card_container,
            anchor=tk.NW,
        )
        self.action_card_container.bind(
            "<Configure>",
            lambda _event: self.action_card_canvas.configure(
                scrollregion=self.action_card_canvas.bbox(tk.ALL)
            ),
        )
        self.action_card_canvas.bind(
            "<Configure>",
            lambda event: self.action_card_canvas.itemconfigure(
                self.action_card_window,
                width=event.width,
            ),
        )
        self.action_card_canvas.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.action_card_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.action_card_widgets: dict[str, Any] = {}
        self.populate_action_tree()

        button_row = tk.Frame(parent, bg=THEME.color_panel_bg)
        button_row.pack(fill=tk.X, pady=(10, 15))
        inspect_button = ttk.Button(button_row, text="Inspect", command=self.inspect_selected)
        attach_tooltip(inspect_button, "Show metadata, command, and safety details for the selected action.")
        inspect_button.pack(side=tk.LEFT, padx=(0, 9))
        run_button = ttk.Button(button_row, text="Run read-only", command=self.run_selected_read_only)
        attach_tooltip(run_button, "Run only selected read-only cockpit actions through the shared cockpit layer.")
        run_button.pack(side=tk.LEFT, padx=(0, 9))


    def selected_action_id(self) -> str | None:
        return self.selected_action_id_value

    def action_view_by_id(self, action_id: str) -> GuiActionView | None:
        for action in self.actions:
            if action.action_id == action_id:
                return action
        return None

    def populate_action_tree(self) -> None:
        for child in self.action_card_container.winfo_children():
            child.destroy()
        self.action_card_widgets = {}
        action_groups = grouped_action_views(self.actions)
        for group in action_groups:
            self._create_action_group_heading(group)
            for action in group.actions:
                self._create_action_card(action)
        visible_ids = {action.action_id for group in action_groups for action in group.actions}
        if self.selected_action_id_value not in visible_ids:
            first_group = action_groups[0] if action_groups else None
            self.selected_action_id_value = first_group.actions[0].action_id if first_group and first_group.actions else None
        self._refresh_action_card_selection()

    def _create_action_group_heading(self, group: GuiActionGroupView) -> None:
        import tkinter as tk

        frame = tk.Frame(self.action_card_container, bg=THEME.color_panel_bg)
        frame.pack(fill=tk.X, pady=(7 if self.action_card_widgets else 0, 4))
        tk.Label(
            frame,
            text=group.label.upper(),
            bg=THEME.color_panel_bg,
            fg=THEME.color_muted_text,
            font=THEME.section_font,
            anchor=tk.W,
        ).pack(side=tk.LEFT)
        tk.Label(
            frame,
            text=group.description,
            bg=THEME.color_panel_bg,
            fg=THEME.color_muted_text,
            font=THEME.small_font,
            anchor=tk.E,
        ).pack(side=tk.RIGHT)

    def _create_action_card(self, action: GuiActionView) -> None:
        import tkinter as tk

        bg = action_tree_tag_colors().get(action.safety, "#f4f4f4")
        card = tk.Frame(
            self.action_card_container,
            bg=bg,
            highlightbackground=bg,
            highlightthickness=2,
            padx=7,
            pady=5,
        )
        card.pack(fill=tk.X, pady=(0, 4))
        dot = tk.Canvas(card, width=12, height=12, bg=bg, highlightthickness=0)
        dot.create_oval(2, 2, 10, 10, fill=traffic_light_fill("green" if action.safety == READ_ONLY else "yellow"), outline="")
        dot.pack(side=tk.LEFT, padx=(0, 8))
        label = tk.Label(
            card,
            text=action.label,
            bg=bg,
            fg="#0b2f27" if action.safety == READ_ONLY else "#3d2200",
            font=THEME.action_font,
            anchor=tk.W,
        )
        label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        safety = tk.Label(
            card,
            text=action.safety.replace("_", "-"),
            bg=bg,
            fg="#006b50" if action.safety == READ_ONLY else "#6b3d00",
            font=THEME.small_font,
        )
        safety.pack(side=tk.RIGHT)
        tooltip = f"{action.short_description}. {explain_safety(action.safety)}"
        for widget in (card, dot, label, safety):
            widget.bind("<Button-1>", lambda _event, action_id=action.action_id: self._select_action(action_id))
        attach_tooltip(card, tooltip)
        self.action_card_widgets[action.action_id] = card

    def _select_action(self, action_id: str) -> None:
        self.selected_action_id_value = action_id
        self._refresh_action_card_selection()

    def _refresh_action_card_selection(self) -> None:
        for action_id, card in self.action_card_widgets.items():
            selected = action_id == self.selected_action_id_value
            bg = card.cget("bg")
            card.configure(
                highlightbackground="#1f5b9d" if selected else bg,
                highlightthickness=2 if selected else 1,
            )


    def load_recovery_action(self) -> None:
        if self.recovery_action_id is None:
            return
        self._select_action(self.recovery_action_id)
        action = self.action_view_by_id(self.recovery_action_id)
        label = action.label if action is not None else self.recovery_action_id
        self.write_output(f"\nRecovery action loaded: {label}. Inspect or run read-only manually.\n")

    def inspect_selected(self) -> None:
        action_id = self.selected_action_id()
        if action_id is None:
            self.write_output("No cockpit action selected.\n")
            return
        action = self.action_view_by_id(action_id)
        if action is None:
            self.write_output(f"Unknown cockpit action: {action_id}\n")
            return
        [
            "",
            f"action_id={action.action_id}",
            f"label={action.label}",
            f"category={action.category}",
            f"safety={action.safety}",
            f"can_run_by_default={str(action.can_run_by_default).lower()}",
            f"command={' '.join(action.command)}",
            f"description={action.description}",
            "",
        ]
        self.write_output("\n\n" + format_action_details(action) + "\n")

    def run_basic_action(self, command_id: str) -> None:
        self.write_output("\n" + run_basic_cockpit_button(command_id, project_root=self.project_root) + "\n")

    def run_selected_read_only(self) -> None:
        action_id = self.selected_action_id()
        if action_id is None:
            self.write_output("No cockpit action selected.\n")
            return
        action = self.action_view_by_id(action_id)
        if action is not None and action.safety != READ_ONLY:
            self.write_output("\n" + format_action_details(action) + "\n")
            return
        result = run_cockpit_action(action_id, self.project_root, allow_bounded=False)
        self.write_output("\n" + format_action_result(result) + "\n")
