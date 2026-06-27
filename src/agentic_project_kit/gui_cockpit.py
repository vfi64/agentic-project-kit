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
    title_font: tuple[str, int, str] = ("TkDefaultFont", 14, "bold")
    section_font: tuple[str, int, str] = ("TkDefaultFont", 9, "bold")
    body_font: tuple[str, int] = ("TkDefaultFont", 10)
    small_font: tuple[str, int] = ("TkDefaultFont", 8)
    action_font: tuple[str, int, str] = ("TkDefaultFont", 10, "bold")
    output_font: tuple[str, int] = ("TkFixedFont", 10)
    recommended_font: tuple[str, int, str] = ("TkDefaultFont", 10, "bold")
    frame_padding: int = 16
    section_padding: int = 11
    output_height: int = 20
    action_rows_visible: int = 4
    task_text_height: int = 3
    window_geometry: str = "1180x760"
    sidebar_width: int = 320
    color_shell_bg: str = "#fbfbfa"
    color_panel_bg: str = "#ffffff"
    color_border: str = "#dddddd"
    color_muted_text: str = "#737373"
    color_read_only: str = "#dff3ef"
    color_bounded: str = "#fdf0d9"
    color_destructive: str = "#fbe6e6"
    color_ready_bg: str = "#d8f0d1"
    color_ready_border: str = "#68c36a"
    color_recommended_bg: str = "#d7eaff"
    color_button_outline: str = "#cfcfcf"
    action_card_height: int = 38
    action_column_width: int = 165
    what_it_does_column_width: int = 465
    safety_column_width: int = 90


THEME = GuiTheme()
HEADER_TEXT = "Agentic Project Kit — Cockpit"
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


@dataclass(frozen=True)
class GuiActionGroupView:
    group_id: str
    label: str
    description: str
    actions: tuple[GuiActionView, ...]


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


def action_group_for(action: GuiActionView) -> tuple[str, str, str]:
    if action.category in {"git", "workflow"} and action.safety == READ_ONLY:
        return ("routine", "Routine", "Frequent read-only orientation checks.")
    if action.category in {"dialog", "transfer"} or action.action_id == "workflow.go":
        return ("transfer", "Transfer", "File-transfer work-order and closeout actions.")
    if action.category in {"gate", "audit"}:
        return ("diagnostics", "Diagnostics", "Read-only checks for blockers and drift.")
    return ("advanced", "Advanced", "Release, handoff, and rule-refresh controls.")


def grouped_action_views(actions: list[GuiActionView] | tuple[GuiActionView, ...]) -> tuple[GuiActionGroupView, ...]:
    order = ("routine", "transfer", "diagnostics", "advanced")
    labels: dict[str, tuple[str, str]] = {}
    buckets: dict[str, list[GuiActionView]] = {}
    for action in actions:
        group_id, label, description = action_group_for(action)
        labels[group_id] = (label, description)
        buckets.setdefault(group_id, []).append(action)
    groups: list[GuiActionGroupView] = []
    for group_id in order:
        actions_in_group = tuple(buckets.get(group_id, ()))
        if not actions_in_group:
            continue
        label, description = labels[group_id]
        groups.append(GuiActionGroupView(group_id, label, description, actions_in_group))
    return tuple(groups)


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
    if view_model.recommended_action.kind == "select_action":
        return view_model.recommended_action.cockpit_action_id or None
    return None


