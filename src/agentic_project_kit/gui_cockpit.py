from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess
from typing import Any

from agentic_project_kit.cockpit import READ_ONLY, CockpitAction, CockpitActionResult, cockpit_actions, run_cockpit_action
from agentic_project_kit.gui_task_editor import (
    TaskEditorState,
    task_editor_send_enabled,
    task_editor_state_after_read,
    task_editor_state_after_send,
    task_editor_visible_for_mode,
)
from agentic_project_kit.gui_tk_widgets import (
    attach_tooltip,
    communication_mode_explanation,
    communication_mode_option_values,
    selected_communication_mode_option,
    traffic_light_fill,
    traffic_light_state_label,
)
from agentic_project_kit.gui_tkinter_shell import run_basic_cockpit_button
from agentic_project_kit.gui_viewmodel import BasicCockpitViewModel, build_basic_cockpit_view_model


@dataclass(frozen=True)
class GuiActionView:
    action_id: str
    label: str
    category: str
    safety: str
    command: tuple[str, ...]
    description: str
    can_run_by_default: bool
    structured_explanation: str | None = None


STRUCTURED_ACTION_EXPLANATIONS = {
    "git.status": (
        "PURPOSE: Show local repository dirty state.\n"
        "EFFECT: Reads git status only.\n"
        "WHEN: Use before any mutation or PR closeout.\n"
        "BLOCKED WHEN: Git status cannot run.\n"
        "AFTER PASS: Continue with the next safe action.\n"
        "AFTER FAIL: Diagnose repository access."
    ),
    "workflow.state": (
        "PURPOSE: Show workflow and gatekeeper readiness.\n"
        "EFFECT: Reads workflow state only.\n"
        "WHEN: Use when deciding whether the GUI may proceed.\n"
        "BLOCKED WHEN: Workflow state files are unreadable.\n"
        "AFTER PASS: Continue with the recommended action.\n"
        "AFTER FAIL: Preserve evidence and diagnose workflow state."
    ),
    "dialog.rn": (
        "PURPOSE: Run the next file-transfer work order through the wrapper.\n"
        "EFFECT: Performs bounded local workflow mutation.\n"
        "WHEN: Use only after READY state and valid work order.\n"
        "BLOCKED WHEN: d2 is pending, state is dirty, or work order is invalid.\n"
        "AFTER PASS: Read the generated result/evidence.\n"
        "AFTER FAIL: Inspect the report before retrying."
    ),
    "dialog.rnc": (
        "PURPOSE: Close out the last run through the fixed closeout wrapper.\n"
        "EFFECT: Commits/pushes expected closeout paths when guarded.\n"
        "WHEN: Use after a successful bounded run.\n"
        "BLOCKED WHEN: Required evidence or clean state is missing.\n"
        "AFTER PASS: Continue with handoff or next slice.\n"
        "AFTER FAIL: Diagnose closeout evidence."
    ),
    "rules.communication-refresh": (
        "PURPOSE: Publish the current communication rule capsule.\n"
        "EFFECT: Writes generated rule artifacts and a local d2 pending state.\n"
        "WHEN: Use when the assistant must reload communication rules.\n"
        "BLOCKED WHEN: Local mutation is not safe.\n"
        "AFTER PASS: Send d2 and require machine-readable ACK.\n"
        "AFTER FAIL: Diagnose rule-refresh output."
    ),
}


def build_gui_action_views(actions: list[CockpitAction] | None = None) -> list[GuiActionView]:
    selected = actions if actions is not None else cockpit_actions()
    return [
        GuiActionView(
            action_id=action.action_id,
            label=action.label,
            category=action.category,
            safety=action.safety,
            command=action.command,
            description=action.description,
            can_run_by_default=action.safety == READ_ONLY,
            structured_explanation=STRUCTURED_ACTION_EXPLANATIONS.get(action.action_id),
        )
        for action in selected
    ]


SAFETY_EXPLANATIONS = {
    "read_only": "Safe default: this action may be executed from the GUI through the shared cockpit layer.",
    "bounded": "Blocked by default: bounded workflow actions require an explicit non-GUI allow path.",
    "destructive": "Blocked: destructive actions are not executable from the GUI cockpit.",
}


def explain_safety(safety: str) -> str:
    return SAFETY_EXPLANATIONS.get(safety, f"Blocked: unknown safety class {safety}.")


