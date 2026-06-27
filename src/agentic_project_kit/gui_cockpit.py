from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess
from typing import Any

from agentic_project_kit.access_levels import DEFAULT_ACCESS_LEVEL, normalize_access_level
from agentic_project_kit.cockpit import (
    BOUNDED,
    DESTRUCTIVE,
    READ_ONLY,
    CockpitAction,
    CockpitActionResult,
    run_cockpit_action,
)
from agentic_project_kit.gui_task_editor import (
    CANONICAL_TRANSFER_OUTBOX_PATH,
    TaskEditorState,
    task_editor_send_enabled,
    task_editor_state_after_read,
    task_editor_state_after_send,
    task_editor_visible_for_mode,
    transfer_state_has_canonical_outbox_result,
)
from agentic_project_kit.gui_tk_widgets import (
    access_level_option_values,
    attach_tooltip,
    communication_mode_explanation,
    communication_mode_option_values,
    selected_communication_mode_option,
    traffic_light_fill,
    traffic_light_state_label,
)
from agentic_project_kit.gui_tkinter_shell import run_basic_cockpit_button
from agentic_project_kit.gui_viewmodel import BasicCockpitViewModel, build_basic_cockpit_view_model
from agentic_project_kit.gui_viewmodel import cockpit_actions_for_access_level


@dataclass(frozen=True)
class GuiTheme:
    title_font: tuple[str, int, str] = ("TkDefaultFont", 16, "bold")
    section_font: tuple[str, int, str] = ("TkDefaultFont", 11, "bold")
    recommended_font: tuple[str, int, str] = ("TkDefaultFont", 13, "bold")
    frame_padding: int = 10
    section_padding: int = 8
    output_height: int = 21
    action_rows_visible: int = 4
    task_text_height: int = 6
    color_read_only: str = "#e8f3ea"
    color_bounded: str = "#fdf4e3"
    color_destructive: str = "#fbeaea"
    color_recommended_bg: str = "#eaf1fb"
    action_column_width: int = 220
    what_it_does_column_width: int = 620
    safety_column_width: int = 120


THEME = GuiTheme()
HEADER_TEXT = "Agentic-Project-Kit — Basic Cockpit"
ACTION_TREE_COLUMNS = ("action", "what_it_does", "safety")
SAFETY_SORT_ORDER = {READ_ONLY: 0, BOUNDED: 1, DESTRUCTIVE: 2}
RECOVERY_ACTION_ID = "gate.doctor"


@dataclass(frozen=True)
class GuiActionView:
    action_id: str
    label: str
    category: str
    safety: str
    command: tuple[str, ...]
    description: str
    short_description: str
    min_access_level: str
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


