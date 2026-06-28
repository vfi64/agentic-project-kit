from __future__ import annotations

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

        task_frame = tk.Frame(
            parent,
            bg=THEME.color_panel_bg,
            highlightbackground=THEME.color_border,
            highlightthickness=1,
            padx=THEME.section_padding,
            pady=THEME.section_padding,
        )
        task_frame.pack(fill=tk.X, pady=(0, 12))
        heading_row = tk.Frame(task_frame, bg=THEME.color_panel_bg)
        heading_row.pack(fill=tk.X)
        tk.Label(
            heading_row,
            text="File transfer task",
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
        self.task_open_terminal_button = ttk.Button(
            task_button_row,
            text="Open local terminal",
            command=self.open_transfer_terminal,
        )
        attach_tooltip(
            self.task_open_terminal_button,
            "Open the operating-system terminal for the currently selected transfer mode.",
        )
        self.task_open_terminal_button.pack(side=tk.LEFT, padx=(0, 9))
        self.task_standard_command_button = ttk.Button(
            task_button_row,
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
        return subprocess.run(
            command,
            cwd=self.project_root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

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
