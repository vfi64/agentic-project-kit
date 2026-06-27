from __future__ import annotations

from agentic_project_kit.gui_tk_widgets import (
    attach_tooltip,
    communication_mode_explanation,
    communication_mode_option_label,
    communication_mode_option_values,
    selected_communication_mode_option,
    traffic_light_fill,
    traffic_light_state_label,
)
from agentic_project_kit.gui_viewmodel import CommunicationModeViewModel


class FakeWidget:
    def __init__(self) -> None:
        self.bound_events: dict[str, object] = {}

    def bind(self, event: str, callback: object) -> None:
        self.bound_events[event] = callback


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

    assert "Normal mode" in text
    assert "g/go" in text


def test_communication_mode_explanation_remote() -> None:
    text = communication_mode_explanation("remote")

    assert "PR/CI/GitHub" in text
    assert "bounded wrappers" in text


def test_communication_mode_explanation_copy_paste() -> None:
    text = communication_mode_explanation("copy_paste")

    assert "Recovery fallback" in text
    assert "Not the normal" in text


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
    assert "<Enter>" in widget.bound_events
    assert "<Leave>" in widget.bound_events


def test_attach_tooltip_replaces_existing_tooltip() -> None:
    widget = FakeWidget()
    first = attach_tooltip(widget, "First")._agentic_tooltip

    attach_tooltip(widget, "Second")

    assert widget._agentic_tooltip_text == "Second"
    assert widget._agentic_tooltip is not first