def format_action_details(action: GuiActionView) -> str:
    lines = [
        f"action_id={action.action_id}",
        f"label={action.label}",
        f"category={action.category}",
        f"safety={action.safety}",
        f"can_run_by_default={str(action.can_run_by_default).lower()}",
        "command=" + " ".join(action.command),
        f"description={action.description}",
        f"safety_explanation={explain_safety(action.safety)}",
    ]
    if action.structured_explanation:
        lines.extend(["", "structured_explanation:", action.structured_explanation])
    return "\n".join(lines)


def format_action_result(result: CockpitActionResult) -> str:
    lines = [
        f"action_id={result.action_id}",
        "status=" + ("completed" if result.executed else "blocked"),
        f"allowed={str(result.allowed).lower()}",
        f"executed={str(result.executed).lower()}",
        f"returncode={result.returncode}",
    ]
    if result.message:
        lines.append(result.message)
    if result.stdout:
        lines.extend(["", "stdout:", result.stdout])
    if result.stderr:
        lines.extend(["", "stderr:", result.stderr])
    return "\n".join(lines).rstrip()


def format_basic_cockpit_summary(view_model: BasicCockpitViewModel) -> str:
    lines = [
        "BASIC_COCKPIT",
        f"traffic_light_state={view_model.traffic_light_state}",
        f"traffic_light_color={view_model.traffic_light_color}",
        f"communication_mode={view_model.communication_mode}",
        f"communication_context_fresh={str(view_model.communication_context_fresh).lower()}",
        f"required_next_reply={view_model.required_next_reply or '<none>'}",
        f"mutation_allowed={str(view_model.mutation_allowed).lower()}",
        f"next_safe_action={view_model.next_safe_action}",
        f"reason={view_model.reason}",
        "buttons=" + ",".join(button.command_id for button in view_model.buttons),
    ]
    return "\n".join(lines)


def format_state_details(view_model: BasicCockpitViewModel) -> str:
    lines = [
        f"STATE: {traffic_light_state_label(view_model.traffic_light_state)}",
        f"REASON: {view_model.reason}",
        f"NEXT ACTION: {view_model.next_safe_action}",
    ]
    if view_model.required_next_reply == "d2":
        lines.extend(
            [
                "",
                "Communication Rules Refresh pending. Send 'd2' to the chat.",
                "The assistant must read the remote rule capsule and provide ACK before mutation.",
            ]
        )
    return "\n".join(lines)


