from __future__ import annotations

from pathlib import Path
from typing import Any

from agentic_project_kit.gui_action_views import (
    GuiActionGroupView as GuiActionGroupView,
    GuiActionView as GuiActionView,
    build_gui_action_views as build_gui_action_views,
    explain_safety as explain_safety,
    format_action_details as format_action_details,
    format_action_result as format_action_result,
    grouped_action_views as grouped_action_views,
    ordered_action_views as ordered_action_views,
)
from agentic_project_kit.gui_cockpit_actions import CockpitActionsMixin
from agentic_project_kit.gui_cockpit_common import (
    HEADER_TEXT,
    RECOVERY_ACTION_ID as RECOVERY_ACTION_ID,
    THEME,
    GuiTheme as GuiTheme,
    action_tree_columns as action_tree_columns,
    action_tree_tag_colors as action_tree_tag_colors,
    action_tree_tag_for_safety as action_tree_tag_for_safety,
    action_tree_visible_rows as action_tree_visible_rows,
    format_basic_cockpit_summary,
    format_recommended_action as format_recommended_action,
    format_state_details as format_state_details,
    recommended_recovery_action_id,
)
from agentic_project_kit.gui_cockpit_header import CockpitHeaderMixin
from agentic_project_kit.gui_cockpit_sidebar import CockpitSidebarMixin
from agentic_project_kit.gui_cockpit_task import CockpitTaskMixin
from agentic_project_kit.gui_tk_widgets import maximize_root_window
from agentic_project_kit.gui_viewmodel import build_basic_cockpit_view_model


class CockpitGui(CockpitHeaderMixin, CockpitSidebarMixin, CockpitActionsMixin, CockpitTaskMixin):
    def __init__(self, root: Any, project_root: Path | None = None) -> None:
        import tkinter as tk
        from tkinter import ttk

        self.root = root
        self.project_root = (project_root or Path(".")).resolve()
        self.basic_view = build_basic_cockpit_view_model(self.project_root)
        self.actions = ordered_action_views(
            build_gui_action_views(access_level=self.basic_view.access_level)
        )
        self.recovery_action_id = recommended_recovery_action_id(self.basic_view)
        self.root.title(HEADER_TEXT)
        maximize_root_window(self.root, fallback_geometry=THEME.window_geometry)
        if hasattr(self.root, "minsize"):
            self.root.minsize(1040, 680)
        self.selected_action_id_value: str | None = None
        self.work_cycle_last_check_passed = False
        self.work_cycle_last_check_signature = ""
        self.pending_finish_preview: dict[str, object] | None = None
        self.pending_discard_preview: dict[str, object] | None = None
        self.pending_release_preview: dict[str, object] | None = None
        self.work_finish_confirm_button: Any | None = None
        self.work_discard_confirm_button: Any | None = None
        self.release_confirm_button: Any | None = None
        self.start_from_ref_value = tk.StringVar(value="latest main")
        self.release_version_var = tk.StringVar(value="")

        shell = tk.Frame(
            root,
            bg=THEME.color_shell_bg,
            highlightbackground=THEME.color_border,
            highlightthickness=1,
        )
        shell.pack(fill=tk.BOTH, expand=True, padx=14, pady=14)

        self._build_header(shell)
        self._build_work_cycle_bar(shell)

        body = tk.Frame(shell, bg=THEME.color_panel_bg)
        body.pack(fill=tk.BOTH, expand=True)

        sidebar = tk.Frame(
            body,
            bg=THEME.color_panel_bg,
            width=THEME.sidebar_width,
            padx=THEME.frame_padding,
            pady=THEME.frame_padding,
        )
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)

        separator = ttk.Separator(body, orient=tk.VERTICAL)
        separator.pack(side=tk.LEFT, fill=tk.Y)

        main_area = tk.Frame(
            body,
            bg=THEME.color_panel_bg,
            padx=THEME.frame_padding,
            pady=THEME.frame_padding,
        )
        main_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._build_sidebar(sidebar)
        self._build_next_step_panel(main_area)
        self._build_action_cards(main_area)
        self._build_task_editor(main_area)
        self._build_output_panel(main_area)

        self.write_output(format_basic_cockpit_summary(self.basic_view) + "\n")


def main() -> None:
    import tkinter as tk

    root = tk.Tk()
    CockpitGui(root)
    root.mainloop()
