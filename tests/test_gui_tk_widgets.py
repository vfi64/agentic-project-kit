from __future__ import annotations

from agentic_project_kit.gui_tk_widgets import (
    attach_tooltip,
    communication_mode_option_label,
    communication_mode_option_values,
    selected_communication_mode_option,
    traffic_light_fill,
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
