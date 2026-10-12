"""Optional tabbed Kit frontend; no private controller or browser runtime required."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from agentic_project_kit.gui_cockpit import CockpitGui
from agentic_project_kit.gui_cockpit_common import THEME, recommended_recovery_action_id
from agentic_project_kit.gui_guided_workbar import build_guided_workbar
from agentic_project_kit.gui_guided_theme import apply_guided_theme
from agentic_project_kit.gui_service_bridge import TkServiceBridge
from agentic_project_kit.gui_task_editor import TaskEditorState
from agentic_project_kit.gui_viewmodel import build_basic_cockpit_view_model


GUIDED_TABS = (
    ("standard", "Standard tasks"),
    ("work", "Work"),
    ("tools", "Kit tools"),
    ("system", "System"),
)


class GuidedKitGui(CockpitGui):
    """Reuse all action guards; change only composition and execution presentation."""

    task_editor_height = 8

    def __init__(self, root: Any, project_root: Path | None = None, **kwargs: Any) -> None:
        apply_guided_theme(root)
        self.service_bridge = TkServiceBridge(root)
        self._task_draft = ""
        self._task_draft_state = TaskEditorState.IDLE
        super().__init__(root, project_root, **kwargs)
        self.root.minsize(960, 680)
        self.root.report_callback_exception = self._report_callback_exception

    def _report_callback_exception(self, error_type: type[BaseException], error: BaseException, _traceback: Any) -> None:
        self.log_result("GUI action", "ERROR", f"{error_type.__name__}: {error}")

    def _window_title(self) -> str:
        return f"agentic-project-kit · Guided GUI (experimental) · {self.project_root.name}"

    def _build_shell(self) -> None:
        import tkinter as tk
        from tkinter import ttk

        shell = tk.Frame(self.root, bg=THEME.color_panel_bg)
        shell.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)
        header = tk.Frame(shell, bg=THEME.color_panel_bg)
        header.pack(fill=tk.X, pady=(0, 8))
        tk.Label(
            header, text="agentic-project-kit · Guided GUI", bg=THEME.color_panel_bg,
            font=THEME.title_font,
        ).pack(side=tk.LEFT)
        ttk.Button(header, text="Open project…", command=self.open_project).pack(side=tk.RIGHT)
        ttk.Button(header, text="Refresh status", command=self.refresh_guided_status).pack(side=tk.RIGHT, padx=8)
        tk.Label(
            shell, textvariable=self.project_status_var, bg=THEME.color_panel_bg,
            font=THEME.small_font, anchor=tk.W,
        ).pack(fill=tk.X, pady=(0, 8))

        panes = ttk.Panedwindow(shell, orient=tk.VERTICAL)
        panes.pack(fill=tk.BOTH, expand=True)
        self.notebook = ttk.Notebook(panes)
        panes.add(self.notebook, weight=3)
        self.tabs: dict[str, Any] = {}
        self.tab_canvases: dict[str, Any] = {}
        self.tab_viewports: dict[str, Any] = {}
        for tab_id, label in GUIDED_TABS:
            viewport = tk.Frame(self.notebook, bg=THEME.color_panel_bg)
            self.notebook.add(viewport, text=label)
            self.tab_viewports[tab_id] = viewport
            self.tabs[tab_id] = self._scroll_content(viewport, tab_id)
        # Base project/visibility handlers use these stable composition anchors.
        self.main_area = self.tabs["work"]
        self.sidebar = tk.Frame(self.tabs["system"], bg=THEME.color_panel_bg)
        self.sidebar.pack(fill=tk.X)
        self.communication_area = tk.Frame(self.tabs["system"], bg=THEME.color_panel_bg)
        self.communication_area.pack(fill=tk.X)
        self.workbar_area = tk.Frame(self.tabs["standard"], bg=THEME.color_panel_bg)
        self.workbar_area.pack(fill=tk.X)
        self.next_step_area = tk.Frame(self.tabs["standard"], bg=THEME.color_panel_bg)
        self.next_step_area.pack(fill=tk.X)
        results = tk.Frame(panes, bg=THEME.color_panel_bg)
        panes.add(results, weight=1)
        self._build_output_panel(results)
        self.activity_canvas.configure(height=160)

    def _scroll_content(self, parent: Any, tab_id: str) -> Any:
        import tkinter as tk
        from tkinter import ttk

        canvas = tk.Canvas(parent, bg=THEME.color_panel_bg, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        content = tk.Frame(canvas, bg=THEME.color_panel_bg, padx=8, pady=8)
        window = canvas.create_window((0, 0), window=content, anchor=tk.NW)
        content.bind("<Configure>", lambda _event: canvas.configure(scrollregion=canvas.bbox(tk.ALL)))
        canvas.bind("<Configure>", lambda event: canvas.itemconfigure(window, width=event.width))
        # Bind locally, so scrolling a Text widget never scrolls another tab.
        for event_name in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            canvas.bind(event_name, lambda event, target=canvas: self._scroll_tab(event, target))
        self.tab_canvases[tab_id] = canvas
        return content

    @staticmethod
    def _scroll_tab(event: Any, canvas: Any) -> str:
        number = getattr(event, "num", None)
        delta = getattr(event, "delta", 0)
        if number == 4 or delta > 0:
            canvas.yview_scroll(-1, "units")
        elif number == 5 or delta < 0:
            canvas.yview_scroll(1, "units")
        return "break"

    def _build_main_content(self) -> None:
        import tkinter as tk

        self._build_communication_panel(self.communication_area)
        build_guided_workbar(self, self.workbar_area)
        self._build_next_step_panel(self.next_step_area)
        self._build_task_editor(self.tabs["work"])
        if self.task_text is not None:
            self.task_text.insert("1.0", self._task_draft)
            self.task_editor_state = self._task_draft_state
            if self.task_editor_state == TaskEditorState.SENT:
                self.task_text.configure(state="disabled")
            self.refresh_task_editor_buttons()
        else:
            tk.Label(
                self.tabs["work"], text="Select File Transfer in System to send tasks. "
                "Use the communication helpers below for the selected mode.",
                bg=THEME.color_panel_bg, wraplength=700, justify=tk.LEFT,
            ).pack(fill=tk.X, pady=12)
        self._build_copy_paste_tools(self.tabs["work"])
        if self._advanced_access_visible():
            self._build_action_cards(self.tabs["tools"])
            self.action_scroll_shell.configure(height=220)
            self.action_card_canvas.configure(height=220)
            self._build_advanced_tools(self.tabs["tools"])
            self._build_file_browser(self.tabs["tools"])
        else:
            tk.Label(
                self.tabs["tools"], text="Choose Advanced or Maintainer in System to show Kit tools. "
                "Visibility does not grant execution permission.",
                bg=THEME.color_panel_bg, wraplength=700, justify=tk.LEFT,
            ).pack(fill=tk.X, pady=12)

    def _panel_group_expanded(self, group_id: str) -> bool:
        if group_id == "task_editor" and group_id not in self.panel_expanded_state:
            return True
        return super()._panel_group_expanded(group_id)

    def _remember_task(self) -> None:
        if getattr(self, "task_text", None) is not None:
            self._task_draft = self.task_text.get("1.0", "end").rstrip("\n")
            self._task_draft_state = self.task_editor_state

    def _rebuild_main_content(self) -> None:
        self._remember_task()
        # Invalidate while the old controls still exist; Tk rejects operations
        # on a destroyed widget even if Python retains a reference to it.
        self._disable_confirm_publish()
        self._disable_confirm_discard()
        self.pending_release_preview = None
        self.pending_gc_preview = None
        for area in (self.workbar_area, self.next_step_area, self.tabs["work"], self.tabs["tools"], self.communication_area):
            for child in area.winfo_children():
                child.destroy()
        for group_id in ("communication", "next_step", "task_editor", "action_table", "advanced_tools", "file_browser", "copy_paste_tools"):
            self.gui_group_frames[group_id] = None
            setattr(self, f"{group_id}_frame", None)
        self.work_finish_confirm_button = None
        self.work_discard_confirm_button = None
        self.release_confirm_button = None
        self.gc_confirm_delete_button = None
        self.action_card_widgets = {}
        self._build_main_content()

    def focus_make_changes(self) -> None:
        self.notebook.select(self.tab_viewports["work"])
        super().focus_make_changes()

    def run_work_check(self) -> None:
        super().run_work_check()
        for child in self.workbar_area.winfo_children():
            child.destroy()
        build_guided_workbar(self, self.workbar_area)

    def _select_action(self, action_id: str) -> None:
        self.selected_action_id_value = action_id
        if self._advanced_access_visible():
            self.notebook.select(self.tab_viewports["tools"])
            self._refresh_action_card_selection()
        self.inspect_selected()

    def show_chat_handoff(self) -> None:
        self.log_action("Chat handoff")
        completed = self._agentic_command("transfer", "chat-switch-complete", "--render-prompt")
        self.log_result("Chat handoff", self._completed_status(completed), completed.stdout or completed.stderr)

    def refresh_guided_status(self) -> None:
        mode, access = self.current_communication_mode(), self.basic_view.access_level
        root = self.project_root
        view = self.service_bridge.call(
            lambda: build_basic_cockpit_view_model(
                root, gatekeeper_status=self._gatekeeper_status,
                communication_mode=mode, access_level=access,
            ), label="Read Kit status",
        )
        self.basic_view = view
        self.recovery_action_id = recommended_recovery_action_id(view)
        self._update_project_chrome()
        self._rebuild_sidebar()
        self._rebuild_main_content()
        self.log_result("Refresh status", "INFO", view.reason)

    def switch_project_root(self, path: Path | str) -> bool:
        if self.service_bridge.busy:
            self.log_result("Open project", "BLOCKED", "Wait for the active Kit action to finish.")
            return False
        # Never carry a private task or an approval into another repository.
        self._remember_task()
        old_draft, old_state = self._task_draft, self._task_draft_state
        saved_text = getattr(self, "task_text", None)
        self.task_text = None
        self._task_draft, self._task_draft_state = "", TaskEditorState.IDLE
        switched = super().switch_project_root(path)
        if not switched:
            self.task_text = saved_text
            self._task_draft, self._task_draft_state = old_draft, old_state
        return switched


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="agentic-kit-gui-guided")
    parser.add_argument("--root", default=".", help="Git repository to open.")
    args = parser.parse_args(argv)
    import tkinter as tk

    root = tk.Tk()
    GuidedKitGui(root, Path(args.root))
    root.mainloop()


if __name__ == "__main__":
    main()
