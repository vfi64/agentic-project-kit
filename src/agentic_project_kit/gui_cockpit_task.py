from __future__ import annotations

from pathlib import Path
import subprocess
from typing import Any

from agentic_project_kit.gui_cockpit_common import THEME
from agentic_project_kit.gui_task_editor import (
    CANONICAL_TRANSFER_INBOX_PATH,
    CANONICAL_TRANSFER_OUTBOX_PATH,
    TaskEditorState,
    open_transfer_terminal as open_transfer_terminal_for_project,
    standard_command_args_for_communication_mode,
    standard_command_description_for_communication_mode,
    standard_command_label_for_communication_mode,
    task_editor_send_enabled,
    task_editor_state_after_read,
    task_editor_state_after_send,
    task_editor_visible_for_mode,
    transfer_state_has_canonical_outbox_result,
)
from agentic_project_kit.gui_tk_widgets import attach_tooltip


class CockpitTaskMixin:
    def _build_task_editor(self, parent: Any) -> None:
        import tkinter as tk
        from tkinter import ttk

        self.task_editor_state = TaskEditorState.IDLE
        self.task_status_var = tk.StringVar(value="Write a GUI task, then send it through the guarded wrapper.")
        if not task_editor_visible_for_mode(self.basic_view.communication_mode):
            self.task_text = None
            self.initial_prompt_button = None
            self.task_send_button = None
            self.task_read_button = None
            self.task_open_terminal_button = None
            self.task_standard_command_button = None
            return

        group = self._build_collapsible_group(
            parent,
            group_id="task_editor",
            title="File transfer task",
            subtitle="writes to repo · publishes",
        )
        task_frame = group.body
        self.task_open_terminal_button = None
        self.task_standard_command_button = None
        heading_row = tk.Frame(task_frame, bg=THEME.color_panel_bg)
        heading_row.pack(fill=tk.X)
        tk.Label(
            heading_row,
            text="Describe the task for the LLM.",
            bg=THEME.color_panel_bg,
            font=THEME.body_font,
            anchor=tk.W,
        ).pack(side=tk.LEFT)
        tk.Label(
            heading_row,
            text="writes to repo · publishes",
            bg=THEME.color_panel_bg,
            fg=THEME.color_muted_text,
            font=THEME.small_font,
        ).pack(side=tk.RIGHT)

        self.task_text = tk.Text(
            task_frame,
            height=THEME.task_text_height,
            wrap=tk.WORD,
            font=THEME.body_font,
            relief=tk.GROOVE,
            bd=1,
            padx=9,
            pady=7,
        )
        self.task_text.pack(fill=tk.X, expand=False, pady=(9, 9))
        self.task_text.bind("<KeyRelease>", self.refresh_task_editor_buttons)
        task_button_row = tk.Frame(task_frame, bg=THEME.color_panel_bg)
        task_button_row.pack(fill=tk.X)
        self.initial_prompt_button = ttk.Button(
            task_button_row,
            text="Initial prompt",
            command=self.show_initial_llm_prompt,
        )
        attach_tooltip(
            self.initial_prompt_button,
            "Render the one-time initial LLM prompt for file-transfer dialog setup.",
        )
        self.initial_prompt_button.pack(side=tk.LEFT, padx=(0, 9))
        self.task_send_button = ttk.Button(task_button_row, text="Send", command=self.send_user_task)
        attach_tooltip(
            self.task_send_button,
            "Publish the canonical agentic-kit transfer inbox file "
            f"{CANONICAL_TRANSFER_INBOX_PATH.as_posix()} through "
            "agentic-kit transfer submit-user-task --publish.",
        )
        self.task_send_button.pack(side=tk.LEFT, padx=(0, 9))
        self.task_read_button = ttk.Button(
            task_button_row,
            text="Read",
            command=self.read_last_task_result,
            state=tk.DISABLED,
        )
        attach_tooltip(
            self.task_read_button,
            "Read canonical transfer state through agentic-kit transfer state --json; the local result is .agentic/transfer/outbox/last_result.txt.",
        )
        self.task_read_button.pack(side=tk.LEFT, padx=(0, 9))
        tk.Label(
            task_frame,
            textvariable=self.task_status_var,
            anchor=tk.W,
            justify=tk.LEFT,
            bg=THEME.color_panel_bg,
            fg=THEME.color_muted_text,
            font=THEME.small_font,
            wraplength=620,
        ).pack(fill=tk.X, pady=(7, 0))
        self.refresh_task_editor_buttons()

    def _build_copy_paste_tools(self, parent: Any) -> None:
        import tkinter as tk
        from tkinter import ttk

        group = self._build_collapsible_group(
            parent,
            group_id="copy_paste_tools",
            title="Terminal and standard commands",
            subtitle="local execution helpers",
        )
        body = group.body
        tk.Label(
            body,
            text="Use these helpers when the selected communication mode needs a local command or terminal.",
            bg=THEME.color_panel_bg,
            fg=THEME.color_muted_text,
            font=THEME.small_font,
            anchor=tk.W,
            justify=tk.LEFT,
            wraplength=720,
        ).pack(fill=tk.X, pady=(0, 8))
        row = tk.Frame(body, bg=THEME.color_panel_bg)
        row.pack(fill=tk.X)
        self.task_open_terminal_button = ttk.Button(
            row,
            text="Open local terminal",
            command=self.open_transfer_terminal,
        )
        attach_tooltip(
            self.task_open_terminal_button,
            "Open the operating-system terminal for the currently selected transfer mode.",
        )
        self.task_open_terminal_button.pack(side=tk.LEFT, padx=(0, 9))
        self.task_standard_command_button = ttk.Button(
            row,
            text=standard_command_label_for_communication_mode(self.current_communication_mode()),
            command=self.run_mode_standard_command,
        )
        attach_tooltip(
            self.task_standard_command_button,
            (
                "Run the selected mode's standard command: mode a uses "
                "agentic-kit transfer patch-cycle-status --json; mode b uses "
                "agentic-kit transfer continue --json."
            ),
        )
        self.task_standard_command_button.pack(side=tk.LEFT, padx=(0, 9))
        self.refresh_task_editor_buttons()

    def _build_file_browser(self, parent: Any) -> None:
        import tkinter as tk
        from tkinter import ttk

        group = self._build_collapsible_group(
            parent,
            group_id="file_browser",
            title="Copy / paste files",
            subtitle="read-only local browser",
        )
        browser_frame = group.body
        header = tk.Frame(browser_frame, bg=THEME.color_panel_bg)
        header.pack(fill=tk.X, pady=(0, 6))
        tk.Label(
            header,
            text="COPY / PASTE FILES",
            bg=THEME.color_panel_bg,
            fg=THEME.color_muted_text,
            font=THEME.section_font,
            anchor=tk.W,
        ).pack(side=tk.LEFT)
        tk.Label(
            header,
            text="read-only local browser",
            bg=THEME.color_panel_bg,
            fg=THEME.color_muted_text,
            font=THEME.small_font,
        ).pack(side=tk.RIGHT)

        body = tk.Frame(browser_frame, bg=THEME.color_panel_bg)
        body.pack(fill=tk.X)
        self.file_browser = tk.Listbox(body, height=5, font=THEME.small_font, exportselection=False)
        self.file_browser.pack(side=tk.LEFT, fill=tk.X, expand=True)
        scrollbar = ttk.Scrollbar(body, orient=tk.VERTICAL, command=self.file_browser.yview)
        self.file_browser.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.LEFT, fill=tk.Y, padx=(4, 8))

        buttons = tk.Frame(body, bg=THEME.color_panel_bg)
        buttons.pack(side=tk.LEFT, fill=tk.Y)
        refresh = ttk.Button(buttons, text="Refresh files", command=self.refresh_file_browser)
        refresh.pack(fill=tk.X, pady=(0, 5))
        attach_tooltip(refresh, "Refresh the local read-only file list for tmp and handoff files.")
        copy_path = ttk.Button(buttons, text="Copy path", command=self.copy_selected_file_path)
        copy_path.pack(fill=tk.X, pady=(0, 5))
        attach_tooltip(copy_path, "Copy the selected repository-relative path to the clipboard.")
        copy_file = ttk.Button(buttons, text="Copy file", command=self.copy_selected_file_content)
        copy_file.pack(fill=tk.X)
        attach_tooltip(copy_file, "Copy the selected text file content to the clipboard without editing it.")

        self.file_browser_paths: list[str] = []
        self.refresh_file_browser(write_status=False)

    def _file_browser_roots(self) -> tuple[Path, ...]:
        return (
            Path("tmp"),
            Path("docs/handoff"),
            Path("docs/reports/handoff-packages/latest"),
        )

    def _iter_file_browser_paths(self) -> tuple[str, ...]:
        paths: list[str] = []
        for relative_root in self._file_browser_roots():
            root = self.project_root / relative_root
            if not root.exists() or not root.is_dir():
                continue
            for path in sorted(root.rglob("*")):
                if path.is_symlink() or not path.is_file():
                    continue
                try:
                    rel = path.relative_to(self.project_root).as_posix()
                except ValueError:
                    continue
                paths.append(rel)
        return tuple(paths[:300])

    def refresh_file_browser(self, *, write_status: bool = True) -> None:
        paths = list(self._iter_file_browser_paths())
        self.file_browser_paths = paths
        self.file_browser.delete(0, "end")
        for path in paths:
            self.file_browser.insert("end", path)
        if write_status:
            self.write_output(f"\nFile browser refreshed: {len(paths)} local files listed.\n")

    def _selected_file_browser_path(self) -> Path | None:
        selection = self.file_browser.curselection()
        if not selection:
            self.write_output("\nSelect a file in the Copy / Paste Files browser first.\n")
            return None
        index = int(selection[0])
        try:
            relative = self.file_browser_paths[index]
        except IndexError:
            self.write_output("\nSelected file is no longer available. Refresh files and try again.\n")
            return None
        path = (self.project_root / relative).resolve()
        try:
            path.relative_to(self.project_root.resolve())
        except ValueError:
            self.write_output("\nBlocked: selected path is outside the project root.\n")
            return None
        return path

    def copy_selected_file_path(self) -> None:
        path = self._selected_file_browser_path()
        if path is None:
            return
        relative = path.relative_to(self.project_root).as_posix()
        self.root.clipboard_clear()
        self.root.clipboard_append(relative)
        if hasattr(self.root, "update"):
            self.root.update()
        self.write_output(f"\nCopied path: {relative}\n")

    def copy_selected_file_content(self) -> None:
        path = self._selected_file_browser_path()
        if path is None:
            return
        relative = path.relative_to(self.project_root).as_posix()
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            self.write_output(f"\nBlocked: {relative} is not a UTF-8 text file.\n")
            return
        except OSError as exc:
            self.write_output(f"\nBlocked: could not read {relative}: {exc}\n")
            return
        if len(content) > 200_000:
            self.write_output(f"\nBlocked: {relative} is too large to copy safely from the GUI.\n")
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(content)
        if hasattr(self.root, "update"):
            self.root.update()
        self.write_output(f"\nCopied file content: {relative}\n")

    def _build_output_panel(self, parent: Any) -> None:
        import tkinter as tk
        from tkinter import ttk

        output_frame = tk.Frame(
            parent,
            bg=THEME.color_panel_bg,
            highlightbackground=THEME.color_border,
            highlightthickness=1,
            padx=THEME.section_padding,
            pady=THEME.section_padding,
        )
        self._register_group_frame("output", output_frame)
        output_frame.pack(fill=tk.BOTH, expand=True)
        output_header = tk.Frame(output_frame, bg=THEME.color_panel_bg)
        output_header.pack(fill=tk.X, pady=(0, 7))
        tk.Label(
            output_header,
            text="□  OUTPUT",
            bg=THEME.color_panel_bg,
            fg=THEME.color_muted_text,
            font=THEME.section_font,
            anchor=tk.W,
        ).pack(side=tk.LEFT)
        self.busy_status_var = tk.StringVar(value="Ready")
        tk.Label(
            output_header,
            textvariable=self.busy_status_var,
            bg=THEME.color_panel_bg,
            fg=THEME.color_muted_text,
            font=THEME.small_font,
        ).pack(side=tk.LEFT, padx=(10, 0))
        self.busy_progress = ttk.Progressbar(output_header, mode="indeterminate", length=120)
        self.busy_progress.pack(side=tk.LEFT, padx=(8, 0))
        clear_button = ttk.Button(output_header, text="Clear", command=self.clear_output)
        attach_tooltip(clear_button, "Clear the output panel.")
        clear_button.pack(side=tk.RIGHT)
        copy_button = ttk.Button(output_header, text="Copy", command=self.copy_output)
        attach_tooltip(copy_button, "Copy the full output panel content to the clipboard.")
        copy_button.pack(side=tk.RIGHT, padx=(0, 8))
        self.output = tk.Text(
            output_frame,
            height=THEME.output_height,
            wrap=tk.WORD,
            font=THEME.output_font,
            relief=tk.FLAT,
            bd=0,
            padx=6,
            pady=4,
        )
        self.output.pack(fill=tk.BOTH, expand=True)


    def write_output(self, text: str) -> None:
        self.output.insert("end", text)
        self.output.see("end")

    def _set_busy(self, text: str, *, running: bool) -> None:
        busy_var = getattr(self, "busy_status_var", None)
        progress = getattr(self, "busy_progress", None)
        if busy_var is not None:
            busy_var.set(text)
        if progress is not None:
            if running:
                progress.start(8)
            else:
                progress.stop()
        if hasattr(self.root, "update_idletasks"):
            self.root.update_idletasks()

    def clear_output(self) -> None:
        self.output.delete("1.0", "end")

    def copy_output(self) -> None:
        text = self.output.get("1.0", "end-1c")
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        if hasattr(self.root, "update"):
            self.root.update()


    def current_task_body(self) -> str:
        if self.task_text is None:
            return ""
        return self.task_text.get("1.0", "end").strip()

    def refresh_task_editor_buttons(self, _event: object | None = None) -> None:
        if self.task_send_button is None or self.task_read_button is None:
            return
        mode = self.current_communication_mode()
        if self.task_standard_command_button is not None:
            command_args = standard_command_args_for_communication_mode(mode)
            self.task_standard_command_button.configure(
                text=standard_command_label_for_communication_mode(mode),
                state="normal" if command_args else "disabled",
            )
        if self.task_open_terminal_button is not None:
            self.task_open_terminal_button.configure(state="normal")
        can_send = task_editor_send_enabled(
            self.current_task_body(),
            traffic_light_state=self.basic_view.traffic_light_state,
            communication_context_fresh=self.basic_view.communication_context_fresh,
            required_next_reply=self.basic_view.required_next_reply,
        )
        if self.task_editor_state == TaskEditorState.SENT:
            self.task_send_button.configure(state="disabled")
            self.task_read_button.configure(state="normal")
            self.task_status_var.set(
                f"Task carrier published to gui-transfer-tasks as mode {mode}. Send g/go in chat."
            )
            return
        if self.task_editor_state == TaskEditorState.BLOCKED:
            self.task_read_button.configure(state="disabled")
            self.task_send_button.configure(state="normal" if can_send else "disabled")
            if self.basic_view.required_next_reply == "d2":
                self.task_status_var.set("Blocked: send d2 and complete communication-rule ACK before mutation.")
            elif not self.current_task_body():
                self.task_status_var.set("Blocked: write a GUI task before sending.")
            else:
                self.task_status_var.set("Publish failed or is blocked. Inspect the Send output before retrying.")
            return
        self.task_read_button.configure(state="disabled")
        self.task_send_button.configure(state="normal" if can_send else "disabled")
        if command_description := standard_command_description_for_communication_mode(mode):
            self.task_status_var.set(command_description)
        if self.basic_view.required_next_reply == "d2":
            self.task_status_var.set("Blocked: send d2 and complete communication-rule ACK before mutation.")
        elif not self.current_task_body():
            self.task_status_var.set("Write a GUI task before sending.")
        elif not can_send:
            self.task_status_var.set("Blocked: gatekeeper must be READY and communication context fresh.")
        else:
            self.task_status_var.set("Ready to publish the GUI task carrier.")

    def _agentic_command(self, *parts: str) -> subprocess.CompletedProcess[str]:
        executable = self.project_root / ".venv" / "bin" / "agentic-kit"
        command = [str(executable) if executable.exists() else "agentic-kit", *parts]
        label = "agentic-kit " + " ".join(parts[:3])
        self._set_busy(f"Running: {label}", running=True)
        try:
            completed = subprocess.run(
                command,
                cwd=self.project_root,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
        except OSError as exc:
            completed = subprocess.CompletedProcess(command, 127, "", str(exc))
        self._set_busy("Done" if completed.returncode == 0 else "Blocked", running=False)
        return completed

    def show_initial_llm_prompt(self) -> None:
        completed = self._agentic_command("gui", "initial-llm-prompt", "--json")
        self.write_output("\n" + (completed.stdout or completed.stderr) + "\n")

    def open_transfer_terminal(self) -> None:
        plan = open_transfer_terminal_for_project(
            self.project_root,
            communication_mode=self.current_communication_mode(),
        )
        self.write_output("\n" + __import__("json").dumps(plan.as_json_data(), indent=2, sort_keys=True) + "\n")

    def run_mode_standard_command(self) -> None:
        command_args = standard_command_args_for_communication_mode(self.current_communication_mode())
        if not command_args:
            self.write_output("\nNo standard command is defined for Copy-and-Paste recovery mode.\n")
            return
        completed = self._agentic_command(*command_args)
        self.write_output("\n" + (completed.stdout or completed.stderr) + "\n")

    def send_user_task(self) -> None:
        body = self.current_task_body()
        if not task_editor_send_enabled(
            body,
            traffic_light_state=self.basic_view.traffic_light_state,
            communication_context_fresh=self.basic_view.communication_context_fresh,
            required_next_reply=self.basic_view.required_next_reply,
        ):
            self.task_editor_state = TaskEditorState.BLOCKED
            self.task_status_var.set("Blocked: task text, READY state, and fresh communication context are required.")
            self.refresh_task_editor_buttons()
            return
        tmp_path = self.project_root / "tmp" / "gui-task-editor-current-task.md"
        tmp_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path.write_text(body + "\n", encoding="utf-8")
        completed = self._agentic_command(
            "transfer",
            "submit-user-task",
            "--title",
            "GUI file-transfer task",
            "--body-file",
            str(tmp_path),
            "--communication-mode",
            self.current_communication_mode(),
            "--publish",
            "--json",
        )
        self.write_output("\n" + (completed.stdout or completed.stderr) + "\n")
        result_status = "PASS" if completed.returncode == 0 else "FAIL"
        remote_readable = False
        if completed.stdout:
            try:
                payload = __import__("json").loads(completed.stdout)
                remote_readable = bool(payload.get("remote_readable"))
            except ValueError:
                remote_readable = False
        self.task_editor_state = task_editor_state_after_send(
            result_status,
            remote_readable=remote_readable,
        )
        if self.task_editor_state == TaskEditorState.SENT and self.task_text is not None:
            self.task_text.configure(state="disabled")
        self.refresh_task_editor_buttons()

    def read_last_task_result(self) -> None:
        completed = self._agentic_command("transfer", "state", "--json")
        self.write_output("\n" + (completed.stdout or completed.stderr) + "\n")
        outbox_available = False
        if completed.stdout:
            try:
                payload = __import__("json").loads(completed.stdout)
                outbox_available = transfer_state_has_canonical_outbox_result(payload)
            except ValueError:
                outbox_available = False
        if completed.returncode == 0 and not outbox_available:
            self.task_editor_state = TaskEditorState.SENT
            self.task_status_var.set(
                f"No canonical transfer result yet at {CANONICAL_TRANSFER_OUTBOX_PATH.as_posix()}."
            )
            if self.task_send_button is not None:
                self.task_send_button.configure(state="disabled")
            if self.task_read_button is not None:
                self.task_read_button.configure(state="normal")
            return
        result_status = "PASS" if completed.returncode == 0 and outbox_available else "FAIL"
        self.task_editor_state = task_editor_state_after_read(result_status)
        if self.task_editor_state == TaskEditorState.IDLE and self.task_text is not None:
            self.task_text.configure(state="normal")
            self.task_text.delete("1.0", "end")
        self.refresh_task_editor_buttons()
