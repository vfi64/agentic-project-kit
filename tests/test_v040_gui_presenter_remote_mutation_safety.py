from __future__ import annotations

from dataclasses import dataclass

from agentic_project_kit.gui_action_renderer import render_action_row
from agentic_project_kit.gui_dry_run import render_result
from agentic_project_kit.gui_dry_run import run_gui_dry_run
from agentic_project_kit.gui_presenter import build_no_window_presenter_result
from agentic_project_kit.gui_viewmodel import action_to_view_model


@dataclass(frozen=True)
class Action:
    name: str
    safety_class: str
    description: str


def test_remote_mutation_action_is_disabled_and_confirmation_required_in_viewmodel():
    vm = action_to_view_model(Action("agent-run", "remote-mutation", "Run agent command"))
    assert vm.enabled is False
    assert vm.requires_confirmation is True


def test_remote_mutation_underscore_alias_is_normalized_and_blocked():
    vm = action_to_view_model(Action("agent-run", "remote_mutation", "Run agent command"))
    assert vm.enabled is False
    assert vm.requires_confirmation is True


def test_remote_mutation_action_is_not_rendered_as_enabled_no_confirm():
    presenter = build_no_window_presenter_result([Action("agent-run", "remote-mutation", "Run agent command")])
    assert "agent-run [remote-mutation; disabled; confirm]" in presenter.rendered
    assert "remote-mutation; enabled; no-confirm" not in presenter.rendered


def test_remote_mutation_can_be_enabled_only_by_explicit_future_flag():
    vm = action_to_view_model(Action("agent-run", "remote-mutation", "Run agent command"), destructive_actions_enabled=True)
    assert render_action_row(vm, 1) == "01. agent-run [remote-mutation; enabled; confirm] - Run agent command"


def test_gui_dry_run_has_no_remote_mutation_enabled_no_confirm_lines():
    output = render_result(run_gui_dry_run())
    assert "remote-mutation; enabled; no-confirm" not in output
    assert "remote-mutation; disabled; confirm" in output
