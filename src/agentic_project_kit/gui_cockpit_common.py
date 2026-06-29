from __future__ import annotations

from dataclasses import dataclass

from agentic_project_kit.cockpit import BOUNDED, DESTRUCTIVE, READ_ONLY
from agentic_project_kit.gui_tk_widgets import traffic_light_state_label
from agentic_project_kit.gui_viewmodel import BasicCockpitViewModel


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
    action_list_width: int = 430
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
    action_card_height: int = 23
    action_column_width: int = 165
    what_it_does_column_width: int = 465
    safety_column_width: int = 90


THEME = GuiTheme()
HEADER_TEXT = "Agentic Project Kit — Cockpit"
ACTION_TREE_COLUMNS = ("action", "what_it_does", "safety")
RECOVERY_ACTION_ID = "gate.doctor"


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
