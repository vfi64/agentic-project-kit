from __future__ import annotations

import json
import subprocess
from typing import Any

from agentic_project_kit.gui_cockpit_common import HEADER_TEXT, THEME
from agentic_project_kit.gui_tk_widgets import attach_tooltip
from agentic_project_kit.work_cycle import (
    ChangedPath,
    build_work_cycle_views,
    build_work_finish_args,
    changed_paths_from_status,
    derive_work_phase,
    humanize_work_result,
    slugify_work_title,
)


class CockpitHeaderMixin:
    def _build_header(self, parent: Any) -> None:
        import tkinter as tk
        from tkinter import ttk

        header = tk.Frame(parent, bg=THEME.color_panel_bg, height=48)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        icon = tk.Canvas(header, width=18, height=18, bg=THEME.color_panel_bg, highlightthickness=0)
        icon.create_rectangle(3, 3, 15, 15, outline="#1f5b9d", width=2)
        icon.pack(side=tk.LEFT, padx=(16, 9))

        tk.Label(
            header,
            text=HEADER_TEXT,
            bg=THEME.color_panel_bg,
            font=THEME.title_font,
            anchor=tk.W,
        ).pack(side=tk.LEFT, fill=tk.X, expand=True)

        branch_label = self._branch_label()
        branch_icon = tk.Canvas(header, width=14, height=14, bg=THEME.color_panel_bg, highlightthickness=0)
        branch_icon.create_rectangle(3, 3, 11, 11, outline="#656565", width=2)
        branch_icon.pack(side=tk.LEFT, padx=(0, 7))
        tk.Label(
            header,
            text=branch_label,
            bg=THEME.color_panel_bg,
            fg="#4d4d4d",
            font=THEME.body_font,
        ).pack(side=tk.RIGHT, padx=(0, 16))

        ttk.Separator(parent, orient=tk.HORIZONTAL).pack(fill=tk.X)

    def _build_work_cycle_bar(self, parent: Any) -> None:
        import tkinter as tk
        from tkinter import ttk

        phase = self.current_work_phase()
        views = build_work_cycle_views(phase)
        normal_views = [view for view in views if view.phase_id != "recover"]
        recovery_view = next(view for view in views if view.phase_id == "recover")

        frame = tk.Frame(parent, bg=THEME.color_panel_bg, padx=16, pady=10)
        self._register_group_frame("work_cycle", frame)
        self.start_from_ref_picker = None
        frame.pack(fill=tk.X)
        title = tk.Label(
            frame,
            text="WORK CYCLE",
            bg=THEME.color_panel_bg,
            fg=THEME.color_muted_text,
            font=THEME.section_font,
        )
        title.pack(side=tk.LEFT, padx=(0, 12))

        if phase == "recover":
            button = tk.Button(
                frame,
                text=recovery_view.label,
                command=self.run_work_recover,
                bg=THEME.color_bounded,
                fg="#5f2f00",
                font=THEME.action_font,
                relief=tk.GROOVE,
                bd=1,
                padx=10,
                pady=5,
            )
            attach_tooltip(button, recovery_view.tooltip)
            button.pack(side=tk.LEFT, padx=(0, 8))
        else:
            ref_frame = tk.Frame(frame, bg=THEME.color_panel_bg)
            ref_frame.pack(side=tk.LEFT, padx=(0, 10))
            tk.Label(
                ref_frame,
                text="Start new work based on",
                bg=THEME.color_panel_bg,
                fg=THEME.color_muted_text,
                font=THEME.small_font,
            ).pack(side=tk.TOP, anchor=tk.W)
            ref_picker = ttk.Combobox(
                ref_frame,
                textvariable=self.start_from_ref_value,
                values=self._start_from_ref_options(),
                width=18,
                state="readonly",
            )
            self.start_from_ref_picker = ref_picker
            ref_picker.pack(side=tk.TOP, anchor=tk.W)
            attach_tooltip(
                ref_picker,
                "This creates a fresh workspace starting from the chosen version. It does not rewind history.",
            )
            for index, view in enumerate(normal_views):
                button = tk.Button(
                    frame,
                    text=view.label,
                    command=self._work_cycle_command_for(view.phase_id),
                    bg=THEME.color_recommended_bg if view.is_current else THEME.color_panel_bg,
                    fg="#174ea6" if view.is_current else "#222222",
                    font=THEME.action_font if view.is_current else THEME.body_font,
                    relief=tk.GROOVE,
                    bd=1,
                    padx=10,
                    pady=5,
                    state=tk.NORMAL if view.is_available else tk.DISABLED,
                )
                attach_tooltip(button, f"{view.tooltip}\n{view.command_hint}")
                button.pack(side=tk.LEFT, padx=(0, 6))
                if index < len(normal_views) - 1:
                    tk.Label(
                        frame,
                        text="→",
                        bg=THEME.color_panel_bg,
                        fg=THEME.color_muted_text,
                        font=THEME.body_font,
                    ).pack(side=tk.LEFT, padx=(0, 6))

        self.work_finish_confirm_button = ttk.Button(
            frame,
            text="Confirm publish",
            command=self.confirm_work_finish,
            state=tk.DISABLED,
        )
        attach_tooltip(
            self.work_finish_confirm_button,
            "Runs agentic-kit work finish --execute only after a successful dry-run preview.",
        )
        self.work_finish_confirm_button.pack(side=tk.RIGHT)
        self.open_project_button = ttk.Button(
            frame,
            text="Open project...",
            command=self.open_project,
        )
        attach_tooltip(
            self.open_project_button,
            "Select a local Git repository. The cockpit switches context without initializing it.",
        )
        self.open_project_button.pack(side=tk.RIGHT, padx=(0, 8))
        self.project_status_label = tk.Label(
            frame,
            textvariable=self.project_status_var,
            bg=THEME.color_panel_bg,
            fg=THEME.color_muted_text,
            font=THEME.small_font,
        )
        self.project_status_label.pack(side=tk.RIGHT, padx=(0, 12))
        ttk.Separator(parent, orient=tk.HORIZONTAL).pack(fill=tk.X)

    def _start_from_ref_options(self) -> tuple[str, ...]:
        try:
            completed = self._agentic_command("transfer", "list-refs", "--json")
            payload = json.loads(completed.stdout) if completed.returncode == 0 and completed.stdout else {}
        except (OSError, ValueError):
            payload = {}
        tags = [str(item) for item in payload.get("tags", []) if str(item).strip()]
        branches = [str(item) for item in payload.get("branches", []) if str(item).strip()]
        remote_branches = [
            str(item)
            for item in payload.get("remote_branches", [])
            if str(item).strip() and str(item).strip() not in {"origin/HEAD"}
        ]
        values = ["latest main", *tags, *branches, *remote_branches]
        deduped = tuple(dict.fromkeys(values))
        if self.start_from_ref_value.get() not in deduped:
            self.start_from_ref_value.set(deduped[0])
        return deduped

    def selected_start_ref(self) -> str:
        selected = self.start_from_ref_value.get().strip()
        return "main" if selected in {"", "latest main"} else selected

    def _work_cycle_command_for(self, phase_id: str) -> Any:
        if phase_id == "start":
            return self.start_work_cycle
        if phase_id == "changes":
            return self.focus_make_changes
        if phase_id == "check":
            return self.run_work_check
        if phase_id == "finish":
            return self.preview_work_finish
        return self.run_work_recover

    def _branch_label(self) -> str:
        branch = "unknown"
        for part in self.basic_view.evidence.split(";"):
            key, _, value = part.strip().partition("=")
            if key == "branch" and value:
                branch = value
                break
        try:
            head = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                cwd=self.project_root,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            short = head.stdout.strip() if head.returncode == 0 else "unknown"
        except OSError:
            short = "unknown"
        return f"{branch} · {short}"

    def current_branch(self) -> str:
        for part in self.basic_view.evidence.split(";"):
            key, _, value = part.strip().partition("=")
            if key == "branch" and value:
                return value
        return "unknown"

    def _git_status_short(self) -> str:
        try:
            completed = subprocess.run(
                ["git", "status", "--short"],
                cwd=self.project_root,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
        except OSError:
            return ""
        return completed.stdout if completed.returncode == 0 else ""

    def _changed_paths(self) -> tuple[ChangedPath, ...]:
        return changed_paths_from_status(self._git_status_short())

    def _work_cycle_signature(self) -> str:
        return f"{self.current_branch()}::{self._git_status_short()}"

    def current_work_phase(self) -> str:
        branch = self.current_branch()
        changed_paths = self._changed_paths()
        has_blockers = self.basic_view.traffic_light_state in {"BLOCKED", "FAILED", "WAIT_FOR_D2"}
        return derive_work_phase(
            repo_clean=not changed_paths,
            on_feature_branch=branch not in {"", "unknown", "main", "master"},
            has_blockers=has_blockers,
            has_changes=bool(changed_paths),
            last_check_passed=(
                self.work_cycle_last_check_passed
                and self.work_cycle_last_check_signature == self._work_cycle_signature()
            ),
        )


    def _write_work_command_result(
        self,
        completed: subprocess.CompletedProcess[str],
        *,
        label: str = "Work result",
        allow_confirm_from_preview: bool = False,
        allow_confirm_discard_from_preview: bool = False,
    ) -> dict[str, object] | None:
        output = completed.stdout or completed.stderr
        payload: dict[str, object] | None = None
        if completed.stdout:
            try:
                loaded = json.loads(completed.stdout)
                if isinstance(loaded, dict):
                    payload = loaded
            except ValueError:
                payload = None
        if payload is None:
            self.log_result(label, "PASS" if completed.returncode == 0 else "ERROR", output)
            self._disable_confirm_publish()
            self._disable_confirm_discard()
            return None
        message = humanize_work_result(payload)
        lines = [
            "",
            message.headline,
            message.detail,
        ]
        if message.blockers_human:
            lines.append("")
            lines.extend(f"- {blocker}" for blocker in message.blockers_human)
        lines.extend(["", f"Next: {message.suggested_next}", ""])
        self.log_result(label, str(payload.get("result_status", "")), "\n".join(lines))
        if allow_confirm_from_preview and message.allow_confirm_publish:
            self.pending_finish_preview = payload
            if self.work_finish_confirm_button is not None:
                self.work_finish_confirm_button.configure(state="normal")
            self._disable_confirm_discard()
        elif allow_confirm_discard_from_preview and message.allow_confirm_discard:
            self.pending_discard_preview = payload
            if self.work_discard_confirm_button is not None:
                self.work_discard_confirm_button.configure(state="normal")
            self._disable_confirm_publish()
        else:
            self._disable_confirm_publish()
            self._disable_confirm_discard()
        return payload

    def _disable_confirm_publish(self) -> None:
        self.pending_finish_preview = None
        if self.work_finish_confirm_button is not None:
            self.work_finish_confirm_button.configure(state="disabled")

    def _disable_confirm_discard(self) -> None:
        self.pending_discard_preview = None
        if self.work_discard_confirm_button is not None:
            self.work_discard_confirm_button.configure(state="disabled")

    def _discard_available(self) -> bool:
        return self.current_branch() not in {"", "unknown", "main", "master"} and bool(self._changed_paths())

    def start_work_cycle(self) -> None:
        from tkinter import simpledialog

        self.log_action("Start work")
        title = self.current_task_body()
        if not title:
            title = simpledialog.askstring(
                "Start work",
                "What are you working on?",
                parent=self.root,
            ) or ""
        branch = slugify_work_title(title)
        start_ref = self.selected_start_ref()
        self.log_result("Start work", "INFO", f"Start new work based on {start_ref}.")
        completed = self._agentic_command(
            "work",
            "start",
            "--branch",
            branch,
            "--kind",
            "patch",
            "--from-ref",
            start_ref,
            "--json",
        )
        self._write_work_command_result(completed, label="Start work")

    def focus_make_changes(self) -> None:
        self.log_action("Make changes")
        if self.task_text is not None:
            self.task_text.focus_set()
            self.task_text.configure(highlightthickness=1, highlightbackground="#7eb1f1")
        self.log_result(
            "Make changes",
            "INFO",
            "Describe the change in the file-transfer task editor, then send it. "
            "The assistant will work from the published task carrier via g/go.",
        )

    def run_work_check(self) -> None:
        self.log_action("Check")
        signature = self._work_cycle_signature()
        completed = self._agentic_command("work", "check", "--profile", "code", "--json")
        payload = self._write_work_command_result(completed, label="Check")
        self.work_cycle_last_check_passed = bool(
            payload and str(payload.get("result_status", "")).upper() == "PASS"
        )
        self.work_cycle_last_check_signature = signature if self.work_cycle_last_check_passed else ""

    def _finish_title(self) -> str:
        task_body = self.current_task_body()
        first_line = next((line.strip() for line in task_body.splitlines() if line.strip()), "")
        return first_line or "Finish guided work slice"

    def _current_finish_args(self, *, execute: bool) -> tuple[str, ...] | None:
        paths = self._changed_paths()
        if not paths:
            fake_payload = {
                "result_status": "BLOCKED",
                "action": "work-finish",
                "blockers": ["path-selection"],
                "dry_run": not execute,
            }
            self._write_work_command_result(
                subprocess.CompletedProcess(args=(), returncode=2, stdout=json.dumps(fake_payload), stderr="")
            )
            return None
        branch = self.current_branch()
        if branch in {"", "unknown", "main", "master"}:
            fake_payload = {
                "result_status": "BLOCKED",
                "action": "work-finish",
                "blockers": ["repo-status"],
                "dry_run": not execute,
            }
            self._write_work_command_result(
                subprocess.CompletedProcess(args=(), returncode=2, stdout=json.dumps(fake_payload), stderr="")
            )
            return None
        title = self._finish_title()
        return build_work_finish_args(
            branch=branch,
            title=title,
            message=title,
            paths=paths,
            execute=execute,
        )

    def preview_work_finish(self) -> None:
        self.log_action("Finish & publish")
        args = self._current_finish_args(execute=False)
        if args is None:
            return
        completed = self._agentic_command(*args)
        payload = self._write_work_command_result(completed, label="Finish & publish", allow_confirm_from_preview=True)
        if payload and self.pending_finish_preview is not None:
            self.pending_finish_preview = {
                "payload": payload,
                "signature": self._work_cycle_signature(),
                "args": args,
            }

    def confirm_work_finish(self) -> None:
        self.log_action("Confirm publish")
        if not self.pending_finish_preview:
            self.log_result(
                "Confirm publish",
                "INFO",
                "Run Finish & publish first. Confirm is enabled only after a passing dry-run.",
            )
            return
        if self.pending_finish_preview.get("signature") != self._work_cycle_signature():
            self.log_result(
                "Confirm publish",
                "BLOCKED",
                "Changed files moved after the dry-run. Run Finish & publish again before confirming.",
            )
            self._disable_confirm_publish()
            return
        args = self._current_finish_args(execute=True)
        if args is None:
            return
        completed = self._agentic_command(*args)
        self._write_work_command_result(completed, label="Confirm publish")

    def run_work_recover(self) -> None:
        self.log_action("Needs recovery")
        completed = self._agentic_command("work", "recover", "--json")
        self._write_work_command_result(completed, label="Needs recovery")

    def preview_discard_changes(self) -> None:
        self.log_action("Discard all changes")
        completed = self._agentic_command("work", "discard-changes", "--json")
        payload = self._write_work_command_result(
            completed,
            label="Discard all changes",
            allow_confirm_discard_from_preview=True,
        )
        if payload and self.pending_discard_preview is not None:
            self.pending_discard_preview = {
                "payload": payload,
                "signature": self._work_cycle_signature(),
                "discard_signature": str(payload.get("signature", "")),
            }

    def confirm_discard_changes(self) -> None:
        self.log_action("Confirm discard")
        if not self.pending_discard_preview:
            self.log_result(
                "Confirm discard",
                "INFO",
                "Run Discard all changes first. Confirm is enabled only after a passing dry-run.",
            )
            return
        if self.pending_discard_preview.get("signature") != self._work_cycle_signature():
            self.log_result(
                "Confirm discard",
                "BLOCKED",
                "Changed files moved after the dry-run. Run Discard all changes again before confirming.",
            )
            self._disable_confirm_discard()
            return
        discard_signature = str(self.pending_discard_preview.get("discard_signature", ""))
        completed = self._agentic_command(
            "work",
            "discard-changes",
            "--execute",
            "--expected-signature",
            discard_signature,
            "--json",
        )
        self._write_work_command_result(completed, label="Confirm discard")
