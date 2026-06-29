from __future__ import annotations

from agentic_project_kit.gui_tk_widgets import (
    attach_tooltip,
    communication_mode_example,
    communication_mode_explanation,
    communication_mode_option_label,
    communication_mode_option_values,
    constrain_tooltip_position,
    maximize_root_window,
    selected_communication_mode_option,
    TOOLTIP_WRAP_LENGTH,
    traffic_light_fill,
    traffic_light_state_label,
)
from agentic_project_kit.gui_communication_modes import communication_mode_definitions
from agentic_project_kit.gui_viewmodel import CommunicationModeViewModel


class FakeWidget:
    def __init__(self) -> None:
        self.bound_events: dict[str, object] = {}
        self.bind_counts: dict[str, int] = {}

    def bind(self, event: str, callback: object) -> None:
        self.bound_events[event] = callback
        self.bind_counts[event] = self.bind_counts.get(event, 0) + 1


class FakeRoot:
    def __init__(self, *, width: int = 1440, height: int = 900) -> None:
        self.width = width
        self.height = height
        self.geometry_calls: list[str] = []

    def winfo_screenwidth(self) -> int:
        return self.width

    def winfo_screenheight(self) -> int:
        return self.height

    def geometry(self, value: str) -> None:
        self.geometry_calls.append(value)


def test_traffic_light_fill_maps_supported_colors() -> None:
    assert traffic_light_fill("green") == "#1f883d"
    assert traffic_light_fill("yellow") == "#bf8700"
    assert traffic_light_fill("red") == "#cf222e"
    assert traffic_light_fill("gray") == "#6e7781"
    assert traffic_light_fill("mystery") == "#6e7781"


def test_traffic_light_state_label_names_wait_for_d2() -> None:
    assert traffic_light_state_label("WAIT_FOR_D2") == "WAIT_FOR_D2 (yellow)"
    assert traffic_light_state_label("READY") == "READY (green)"


def test_communication_mode_explanation_file_transfer() -> None:
    text = communication_mode_explanation("file_transfer")
    example = communication_mode_example("file_transfer")

    assert "Normal mode" in text
    assert "g/go" in text
    assert "Example:" not in text
    assert "Example:" in example
    assert "agentic-kit transfer continue --json" in example


def test_communication_mode_explanation_remote() -> None:
    text = communication_mode_explanation("remote")
    example = communication_mode_example("remote")

    assert "PR/CI/GitHub" in text
    assert "bounded wrappers" in text
    assert "Example:" not in text
    assert "Example:" in example
    assert "agentic-kit transfer patch-cycle-status --json" in example


def test_communication_mode_explanation_copy_paste() -> None:
    text = communication_mode_explanation("copy_paste")
    example = communication_mode_example("copy_paste")

    assert "Recovery fallback" in text
    assert "Not the normal" in text
    assert "Example:" not in text
    assert "Example:" in example
    assert "complete recovery block" in example


def test_communication_mode_example_exists_for_each_mode() -> None:
    for definition in communication_mode_definitions():
        assert communication_mode_example(definition.mode_id) == definition.example
        assert communication_mode_example(definition.mode_id).startswith("Example:")


def test_communication_mode_option_values_are_deterministic() -> None:
    modes = (
        CommunicationModeViewModel("file_transfer", "File Transfer", "Standard", True, True, ""),
        CommunicationModeViewModel("remote", "Remote", "GitHub/PR/CI", False, False, ""),
    )

    assert communication_mode_option_label(modes[0]) == "File Transfer: Standard"
    assert communication_mode_option_values(modes) == (
        "File Transfer: Standard",
        "Remote: GitHub/PR/CI",
    )
    assert selected_communication_mode_option(modes) == "File Transfer: Standard"


def test_attach_tooltip_records_text_and_binds_hover_events() -> None:
    widget = FakeWidget()

    returned = attach_tooltip(widget, "Helpful text")

    assert returned is widget
    assert widget._agentic_tooltip_text == "Helpful text"
    assert widget._agentic_tooltip.wraplength == TOOLTIP_WRAP_LENGTH
    assert "<Enter>" in widget.bound_events
    assert "<Leave>" in widget.bound_events


def test_attach_tooltip_reuses_existing_tooltip_and_updates_text() -> None:
    widget = FakeWidget()
    first = attach_tooltip(widget, "First")._agentic_tooltip

    attach_tooltip(widget, "Second")

    assert widget._agentic_tooltip_text == "Second"
    assert widget._agentic_tooltip is first
    assert widget._agentic_tooltip.text == "Second"


def test_repeated_attach_tooltip_binds_hover_events_once() -> None:
    widget = FakeWidget()

    attach_tooltip(widget, "First")
    attach_tooltip(widget, "Second")
    attach_tooltip(widget, "Third")

    assert widget.bind_counts["<Enter>"] == 1
    assert widget.bind_counts["<Leave>"] == 1


def test_constrain_tooltip_position_keeps_tooltip_inside_right_edge() -> None:
    x, y = constrain_tooltip_position(
        x=1180,
        y=50,
        width=320,
        height=80,
        screen_width=1280,
        screen_height=800,
    )

    assert x == 948
    assert y == 50


def test_constrain_tooltip_position_keeps_margin_for_small_screens() -> None:
    x, y = constrain_tooltip_position(
        x=-100,
        y=900,
        width=800,
        height=500,
        screen_width=640,
        screen_height=480,
    )

    assert x == 12
    assert y == 12


def test_maximize_root_window_uses_screen_size() -> None:
    root = FakeRoot(width=1440, height=900)

    maximize_root_window(root, fallback_geometry="1180x760")

    assert root.geometry_calls == ["1440x900+0+0"]


def test_maximize_root_window_falls_back_for_invalid_screen_size() -> None:
    root = FakeRoot(width=0, height=0)

    maximize_root_window(root, fallback_geometry="1180x760")

    assert root.geometry_calls == ["1180x760"]
