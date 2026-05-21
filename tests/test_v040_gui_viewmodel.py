from __future__ import annotations

from dataclasses import dataclass

from agentic_project_kit.gui_viewmodel import action_to_view_model
from agentic_project_kit.gui_viewmodel import build_gui_controller_view_model


@dataclass(frozen=True)
class DummyAction:
    name: str
    safety_class: str
    description: str = ""


def test_action_to_view_model_keeps_read_only_enabled():
    vm = action_to_view_model(DummyAction("status", "read_only", "Show status"))
    assert vm.name == "status"
    assert vm.safety_class == "read_only"
    assert vm.description == "Show status"
    assert vm.enabled is True
    assert vm.requires_confirmation is False


def test_action_to_view_model_disables_destructive_by_default():
    vm = action_to_view_model(DummyAction("publish", "destructive", "Publish release"))
    assert vm.enabled is False
    assert vm.requires_confirmation is True


def test_action_to_view_model_can_enable_destructive_actions_explicitly():
    vm = action_to_view_model(
        DummyAction("publish", "destructive", "Publish release"),
        destructive_actions_enabled=True,
    )
    assert vm.enabled is True
    assert vm.requires_confirmation is True


def test_build_gui_controller_view_model_is_deterministic():
    vm = build_gui_controller_view_model(
        [
            DummyAction("status", "read_only", "Show status"),
            DummyAction("publish", "destructive", "Publish release"),
        ],
        title="Test Cockpit",
        status="dry-run-ready",
    )
    assert vm.title == "Test Cockpit"
    assert vm.status == "dry-run-ready"
    assert vm.action_count == 2
    assert [action.name for action in vm.actions] == ["status", "publish"]
    assert [action.enabled for action in vm.actions] == [True, False]
