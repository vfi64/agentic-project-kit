from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from agentic_project_kit.cockpit import READ_ONLY, CockpitAction, CockpitActionResult, cockpit_actions, run_cockpit_action
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
        f"mutation_allowed={str(view_model.mutation_allowed).lower()}",
        f"next_safe_action={view_model.next_safe_action}",
        f"reason={view_model.reason}",
        "buttons=" + ",".join(button.command_id for button in view_model.buttons),
    ]
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
        self.root.geometry("1120x760")

        frame = ttk.Frame(root, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        title = ttk.Label(frame, text="Basic Cockpit", font=("TkDefaultFont", 16, "bold"))
        title.pack(anchor=tk.W)

        status_frame = ttk.LabelFrame(frame, text="State", padding=8)
        status_frame.pack(fill=tk.X, pady=(4, 8))
        status_text = (
            f"{self.basic_view.traffic_light_state} ({self.basic_view.traffic_light_color}) | "
            f"mode={self.basic_view.communication_mode} | "
            f"next={self.basic_view.next_safe_action}"
        )
        ttk.Label(status_frame, text=status_text, anchor=tk.W, wraplength=980).pack(fill=tk.X)
        ttk.Label(status_frame, text=self.basic_view.reason, anchor=tk.W, wraplength=980).pack(
            fill=tk.X, pady=(4, 0)
        )

        mode_row = ttk.Frame(status_frame)
        mode_row.pack(fill=tk.X, pady=(6, 0))
        for mode in self.basic_view.communication_modes:
            marker = "[x]" if mode.selected else "[ ]"
            ttk.Label(mode_row, text=f"{marker} {mode.label}: {mode.role}").pack(
                side=tk.LEFT, padx=(0, 12)
            )

        basic_buttons = ttk.LabelFrame(frame, text="Basic Actions", padding=8)
        basic_buttons.pack(fill=tk.X, pady=(0, 8))
        for button in self.basic_view.buttons:
            state = tk.NORMAL if button.enabled else tk.DISABLED
            ttk.Button(
                basic_buttons,
                text=button.label,
                state=state,
                command=lambda command_id=button.command_id: self.run_basic_action(command_id),
                width=22,
            ).pack(side=tk.LEFT, padx=(0, 8), pady=1)

        columns = ("label", "category", "safety", "command")
        self.tree = ttk.Treeview(frame, columns=columns, show="headings", height=12)
        self.tree.heading("label", text="Action")
        self.tree.heading("category", text="Category")
        self.tree.heading("safety", text="Safety")
        self.tree.heading("command", text="Command")
        self.tree.column("label", width=190)
        self.tree.column("category", width=100)
        self.tree.column("safety", width=100)
        self.tree.column("command", width=610)
        self.tree.pack(fill=tk.BOTH, expand=False)

        for action in self.actions:
            self.tree.insert("", tk.END, iid=action.action_id, values=(action.label, action.category, action.safety, " ".join(action.command)))

        button_row = ttk.Frame(frame)
        button_row.pack(fill=tk.X, pady=8)
        ttk.Button(button_row, text="Inspect selected", command=self.inspect_selected).pack(side=tk.LEFT)
        ttk.Button(button_row, text="Run selected read-only", command=self.run_selected_read_only).pack(side=tk.LEFT, padx=8)
        ttk.Button(button_row, text="Clear output", command=self.clear_output).pack(side=tk.LEFT)

        output_label = ttk.Label(frame, text="Output")
        output_label.pack(anchor=tk.W)
        self.output = tk.Text(frame, height=16, wrap=tk.WORD)
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
