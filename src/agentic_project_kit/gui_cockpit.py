from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
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
from agentic_project_kit.gui_activity_log import ActivityLog
from agentic_project_kit.gui_cockpit_actions import CockpitActionsMixin
from agentic_project_kit.gui_cockpit_common import (
    HEADER_TEXT,
    RECOVERY_ACTION_ID as RECOVERY_ACTION_ID,
    THEME,
    GuiTheme as GuiTheme,
    build_collapsible_group,
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
from agentic_project_kit.gui_panel_state import read_panel_state, write_panel_state
from agentic_project_kit.gui_tk_widgets import maximize_root_window
from agentic_project_kit.gui_viewmodel import build_basic_cockpit_view_model
from agentic_project_kit.workspace_adopt import analyze_workspace_adoption


GUI_GROUP_IDS = (
    "work_cycle",
    "communication",
    "next_step",
    "task_editor",
    "action_table",
    "advanced_tools",
    "file_browser",
    "copy_paste_tools",
    "output",
)
MAIN_CONTENT_GROUP_IDS = (
    "communication",
    "next_step",
    "task_editor",
    "action_table",
    "advanced_tools",
    "file_browser",
    "copy_paste_tools",
    "output",
)


class CockpitGui(CockpitHeaderMixin, CockpitSidebarMixin, CockpitActionsMixin, CockpitTaskMixin):
    def __init__(self, root: Any, project_root: Path | None = None) -> None:
        import tkinter as tk
        from tkinter import ttk

        self.root = root
        self.project_root = (project_root or Path(".")).resolve()
        self.activity_log = ActivityLog()
        self.gui_group_frames: dict[str, Any | None] = dict.fromkeys(GUI_GROUP_IDS)
        self.panel_expanded_state: dict[str, bool] = {}
        self.actions: tuple[GuiActionView, ...] = ()
        self.recovery_action_id = RECOVERY_ACTION_ID
        self._reload_project_view_state()
        self.root.title(self._window_title())
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
        self.start_from_ref_picker: Any | None = None
        self.project_status_var = tk.StringVar(value=self._project_status_text())
        self.release_version_var = tk.StringVar(value="")

        shell = tk.Frame(
            root,
            bg=THEME.color_shell_bg,
            highlightbackground=THEME.color_border,
            highlightthickness=1,
        )
        shell.pack(fill=tk.BOTH, expand=True, padx=14, pady=14)

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
        self.sidebar = sidebar

        separator = ttk.Separator(body, orient=tk.VERTICAL)
        separator.pack(side=tk.LEFT, fill=tk.Y)

        main_scroll_shell = tk.Frame(
            body,
            bg=THEME.color_panel_bg,
            padx=THEME.frame_padding,
            pady=THEME.frame_padding,
        )
        main_scroll_shell.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        main_canvas = tk.Canvas(main_scroll_shell, bg=THEME.color_panel_bg, highlightthickness=0)
        main_scrollbar = ttk.Scrollbar(main_scroll_shell, orient=tk.VERTICAL, command=main_canvas.yview)
        main_canvas.configure(yscrollcommand=main_scrollbar.set)
        main_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        main_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        main_area = tk.Frame(main_canvas, bg=THEME.color_panel_bg)
        main_window = main_canvas.create_window((0, 0), window=main_area, anchor=tk.NW)
        main_area.bind(
            "<Configure>",
            lambda _event: main_canvas.configure(scrollregion=main_canvas.bbox(tk.ALL)),
        )
        main_canvas.bind(
            "<Configure>",
            lambda event: main_canvas.itemconfigure(main_window, width=event.width),
        )
        self.main_area = main_area

        self._build_sidebar(sidebar)
        self._build_main_content()

        self.write_output(format_basic_cockpit_summary(self.basic_view) + "\n")

    def _reload_project_view_state(
        self,
        *,
        communication_mode: str | None = None,
        access_level: str | None = None,
    ) -> None:
        try:
            self.panel_expanded_state = read_panel_state(self.project_root)
        except RuntimeError:
            self.panel_expanded_state = {}
        self.basic_view = build_basic_cockpit_view_model(
            self.project_root,
            communication_mode=communication_mode,
            access_level=access_level,
        )
        self.actions = ordered_action_views(
            build_gui_action_views(access_level=self.basic_view.access_level)
        )
        self.recovery_action_id = recommended_recovery_action_id(self.basic_view)

    def _manifest_status(self) -> str:
        try:
            report = analyze_workspace_adoption(self.project_root)
        except RuntimeError:
            return "invalid"
        return {
            "already_initialized": "initialized",
            "ready_for_workspace_init": "ready-for-init",
            "foreign_agentic_directory": "foreign",
            "invalid_workspace_manifest": "invalid",
        }.get(report.agentic.status, report.agentic.status.replace("_", "-"))

    def _project_branch_label(self) -> str:
        try:
            completed = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=self.project_root,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
        except OSError:
            return "unknown"
        branch = completed.stdout.strip() if completed.returncode == 0 else ""
        return branch or "detached"

    def _project_status_text(self) -> str:
        return f"{self.project_root.name} | {self._project_branch_label()} | {self._manifest_status()}"

    def _window_title(self) -> str:
        return f"{HEADER_TEXT} - {self.project_root.name} - {self._project_branch_label()}"

    def _update_project_chrome(self) -> None:
        self.root.title(self._window_title())
        if hasattr(self, "project_status_var"):
            self.project_status_var.set(self._project_status_text())

    def _is_git_repository(self, path: Path) -> bool:
        try:
            completed = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                cwd=path,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
        except OSError:
            return False
        return completed.returncode == 0

    def open_project(self) -> None:
        from tkinter import filedialog

        selected = filedialog.askdirectory(
            parent=self.root,
            initialdir=str(self.project_root),
            title="Open project",
        )
        if not selected:
            return
        self.switch_project_root(Path(selected))

    def switch_project_root(self, path: Path | str) -> bool:
        candidate = Path(path).expanduser().resolve()
        if not candidate.exists() or not candidate.is_dir():
            self.log_result("Open project", "BLOCKED", f"Folder does not exist: {candidate}")
            return False
        if not self._is_git_repository(candidate):
            self.log_result("Open project", "BLOCKED", f"Selected folder is not a git repository: {candidate}")
            return False
        communication_mode = self.current_communication_mode() if hasattr(self, "mode_var") else None
        access_level = self.basic_view.access_level
        self.project_root = candidate
        self._reload_project_view_state(communication_mode=communication_mode, access_level=access_level)
        self._update_project_chrome()
        if hasattr(self, "start_from_ref_value"):
            self.start_from_ref_value.set("latest main")
        if self.start_from_ref_picker is not None:
            self.start_from_ref_picker.configure(values=self._start_from_ref_options())
        if hasattr(self, "sidebar"):
            self._rebuild_sidebar()
        if hasattr(self, "main_area"):
            self._rebuild_main_content()
        status = self._manifest_status()
        hint = " Foreign .agentic directory detected; workspace init is intentionally not run." if status == "foreign" else ""
        self.log_result("Open project", "PASS", f"Project switched to {candidate}\nStatus: {status}.{hint}")
        return True

    def _advanced_access_visible(self) -> bool:
        return self.basic_view.access_level in {"advanced", "maintainer"}

    def _register_group_frame(self, group_id: str, frame: Any) -> Any:
        if group_id not in self.gui_group_frames:
            raise KeyError(f"unknown GUI group id: {group_id}")
        self.gui_group_frames[group_id] = frame
        setattr(self, f"{group_id}_frame", frame)
        return frame

    def _reset_main_group_frames(self) -> None:
        for group_id in MAIN_CONTENT_GROUP_IDS:
            self.gui_group_frames[group_id] = None
            setattr(self, f"{group_id}_frame", None)
            setattr(self, f"{group_id}_body", None)
            setattr(self, f"{group_id}_expanded", False)

    def _panel_group_expanded(self, group_id: str) -> bool:
        if group_id in self.panel_expanded_state:
            return bool(self.panel_expanded_state[group_id])
        return group_id in set(self.basic_view.default_expanded_groups)

    def _set_panel_group_expanded(self, group_id: str, expanded: bool) -> None:
        self.panel_expanded_state[group_id] = bool(expanded)
        write_panel_state(self.project_root, self.panel_expanded_state)

    def _toggle_panel_group(self, group_id: str) -> None:
        self._set_panel_group_expanded(group_id, not self._panel_group_expanded(group_id))
        self._rebuild_main_content()

    def _build_collapsible_group(
        self,
        parent: Any,
        *,
        group_id: str,
        title: str,
        subtitle: str = "",
    ) -> Any:
        group = build_collapsible_group(
            parent,
            group_id=group_id,
            title=title,
            subtitle=subtitle,
            expanded=self._panel_group_expanded(group_id),
            on_toggle=self._toggle_panel_group,
        )
        self._register_group_frame(group_id, group.frame)
        setattr(self, f"{group_id}_body", group.body)
        setattr(self, f"{group_id}_expanded", group.expanded)
        return group

    def _build_main_content(self) -> None:
        self._reset_main_group_frames()
        self._build_primary_status_row(self.main_area)
        if self._advanced_access_visible():
            self._build_action_cards(self.main_area)
            self._build_advanced_tools(self.main_area)
            self._build_file_browser(self.main_area)
        self._build_task_editor(self.main_area)
        self._build_copy_paste_tools(self.main_area)
        self._build_output_panel(self.main_area)

    def _build_primary_status_row(self, parent: Any) -> None:
        import tkinter as tk

        row = tk.Frame(parent, bg=THEME.color_panel_bg)
        self.primary_status_row = row
        row.pack(fill=tk.X, pady=(0, 10))
        row.columnconfigure(0, weight=1)
        row.columnconfigure(1, weight=1)

        communication_column = tk.Frame(row, bg=THEME.color_panel_bg)
        communication_column._primary_status_column = "communication"  # type: ignore[attr-defined]
        communication_column.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        next_step_column = tk.Frame(row, bg=THEME.color_panel_bg)
        next_step_column._primary_status_column = "next_step"  # type: ignore[attr-defined]
        next_step_column.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        self._build_communication_panel(communication_column)
        self._build_next_step_panel(next_step_column)

    def _rebuild_main_content(self) -> None:
        for child in self.main_area.winfo_children():
            child.destroy()
        self._build_main_content()

    def _rebuild_sidebar(self) -> None:
        for child in self.sidebar.winfo_children():
            child.destroy()
        self._build_sidebar(self.sidebar)


def main(argv: list[str] | None = None) -> None:
    import tkinter as tk

    parser = argparse.ArgumentParser(prog="agentic-kit-gui")
    parser.add_argument("--root", default=".", help="Project root to open in the cockpit.")
    args = parser.parse_args(argv)
    root = tk.Tk()
    CockpitGui(root, project_root=Path(args.root))
    root.mainloop()