class CockpitGui:
    def __init__(self, root: Any, project_root: Path | None = None) -> None:
        import tkinter as tk
        from tkinter import ttk

        self.root = root
        self.project_root = (project_root or Path(".")).resolve()
        self.actions = build_gui_action_views()
        self.basic_view = build_basic_cockpit_view_model(self.project_root)
        self.root.title("agentic-project-kit cockpit")
        self.root.geometry("1120x820")

        frame = ttk.Frame(root, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        title = ttk.Label(frame, text="Agentic-Project-Kit - Basic Cockpit", font=("TkDefaultFont", 16, "bold"))
        title.pack(anchor=tk.W)

        status_frame = ttk.LabelFrame(frame, text="State", padding=4)
        status_frame.pack(fill=tk.X, pady=(2, 4))

        traffic_row = ttk.Frame(status_frame)
        traffic_row.pack(fill=tk.X)
        traffic_light = tk.Canvas(traffic_row, width=18, height=18, highlightthickness=0)
        traffic_light.create_oval(
            3,
            3,
            15,
            15,
            fill=traffic_light_fill(self.basic_view.traffic_light_color),
            outline=traffic_light_fill(self.basic_view.traffic_light_color),
        )
        traffic_light.pack(side=tk.LEFT, padx=(0, 8))
        ttk.Label(
            traffic_row,
            text=traffic_light_state_label(self.basic_view.traffic_light_state),
            font=("TkDefaultFont", 12, "bold"),
        ).pack(side=tk.LEFT, padx=(0, 12))
        ttk.Label(
            traffic_row,
            text=f"Next: {self.basic_view.next_safe_action}",
            anchor=tk.W,
            wraplength=820,
        ).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Label(status_frame, text=self.basic_view.reason, anchor=tk.W, wraplength=980).pack(
            fill=tk.X, pady=(4, 0)
        )
        ttk.Label(
            status_frame,
            text=format_state_details(self.basic_view),
            anchor=tk.W,
            justify=tk.LEFT,
            wraplength=980,
        ).pack(fill=tk.X, pady=(3, 0))

        mode_row = ttk.Frame(status_frame)
        mode_row.pack(fill=tk.X, pady=(3, 0))
        ttk.Label(mode_row, text="Transfer mode").pack(side=tk.LEFT, padx=(0, 8))
        self.mode_var = tk.StringVar(
            value=selected_communication_mode_option(self.basic_view.communication_modes)
        )
        mode_select = ttk.Combobox(
            mode_row,
            textvariable=self.mode_var,
            values=communication_mode_option_values(self.basic_view.communication_modes),
            state="readonly",
            width=34,
        )
        mode_select.pack(side=tk.LEFT)
        attach_tooltip(
            mode_select,
            "Select the communication mode. File Transfer is the standard path; Copy-and-Paste is a recovery fallback.",
        )
        self.mode_explanation_var = tk.StringVar(
            value=communication_mode_explanation(self.basic_view.communication_mode)
        )
        ttk.Label(
            status_frame,
            textvariable=self.mode_explanation_var,
            anchor=tk.W,
            wraplength=980,
        ).pack(fill=tk.X, pady=(2, 0))
        mode_select.bind("<<ComboboxSelected>>", self.update_mode_explanation)

        basic_buttons = ttk.LabelFrame(frame, text="Basic Actions", padding=4)
        basic_buttons.pack(fill=tk.X, pady=(0, 4))
        for button in self.basic_view.buttons:
            state = tk.NORMAL if button.enabled else tk.DISABLED
            widget = ttk.Button(
                basic_buttons,
                text=button.label,
                state=state,
                command=lambda command_id=button.command_id: self.run_basic_action(command_id),
                width=18,
            )
            tooltip = button.tooltip
            if button.disabled_reason:
                tooltip = f"{tooltip} Disabled: {button.disabled_reason}"
            attach_tooltip(widget, tooltip)
            widget.pack(side=tk.LEFT, padx=(0, 8), pady=1)

        self.task_editor_state = TaskEditorState.IDLE
        self.task_status_var = tk.StringVar(value="Write a file-transfer task, then send it through the guarded wrapper.")
        if task_editor_visible_for_mode(self.basic_view.communication_mode):
            task_frame = ttk.LabelFrame(frame, text="File Transfer Task", padding=4)
            task_frame.pack(fill=tk.X, pady=(0, 4))
            self.task_text = tk.Text(task_frame, height=6, wrap=tk.WORD)
            self.task_text.pack(fill=tk.X, expand=False)
            self.task_text.bind("<KeyRelease>", self.refresh_task_editor_buttons)
            task_button_row = ttk.Frame(task_frame)
            task_button_row.pack(fill=tk.X, pady=(6, 0))
            self.initial_prompt_button = ttk.Button(
                task_button_row,
                text="Initial Prompt",
                command=self.show_initial_llm_prompt,
            )
            attach_tooltip(
                self.initial_prompt_button,
                "Render the one-time initial LLM prompt for file-transfer dialog setup.",
            )
            self.initial_prompt_button.pack(side=tk.LEFT, padx=(0, 8))
            self.task_send_button = ttk.Button(
                task_button_row,
                text="Send",
                command=self.send_user_task,
            )
            attach_tooltip(
                self.task_send_button,
                "Write the task through agentic-kit transfer submit-user-task. The current implementation reports local-only until published.",
            )
            self.task_send_button.pack(side=tk.LEFT, padx=(0, 8))
            self.task_read_button = ttk.Button(
                task_button_row,
                text="Read",
                command=self.read_last_task_result,
                state=tk.DISABLED,
            )
            attach_tooltip(
                self.task_read_button,
                "Read the current task carrier through agentic-kit transfer read-user-task --json.",
            )
            self.task_read_button.pack(side=tk.LEFT, padx=(0, 8))
            ttk.Label(
                task_frame,
                textvariable=self.task_status_var,
                anchor=tk.W,
                wraplength=980,
            ).pack(fill=tk.X, pady=(3, 0))
            self.refresh_task_editor_buttons()
        else:
            self.task_text = None
            self.initial_prompt_button = None
            self.task_send_button = None
            self.task_read_button = None

        columns = ("label", "category", "safety", "command")
        tree_frame = ttk.Frame(frame)
        tree_frame.pack(fill=tk.X, expand=False)
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=4)
        self.tree.heading("label", text="Action")
        self.tree.heading("category", text="Category")
        self.tree.heading("safety", text="Safety")
        self.tree.heading("command", text="Command")
        self.tree.column("label", width=190)
        self.tree.column("category", width=100)
        self.tree.column("safety", width=100)
        self.tree.column("command", width=610)
        tree_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.X, expand=True)
        tree_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree_scrollbar = tree_scrollbar

        for action in self.actions:
            self.tree.insert("", tk.END, iid=action.action_id, values=(action.label, action.category, action.safety, " ".join(action.command)))

        button_row = ttk.Frame(frame)
        button_row.pack(fill=tk.X, pady=8)
        inspect_button = ttk.Button(
            button_row, text="Inspect Selected", command=self.inspect_selected
        )
        attach_tooltip(inspect_button, "Show metadata, command, and safety details for the selected action.")
        inspect_button.pack(side=tk.LEFT)
        run_button = ttk.Button(
            button_row, text="Run Selected Read-Only", command=self.run_selected_read_only
        )
        attach_tooltip(run_button, "Run only selected read-only cockpit actions through the shared cockpit layer.")
        run_button.pack(side=tk.LEFT, padx=8)
        clear_button = ttk.Button(button_row, text="Clear Output", command=self.clear_output)
        attach_tooltip(clear_button, "Clear the output panel.")
        clear_button.pack(side=tk.LEFT)

        output_label = ttk.Label(frame, text="Output")
        output_label.pack(anchor=tk.W)
        self.output = tk.Text(frame, height=21, wrap=tk.WORD)
        self.output.pack(fill=tk.BOTH, expand=True)
        self.write_output(format_basic_cockpit_summary(self.basic_view) + "\n")

    def selected_action_id(self) -> str | None:
        selected = self.tree.selection()
        if not selected:
            return None
        return str(selected[0])

    def action_view_by_id(self, action_id: str) -> GuiActionView | None:
        for action in self.actions:
            if action.action_id == action_id:
                return action
        return None

    def write_output(self, text: str) -> None:
        self.output.insert("end", text)
        self.output.see("end")

    def clear_output(self) -> None:
        self.output.delete("1.0", "end")

    def update_mode_explanation(self, _event: object | None = None) -> None:
        option = self.mode_var.get()
        selected = next(
            (
                mode.mode_id
                for mode in self.basic_view.communication_modes
                if f"{mode.label}: {mode.role}" == option
            ),
            self.basic_view.communication_mode,
        )
        self.mode_explanation_var.set(communication_mode_explanation(selected))

    def current_task_body(self) -> str:
        if self.task_text is None:
            return ""
        return self.task_text.get("1.0", "end").strip()

    def refresh_task_editor_buttons(self, _event: object | None = None) -> None:
        if self.task_send_button is None or self.task_read_button is None:
            return
        can_send = task_editor_send_enabled(
            self.current_task_body(),
            traffic_light_state=self.basic_view.traffic_light_state,
            communication_context_fresh=self.basic_view.communication_context_fresh,
            required_next_reply=self.basic_view.required_next_reply,
        )
        if self.task_editor_state == TaskEditorState.SENT:
            self.task_send_button.configure(state="disabled")
            self.task_read_button.configure(state="normal")
            self.task_status_var.set("Task is remote-readable. Send 'g' or 'go' in chat, then use Read.")
            return
        self.task_read_button.configure(state="disabled")
        self.task_send_button.configure(state="normal" if can_send else "disabled")
        if self.basic_view.required_next_reply == "d2":
            self.task_status_var.set("Blocked: send d2 and complete communication-rule ACK before mutation.")
        elif not self.current_task_body():
            self.task_status_var.set("Write a file-transfer task before sending.")
        elif not can_send:
            self.task_status_var.set("Blocked: gatekeeper must be READY and communication context fresh.")
        else:
            self.task_status_var.set("Ready to send the file-transfer task.")

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
        elif result_status == "PASS":
            self.task_status_var.set("Task written locally only. Publish through the guarded transfer path before sending g/go.")
        self.refresh_task_editor_buttons()

    def read_last_task_result(self) -> None:
        completed = self._agentic_command("transfer", "read-user-task", "--json")
        self.write_output("\n" + (completed.stdout or completed.stderr) + "\n")
        result_status = "PASS" if completed.returncode == 0 else "FAIL"
        self.task_editor_state = task_editor_state_after_read(result_status)
        if self.task_editor_state == TaskEditorState.IDLE and self.task_text is not None:
            self.task_text.configure(state="normal")
            self.task_text.delete("1.0", "end")
        self.refresh_task_editor_buttons()

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
        result = run_cockpit_action(action_id, self.project_root, allow_bounded=False)
        self.write_output("\n" + format_action_result(result) + "\n")


def main() -> None:
    import tkinter as tk

    root = tk.Tk()
    CockpitGui(root)
    root.mainloop()