def build_gui_action_views(
    actions: list[CockpitAction] | None = None,
    *,
    access_level: str = DEFAULT_ACCESS_LEVEL,
) -> list[GuiActionView]:
    selected = cockpit_actions_for_access_level(actions, access_level=access_level)
    return [
        GuiActionView(
            action_id=action.action_id,
            label=action.label,
            category=action.category,
            safety=action.safety,
            command=action.command,
            description=action.description,
            short_description=action.short_description,
            min_access_level=action.min_access_level,
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


def ordered_action_views(
    actions: list[GuiActionView] | None = None,
    *,
    access_level: str = DEFAULT_ACCESS_LEVEL,
) -> list[GuiActionView]:
    selected = actions if actions is not None else build_gui_action_views(access_level=access_level)
    return sorted(
        selected,
        key=lambda action: (
            SAFETY_SORT_ORDER.get(action.safety, len(SAFETY_SORT_ORDER)),
            action.label.casefold(),
            action.action_id,
        ),
    )


def action_tree_columns() -> tuple[str, ...]:
    return ACTION_TREE_COLUMNS


def action_tree_visible_rows(theme: GuiTheme = THEME) -> int:
    return theme.action_rows_visible


def action_tree_tag_colors(theme: GuiTheme = THEME) -> dict[str, str]:
    return {
        READ_ONLY: theme.color_read_only,
        BOUNDED: theme.color_bounded,
        DESTRUCTIVE: theme.color_destructive,
    }


def action_tree_tag_for_safety(safety: str) -> str:
    return safety if safety in action_tree_tag_colors() else "unknown"


def recommended_recovery_action_id(view_model: BasicCockpitViewModel) -> str | None:
    if view_model.traffic_light_color == "red":
        return RECOVERY_ACTION_ID
    return None


def format_recommended_action(view_model: BasicCockpitViewModel) -> str:
    lines = [
        view_model.next_safe_action,
        view_model.reason,
    ]
    if recommended_recovery_action_id(view_model):
        lines.append("Recovery: load the diagnostic action without running it.")
    return "\n".join(lines)


def format_action_details(action: GuiActionView) -> str:
    lines = [
        f"action_id={action.action_id}",
        f"label={action.label}",
        f"category={action.category}",
        f"safety={action.safety}",
        f"can_run_by_default={str(action.can_run_by_default).lower()}",
        "command=" + " ".join(action.command),
        f"description={action.description}",
        f"short_description={action.short_description}",
        f"min_access_level={action.min_access_level}",
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
        f"access_level={view_model.access_level}",
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
        self.basic_view = build_basic_cockpit_view_model(self.project_root)
        self.actions = ordered_action_views(
            build_gui_action_views(access_level=self.basic_view.access_level)
        )
        self.recovery_action_id = recommended_recovery_action_id(self.basic_view)
        self.root.title(HEADER_TEXT)
        self.root.geometry("1120x820")

        frame = ttk.Frame(root, padding=THEME.frame_padding)
        frame.pack(fill=tk.BOTH, expand=True)

        title = ttk.Label(frame, text=HEADER_TEXT, font=THEME.title_font)
        title.pack(anchor=tk.W)

        recommended_frame = tk.LabelFrame(
            frame,
            text="Recommended Next Action",
            font=THEME.section_font,
            bg=THEME.color_recommended_bg,
            padx=THEME.section_padding,
            pady=THEME.section_padding,
        )
        recommended_frame.pack(fill=tk.X, pady=(4, 4))
        tk.Label(
            recommended_frame,
            text=self.basic_view.next_safe_action,
            font=THEME.recommended_font,
            bg=THEME.color_recommended_bg,
            anchor=tk.W,
            justify=tk.LEFT,
            wraplength=980,
        ).pack(fill=tk.X)
        tk.Label(
            recommended_frame,
            text=self.basic_view.reason,
            bg=THEME.color_recommended_bg,
            anchor=tk.W,
            justify=tk.LEFT,
            wraplength=980,
        ).pack(fill=tk.X, pady=(2, 0))
        if self.recovery_action_id is not None:
            recovery_action = self.action_view_by_id(self.recovery_action_id)
            recovery_label = recovery_action.label if recovery_action is not None else self.recovery_action_id
            tk.Label(
                recommended_frame,
                text=f"Recovery: load {recovery_label} for diagnostics. This does not run the action.",
                bg=THEME.color_recommended_bg,
                anchor=tk.W,
                justify=tk.LEFT,
                wraplength=980,
            ).pack(fill=tk.X, pady=(4, 0))
            recovery_button = ttk.Button(
                recommended_frame,
                text="Load Recovery Action",
                command=self.load_recovery_action,
            )
            attach_tooltip(
                recovery_button,
                "Select the recommended read-only diagnostic action without executing it.",
            )
            recovery_button.pack(anchor=tk.W, pady=(4, 0))

        status_frame = ttk.LabelFrame(frame, text="State", padding=THEME.section_padding)
        status_frame.pack(fill=tk.X, pady=(0, 4))

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
            font=THEME.section_font,
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

        access_row = ttk.Frame(status_frame)
        access_row.pack(fill=tk.X, pady=(3, 0))
        ttk.Label(access_row, text="Access level").pack(side=tk.LEFT, padx=(0, 8))
        self.access_level_var = tk.StringVar(value=self.basic_view.access_level)
        access_select = ttk.Combobox(
            access_row,
            textvariable=self.access_level_var,
            values=access_level_option_values(),
            state="readonly",
            width=18,
        )
        access_select.pack(side=tk.LEFT)
        attach_tooltip(
            access_select,
            "Basic shows routine actions. Advanced adds release and rules. Maintainer adds deep audits. Access level does not grant permission.",
        )
        self.access_level_explanation_var = tk.StringVar(
            value=self.basic_view.access_level_explanation
        )
        ttk.Label(
            status_frame,
            textvariable=self.access_level_explanation_var,
            anchor=tk.W,
            wraplength=980,
        ).pack(fill=tk.X, pady=(2, 0))
        access_select.bind("<<ComboboxSelected>>", self.update_access_level)

        basic_buttons = ttk.LabelFrame(frame, text="Basic Actions", padding=THEME.section_padding)
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
        self.task_status_var = tk.StringVar(value="Write a transfer order, then send it through the guarded wrapper.")
        if task_editor_visible_for_mode(self.basic_view.communication_mode):
            task_frame = ttk.LabelFrame(frame, text="Transfer Order", padding=THEME.section_padding)
            task_frame.pack(fill=tk.X, pady=(0, 4))
            self.task_text = tk.Text(task_frame, height=THEME.task_text_height, wrap=tk.WORD)
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
                "Publish the canonical agentic-kit transfer inbox file through agentic-kit transfer submit-user-task --publish.",
            )
            self.task_send_button.pack(side=tk.LEFT, padx=(0, 8))
            self.task_read_button = ttk.Button(
                task_button_row,
                text="Read Result",
                command=self.read_last_task_result,
                state=tk.DISABLED,
            )
            attach_tooltip(
                self.task_read_button,
                "Read canonical transfer state through agentic-kit transfer state --json; the local result is .agentic/transfer/outbox/last_result.txt.",
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

        tree_frame = ttk.Frame(frame)
        tree_frame.pack(fill=tk.X, expand=False)
        self.tree = ttk.Treeview(
            tree_frame,
            columns=ACTION_TREE_COLUMNS,
            show="headings",
            height=THEME.action_rows_visible,
        )
        self.tree.heading("action", text="Action")
        self.tree.heading("what_it_does", text="What it does")
        self.tree.heading("safety", text="Safety")
        self.tree.column("action", width=THEME.action_column_width)
        self.tree.column("what_it_does", width=THEME.what_it_does_column_width)
        self.tree.column("safety", width=THEME.safety_column_width)
        for tag, color in action_tree_tag_colors().items():
            self.tree.tag_configure(tag, background=color)
        tree_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.X, expand=True)
        tree_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree_scrollbar = tree_scrollbar

        self.populate_action_tree()

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
        self.output = tk.Text(frame, height=THEME.output_height, wrap=tk.WORD)
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

    def populate_action_tree(self) -> None:
        import tkinter as tk

        self.tree.delete(*self.tree.get_children())
        for action in self.actions:
            self.tree.insert(
                "",
                tk.END,
                iid=action.action_id,
                values=(action.label, action.short_description, action.safety),
                tags=(action_tree_tag_for_safety(action.safety),),
            )

    def write_output(self, text: str) -> None:
        self.output.insert("end", text)
        self.output.see("end")

    def clear_output(self) -> None:
        self.output.delete("1.0", "end")

    def load_recovery_action(self) -> None:
        if self.recovery_action_id is None:
            return
        self.tree.selection_set(self.recovery_action_id)
        self.tree.focus(self.recovery_action_id)
        self.tree.see(self.recovery_action_id)
        action = self.action_view_by_id(self.recovery_action_id)
        label = action.label if action is not None else self.recovery_action_id
        self.write_output(f"\nRecovery action loaded: {label}. Inspect or run read-only manually.\n")

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
            self.task_status_var.set("Transfer order published to gui-transfer-tasks. Send g/go in chat.")
            return
        self.task_read_button.configure(state="disabled")
        self.task_send_button.configure(state="normal" if can_send else "disabled")
        if self.basic_view.required_next_reply == "d2":
            self.task_status_var.set("Blocked: send d2 and complete communication-rule ACK before mutation.")
        elif not self.current_task_body():
            self.task_status_var.set("Write a transfer order before sending.")
        elif not can_send:
            self.task_status_var.set("Blocked: gatekeeper must be READY and communication context fresh.")
        else:
            self.task_status_var.set("Ready to send the transfer order.")

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
        elif result_status == "PASS":
            self.task_status_var.set("Transfer order written locally only. Publish through the guarded transfer path before sending g/go.")
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


def main() -> None:
    import tkinter as tk

    root = tk.Tk()
    CockpitGui(root)
    root.mainloop()