def format_recommended_action(view_model: BasicCockpitViewModel) -> str:
    lines = [
        view_model.recommended_action.label,
        view_model.recommended_action.description,
        view_model.reason,
    ]
    if view_model.recovery_hint:
        lines.append(view_model.recovery_hint)
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
        f"recommended_action={view_model.recommended_action.label}",
        f"recommended_action_kind={view_model.recommended_action.kind}",
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
        self.root.geometry(THEME.window_geometry)
        if hasattr(self.root, "minsize"):
            self.root.minsize(1040, 680)
        self.selected_action_id_value: str | None = None

        shell = tk.Frame(
            root,
            bg=THEME.color_shell_bg,
            highlightbackground=THEME.color_border,
            highlightthickness=1,
        )
        shell.pack(fill=tk.BOTH, expand=True, padx=14, pady=14)

        self._build_header(shell)

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
        self._build_action_cards(main_area)
        self._build_task_editor(main_area)
        self._build_output_panel(main_area)

        self.write_output(format_basic_cockpit_summary(self.basic_view) + "\n")

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

    def _section_heading(self, parent: Any, text: str) -> None:
        import tkinter as tk

        tk.Label(
            parent,
            text=text.upper(),
            bg=THEME.color_panel_bg,
            fg=THEME.color_muted_text,
            font=THEME.section_font,
            anchor=tk.W,
        ).pack(fill=tk.X, pady=(0, 7))

    def _detail_row(self, parent: Any, label: str, value: str, *, value_color: str = "#1f1f1f") -> None:
        import tkinter as tk

        row = tk.Frame(parent, bg=THEME.color_panel_bg)
        row.pack(fill=tk.X, pady=2)
        label_widget = tk.Label(row, text=label, bg=THEME.color_panel_bg, fg="#4a4a4a", font=THEME.body_font)
        label_widget.pack(side=tk.LEFT)
        value_widget = tk.Label(row, text=value, bg=THEME.color_panel_bg, fg=value_color, font=THEME.body_font)
        value_widget.pack(side=tk.RIGHT)
        if label == "d2 pending":
            tooltip = (
                "d2 means a communication-rule refresh is pending. The assistant must read "
                "the remote rule capsule and return RULE_REFRESH_ACK before mutation."
            )
            attach_tooltip(label_widget, tooltip)
            attach_tooltip(value_widget, tooltip)

    def _build_sidebar(self, sidebar: Any) -> None:
        import tkinter as tk
        from tkinter import ttk

        ready_card = tk.Frame(
            sidebar,
            bg=THEME.color_ready_bg if self.basic_view.traffic_light_color == "green" else "#fff8dc",
            highlightbackground=THEME.color_ready_border,
            highlightthickness=1,
            padx=12,
            pady=12,
        )
        ready_card.pack(fill=tk.X, pady=(0, 18))

        ready_row = tk.Frame(ready_card, bg=ready_card["bg"])
        ready_row.pack(fill=tk.X)
        light = tk.Canvas(ready_row, width=17, height=17, bg=ready_card["bg"], highlightthickness=0)
        light.create_oval(
            3,
            3,
            14,
            14,
            fill=traffic_light_fill(self.basic_view.traffic_light_color),
            outline=traffic_light_fill(self.basic_view.traffic_light_color),
        )
        light.pack(side=tk.LEFT, padx=(0, 9))
        tk.Label(
            ready_row,
            text=traffic_light_state_label(self.basic_view.traffic_light_state).split(" ")[0],
            bg=ready_card["bg"],
            fg="#08775f",
            font=("TkDefaultFont", 13, "bold"),
        ).pack(side=tk.LEFT)
        tk.Label(
            ready_card,
            text=self.basic_view.reason,
            bg=ready_card["bg"],
            fg="#006b50",
            font=THEME.body_font,
            anchor=tk.W,
            justify=tk.LEFT,
            wraplength=255,
        ).pack(fill=tk.X, pady=(12, 0))

        self._build_recommended_card(sidebar)

        self._section_heading(sidebar, "Status Detail")
        self._detail_row(sidebar, "Worktree", "dirty" if "dirty" in self.basic_view.reason.lower() else "clean", value_color="#006b00")
        self._detail_row(sidebar, "Mutation", "allowed" if self.basic_view.mutation_allowed else "guarded")
        self._detail_row(sidebar, "d2 pending", "yes" if self.basic_view.required_next_reply == "d2" else "no")
        version = self._package_version()
        self._detail_row(sidebar, "Version", version)

        tk.Frame(sidebar, height=19, bg=THEME.color_panel_bg).pack(fill=tk.X)
        self._section_heading(sidebar, "Transfer Mode")
        self.mode_var = tk.StringVar(
            value=selected_communication_mode_option(self.basic_view.communication_modes)
        )
        mode_select = ttk.Combobox(
            sidebar,
            textvariable=self.mode_var,
            values=communication_mode_option_values(self.basic_view.communication_modes),
            state="readonly",
            width=24,
            font=THEME.body_font,
        )
        mode_select.pack(fill=tk.X)
        attach_tooltip(
            mode_select,
            "Select the communication mode. File Transfer is the standard path; Copy-and-Paste is a recovery fallback.",
        )
        self.mode_explanation_var = tk.StringVar(
            value=communication_mode_explanation(self.basic_view.communication_mode)
        )
        tk.Label(
            sidebar,
            textvariable=self.mode_explanation_var,
            anchor=tk.W,
            justify=tk.LEFT,
            bg=THEME.color_panel_bg,
            fg=THEME.color_muted_text,
            font=THEME.small_font,
            wraplength=255,
        ).pack(fill=tk.X, pady=(7, 0))
        mode_select.bind("<<ComboboxSelected>>", self.update_mode_explanation)

        tk.Frame(sidebar, height=18, bg=THEME.color_panel_bg).pack(fill=tk.X)
        self._section_heading(sidebar, "Access Level")
        self.access_level_var = tk.StringVar(value=self.basic_view.access_level)
        access_select = ttk.Combobox(
            sidebar,
            textvariable=self.access_level_var,
            values=access_level_option_values(),
            state="readonly",
            width=24,
            font=THEME.body_font,
        )
        access_select.pack(fill=tk.X)
        attach_tooltip(
            access_select,
            "Basic shows routine actions. Advanced adds release and rules. Maintainer adds deep audits. Access level does not grant permission.",
        )
        self.access_level_explanation_var = tk.StringVar(
            value=self.basic_view.access_level_explanation
        )
        tk.Label(
            sidebar,
            textvariable=self.access_level_explanation_var,
            anchor=tk.W,
            justify=tk.LEFT,
            bg=THEME.color_panel_bg,
            fg=THEME.color_muted_text,
            font=THEME.small_font,
            wraplength=255,
        ).pack(fill=tk.X, pady=(7, 0))
        access_select.bind("<<ComboboxSelected>>", self.update_access_level)

        tk.Frame(sidebar, height=10, bg=THEME.color_panel_bg).pack(fill=tk.X, expand=True)

    def _build_recommended_card(self, sidebar: Any) -> None:
        import tkinter as tk

        action = self.basic_view.recommended_action
        card = tk.Frame(
            sidebar,
            bg=THEME.color_recommended_bg,
            highlightbackground="#7eb1f1",
            highlightthickness=1,
            padx=11,
            pady=10,
        )
        card.pack(fill=tk.X, pady=(0, 18))
        tk.Label(
            card,
            text="RECOMMENDED NEXT",
            bg=THEME.color_recommended_bg,
            fg="#174ea6",
            font=THEME.section_font,
            anchor=tk.W,
        ).pack(fill=tk.X, pady=(0, 6))
        recommended = tk.Button(
            card,
            text=f"□  {action.label}",
            font=THEME.recommended_font,
            bg="#c5ddfb",
            fg="#174ea6",
            activebackground="#c5ddfb",
            relief=tk.GROOVE,
            bd=1,
            command=self.run_recommended_action,
            anchor=tk.W,
            padx=12,
            pady=8,
        )
        attach_tooltip(recommended, action.tooltip)
        recommended.pack(fill=tk.X)
        tk.Label(
            card,
            text=action.description,
            bg=THEME.color_recommended_bg,
            fg="#174ea6",
            font=THEME.small_font,
            anchor=tk.W,
            justify=tk.LEFT,
            wraplength=255,
        ).pack(fill=tk.X, pady=(7, 0))
        if self.basic_view.recovery_hint:
            tk.Label(
                card,
                text=self.basic_view.recovery_hint,
                bg=THEME.color_recommended_bg,
                fg="#5f2f00" if self.basic_view.traffic_light_color == "yellow" else "#8a1f11",
                font=THEME.small_font,
                anchor=tk.W,
                justify=tk.LEFT,
                wraplength=255,
            ).pack(fill=tk.X, pady=(5, 0))

    def _package_version(self) -> str:
        try:
            from agentic_project_kit import __version__
        except ImportError:
            return "unknown"
        return __version__

    def _recommended_button_label(self) -> str:
        if self.recovery_action_id:
            action = self.action_view_by_id(self.recovery_action_id)
            return action.label if action is not None else self.recovery_action_id
        return "Run next work order"

    def _build_action_cards(self, parent: Any) -> None:
        import tkinter as tk
        from tkinter import ttk

        self._section_heading(parent, "Actions")
        action_scroll_shell = tk.Frame(parent, bg=THEME.color_panel_bg)
        action_scroll_shell.pack(fill=tk.X)
        self.action_card_canvas = tk.Canvas(
            action_scroll_shell,
            bg=THEME.color_panel_bg,
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
        self.action_card_canvas.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.action_card_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.action_card_widgets: dict[str, Any] = {}
        self.populate_action_tree()

        button_row = tk.Frame(parent, bg=THEME.color_panel_bg)
        button_row.pack(fill=tk.X, pady=(10, 15))
        inspect_button = ttk.Button(button_row, text="Inspect", command=self.inspect_selected)
        attach_tooltip(inspect_button, "Show metadata, command, and safety details for the selected action.")
        inspect_button.pack(side=tk.LEFT, padx=(0, 9))
        run_button = ttk.Button(button_row, text="Run read-only", command=self.run_selected_read_only)
        attach_tooltip(run_button, "Run only selected read-only cockpit actions through the shared cockpit layer.")
        run_button.pack(side=tk.LEFT, padx=(0, 9))

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

    def load_recovery_action(self) -> None:
        if self.recovery_action_id is None:
            return
        self._select_action(self.recovery_action_id)
        action = self.action_view_by_id(self.recovery_action_id)
        label = action.label if action is not None else self.recovery_action_id
        self.write_output(f"\nRecovery action loaded: {label}. Inspect or run read-only manually.\n")

    def run_recommended_action(self) -> None:
        action = self.basic_view.recommended_action
        if action.kind == "run_button" and action.command_id:
            self.run_basic_action(action.command_id)
            return
        if action.kind == "select_action" and action.cockpit_action_id:
            self._select_action(action.cockpit_action_id)
            label = action.label
            self.write_output(f"\nRecommended action loaded: {label}. Inspect or run read-only manually.\n")
            return
        message = self.basic_view.recovery_hint or action.description
        self.write_output(f"\nRecommended next: {message}\n")

    def update_mode_explanation(self, _event: object | None = None) -> None:
        selected = self.current_communication_mode()
        self.mode_explanation_var.set(communication_mode_explanation(selected))
        self.refresh_task_editor_buttons()

    def current_communication_mode(self) -> str:
        option = self.mode_var.get()
        return next(
            (
                mode.mode_id
                for mode in self.basic_view.communication_modes
                if f"{mode.label}: {mode.role}" == option
            ),
            self.basic_view.communication_mode,
        )

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
