from __future__ import annotations

from datetime import datetime, timezone
import json
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
from agentic_project_kit.gui_cockpit_common import (
    THEME,
    action_tree_tag_colors,
    format_state_details,
)
from agentic_project_kit.gui_release_flow import (
    humanize_release_result,
    normalize_release_version,
    release_prepare_args,
    release_preview_signature,
    release_ready_args,
)
from agentic_project_kit.gui_tk_widgets import attach_tooltip, traffic_light_fill
from agentic_project_kit.gui_tkinter_shell import run_basic_cockpit_button


class CockpitActionsMixin:
    def _build_next_step_panel(self, parent: Any) -> None:
        import tkinter as tk
        from tkinter import ttk

        next_step = self.basic_view.next_step
        panel = tk.Frame(
            parent,
            bg=THEME.color_recommended_bg,
            highlightbackground="#7eb1f1",
            highlightthickness=1,
            padx=10,
            pady=6,
        )
        panel.pack(fill=tk.X, pady=(0, 8))

        header = tk.Frame(panel, bg=THEME.color_recommended_bg)
        header.pack(fill=tk.X, pady=(0, 4))
        tk.Label(
            header,
            text="NEXT STEP",
            bg=THEME.color_recommended_bg,
            fg="#174ea6",
            font=THEME.section_font,
            anchor=tk.W,
        ).pack(side=tk.LEFT)
        status = tk.Frame(header, bg=THEME.color_recommended_bg)
        status.pack(side=tk.RIGHT)
        light = tk.Canvas(status, width=14, height=14, bg=THEME.color_recommended_bg, highlightthickness=0)
        fill = traffic_light_fill(self.basic_view.traffic_light_color)
        light.create_oval(3, 3, 11, 11, fill=fill, outline=fill)
        light.pack(side=tk.LEFT, padx=(0, 5))
        tk.Label(
            status,
            text=next_step.state_label,
            bg=THEME.color_recommended_bg,
            fg="#174ea6",
            font=THEME.small_font,
        ).pack(side=tk.LEFT)

        tk.Label(
            panel,
            text=next_step.title,
            bg=THEME.color_recommended_bg,
            fg="#0b2f27",
            font=THEME.recommended_font,
            anchor=tk.W,
            justify=tk.LEFT,
            wraplength=720,
        ).pack(fill=tk.X)
        tk.Label(
            panel,
            text=next_step.message,
            bg=THEME.color_recommended_bg,
            fg="#174ea6",
            font=THEME.body_font,
            anchor=tk.W,
            justify=tk.LEFT,
            wraplength=720,
        ).pack(fill=tk.X, pady=(5, 0))

        button_row = tk.Frame(panel, bg=THEME.color_recommended_bg)
        button_row.pack(fill=tk.X, pady=(6, 0))
        primary_state = tk.NORMAL if next_step.primary_enabled else tk.DISABLED
        primary = ttk.Button(
            button_row,
            text=next_step.primary_label,
            command=self.run_recommended_action,
            state=primary_state,
        )
        primary.pack(side=tk.LEFT, padx=(0, 8))
        attach_tooltip(primary, self.basic_view.recommended_action.tooltip)
        why = ttk.Button(button_row, text="Why?", command=self.show_next_step_details)
        why.pack(side=tk.LEFT, padx=(0, 8))
        attach_tooltip(why, "Explain why this next step is recommended and show the current state details.")
        help_button = ttk.Button(button_row, text="Help", command=self.show_cockpit_help)
        help_button.pack(side=tk.LEFT)
        attach_tooltip(help_button, "Show the current help placeholder, project sources, and maintainer contact.")

    def show_next_step_details(self) -> None:
        next_step = self.basic_view.next_step
        lines = [
            "",
            "NEXT STEP DETAILS",
            f"title={next_step.title}",
            f"primary_action={next_step.primary_label}",
            f"primary_enabled={str(next_step.primary_enabled).lower()}",
            f"reason={next_step.reason}",
            "",
            format_state_details(self.basic_view),
            "",
        ]
        self.write_output("\n".join(lines))

    def show_cockpit_help(self) -> None:
        lines = [
            "",
            "HELP (under construction)",
            "The cockpit help area is under construction.",
            "Authoritative sources:",
            "- GitHub: https://github.com/vfi64/agentic-project-kit",
            "- Zenodo concept DOI: https://doi.org/10.5281/zenodo.20101359",
            "- Current verified Zenodo DOI: https://doi.org/10.5281/zenodo.20917074",
            "- Maintainer: Volker Fickert",
            "",
        ]
        self.write_output("\n".join(lines))

    def _build_action_cards(self, parent: Any) -> None:
        import tkinter as tk
        from tkinter import ttk

        self._section_heading(parent, "Actions")
        actions_row = tk.Frame(parent, bg=THEME.color_panel_bg)
        actions_row.pack(fill=tk.X, pady=(0, 10))
        action_scroll_shell = tk.Frame(actions_row, bg=THEME.color_panel_bg, width=THEME.action_list_width)
        action_scroll_shell.pack(side=tk.LEFT, fill=tk.Y)
        action_scroll_shell.pack_propagate(False)
        self.action_card_canvas = tk.Canvas(
            action_scroll_shell,
            bg=THEME.color_panel_bg,
            width=THEME.action_list_width,
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
        self.action_card_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.action_card_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.action_card_widgets: dict[str, Any] = {}
        self.populate_action_tree()

        controls = tk.Frame(actions_row, bg=THEME.color_panel_bg)
        controls.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(12, 0))
        inspect_button = ttk.Button(controls, text="Inspect", command=self.inspect_selected)
        attach_tooltip(inspect_button, "Show metadata, command, and safety details for the selected action.")
        inspect_button.grid(row=0, column=0, sticky="ew", padx=(0, 8), pady=(0, 6))
        run_button = ttk.Button(controls, text="Run read-only", command=self.run_selected_read_only)
        attach_tooltip(run_button, "Run only selected read-only cockpit actions through the shared cockpit layer.")
        run_button.grid(row=0, column=1, sticky="ew", pady=(0, 6))

        create_button = ttk.Button(controls, text="Create release", command=self.start_create_release)
        create_button.grid(row=1, column=0, sticky="ew", padx=(0, 8), pady=(0, 6))
        attach_tooltip(
            create_button,
            "Ask for a version, run release ready, then enable Confirm create release on PASS.",
        )
        self.release_confirm_button = ttk.Button(
            controls,
            text="Confirm create release",
            command=self.confirm_create_release,
            state=tk.DISABLED,
        )
        self.release_confirm_button.grid(row=1, column=1, sticky="ew", pady=(0, 6))
        attach_tooltip(
            self.release_confirm_button,
            "Runs agentic-kit release prepare --write only after a successful readiness preview for the same version and state.",
        )

        maintenance_row = tk.Frame(controls, bg=THEME.color_panel_bg)
        maintenance_row.grid(row=2, column=0, columnspan=2, sticky="ew")
        tk.Label(
            maintenance_row,
            text="Local tmp cutoff",
            bg=THEME.color_panel_bg,
            fg=THEME.color_muted_text,
            font=THEME.small_font,
        ).pack(side=tk.LEFT, padx=(0, 6))
        self.gc_cutoff_var = tk.StringVar(value=self._default_gc_cutoff())
        cutoff_entry = ttk.Entry(maintenance_row, textvariable=self.gc_cutoff_var, width=20)
        attach_tooltip(cutoff_entry, "ISO cutoff for local repository tmp/ cleanup. Default is now.")
        cutoff_entry.pack(side=tk.LEFT, padx=(0, 9))
        gc_button = ttk.Button(maintenance_row, text="Clean local tmp", command=self.preview_log_cleanup)
        attach_tooltip(
            gc_button,
            "Dry-run local artifact-gc for old untracked files and empty directories under repository tmp/. Never touches the remote repository.",
        )
        gc_button.pack(side=tk.LEFT, padx=(0, 9))
        self.gc_confirm_delete_button = ttk.Button(
            maintenance_row,
            text="Confirm delete",
            command=self.confirm_log_cleanup,
            state=tk.DISABLED,
        )
        attach_tooltip(
            self.gc_confirm_delete_button,
            "Deletes local tmp/ candidates only after a successful preview. Never touches the remote repository.",
        )
        self.gc_confirm_delete_button.pack(side=tk.LEFT, padx=(0, 9))
        self.pending_gc_preview = None
        controls.columnconfigure(0, weight=1)
        controls.columnconfigure(1, weight=1)

    def _default_gc_cutoff(self) -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    def _gc_cutoff_value(self) -> str:
        cutoff_var = getattr(self, "gc_cutoff_var", None)
        value = cutoff_var.get().strip() if cutoff_var is not None else ""
        if value:
            return value
        value = self._default_gc_cutoff()
        if cutoff_var is not None:
            cutoff_var.set(value)
        return value

    def _gc_command_args(self, *, cutoff: str, execute: bool) -> tuple[str, ...]:
        args = (
            "artifact-gc",
            "--local-tmp-contents",
            "--older-than",
            cutoff,
        )
        if execute:
            return (*args, "--execute", "--json")
        return (*args, "--json")

    def _write_gc_result(self, completed: Any) -> dict[str, object] | None:
        output = completed.stdout or completed.stderr
        self.write_output("\n" + output + "\n")
        if not completed.stdout:
            return None
        try:
            payload = json.loads(completed.stdout)
        except ValueError:
            return None
        return payload if isinstance(payload, dict) else None

    def _disable_confirm_delete(self) -> None:
        self.pending_gc_preview = None
        button = getattr(self, "gc_confirm_delete_button", None)
        if button is not None:
            button.configure(state="disabled")

    def _disable_confirm_release(self) -> None:
        self.pending_release_preview = None
        button = getattr(self, "release_confirm_button", None)
        if button is not None:
            button.configure(state="disabled")

    def preview_log_cleanup(self) -> None:
        cutoff = self._gc_cutoff_value()
        args = self._gc_command_args(cutoff=cutoff, execute=False)
        self.write_output(f"\nRunning local tmp cleanup preview for files before {cutoff}...\n")
        completed = self._agentic_command(*args)
        payload = self._write_gc_result(completed)
        candidate_count = int(payload.get("candidate_count", 0)) if payload else 0
        if completed.returncode == 0 and candidate_count > 0:
            self.pending_gc_preview = {
                "cutoff": cutoff,
                "args": args,
                "candidate_count": candidate_count,
            }
            if self.gc_confirm_delete_button is not None:
                self.gc_confirm_delete_button.configure(state="normal")
            return
        self._disable_confirm_delete()

    def confirm_log_cleanup(self) -> None:
        if not self.pending_gc_preview:
            self.write_output("\nRun Clean up logs first. Confirm is enabled only after a dry-run preview.\n")
            return
        cutoff = self._gc_cutoff_value()
        if self.pending_gc_preview.get("cutoff") != cutoff:
            self.write_output("\nLog cleanup cutoff changed after the preview. Run Clean up logs again before confirming.\n")
            self._disable_confirm_delete()
            return
        self.write_output(f"\nDeleting local tmp cleanup candidates before {cutoff}...\n")
        completed = self._agentic_command(*self._gc_command_args(cutoff=cutoff, execute=True))
        self._write_gc_result(completed)
        self._disable_confirm_delete()

    def _current_release_version(self) -> str | None:
        version_var = getattr(self, "release_version_var", None)
        value = version_var.get() if version_var is not None else ""
        return normalize_release_version(value)

    def _release_state_signature(self, version: str) -> str:
        work_signature = self._work_cycle_signature() if hasattr(self, "_work_cycle_signature") else ""
        return release_preview_signature(version=version, state_signature=work_signature)

    def start_create_release(self) -> None:
        from tkinter import simpledialog

        current = self.release_version_var.get().strip()
        version = simpledialog.askstring(
            "Create release",
            "Enter target version (X.Y.Z):",
            initialvalue=current,
            parent=self.root,
        )
        if version is None:
            self.write_output("\nCreate release cancelled.\n")
            self._disable_confirm_release()
            return
        self.release_version_var.set(version.strip())
        self.preview_create_release()

    def _write_release_result(self, completed: Any, *, preview: bool) -> dict[str, object] | None:
        output = completed.stdout or completed.stderr
        if not completed.stdout:
            self.write_output("\n" + output + "\n")
            self._disable_confirm_release()
            return None
        try:
            payload = json.loads(completed.stdout)
        except ValueError:
            self.write_output("\n" + output + "\n")
            self._disable_confirm_release()
            return None
        if not isinstance(payload, dict):
            self.write_output("\n" + output + "\n")
            self._disable_confirm_release()
            return None
        message = humanize_release_result(payload, preview=preview)
        lines = ["", message.headline, message.detail]
        if message.blockers:
            lines.append("")
            lines.extend(f"- {blocker}" for blocker in message.blockers)
        lines.append("")
        self.write_output("\n".join(lines))
        if preview and message.allow_confirm:
            version = str(payload.get("version", "")).strip()
            self.pending_release_preview = {
                "version": version,
                "signature": self._release_state_signature(version),
                "payload": payload,
            }
            if self.release_confirm_button is not None:
                self.release_confirm_button.configure(state="normal")
        else:
            self._disable_confirm_release()
        return payload

    def preview_create_release(self) -> None:
        version = self._current_release_version()
        if version is None:
            self.write_output("\nEnter a release version in X.Y.Z format before creating a release.\n")
            self._disable_confirm_release()
            return
        completed = self._agentic_command(*release_ready_args(version))
        self._write_release_result(completed, preview=True)

    def confirm_create_release(self) -> None:
        version = self._current_release_version()
        if not self.pending_release_preview or version is None:
            self.write_output("\nRun Create release first. Confirm is enabled only after a passing readiness preview.\n")
            self._disable_confirm_release()
            return
        if self.pending_release_preview.get("signature") != self._release_state_signature(version):
            self.write_output(
                "\nVersion or state changed after preview, run Create release again before confirming.\n"
            )
            self._disable_confirm_release()
            return
        completed = self._agentic_command(*release_prepare_args(version))
        self._write_release_result(completed, preview=False)


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
        self.write_output("\nInspecting selected action...\n\n" + format_action_details(action) + "\n")

    def run_basic_action(self, command_id: str) -> None:
        self.write_output(f"\nRunning basic action: {command_id}...\n")
        self.write_output(run_basic_cockpit_button(command_id, project_root=self.project_root) + "\n")

    def run_selected_read_only(self) -> None:
        action_id = self.selected_action_id()
        if action_id is None:
            self.write_output("No cockpit action selected.\n")
            return
        action = self.action_view_by_id(action_id)
        if action is not None and action.safety != READ_ONLY:
            self.write_output("\n" + format_action_details(action) + "\n")
            return
        self.write_output(f"\nRunning read-only action: {action_id}...\n")
        result = run_cockpit_action(action_id, self.project_root, allow_bounded=False)
        self.write_output("\n" + format_action_result(result) + "\n")
