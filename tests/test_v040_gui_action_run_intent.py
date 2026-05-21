from __future__ import annotations

from dataclasses import dataclass

from agentic_project_kit.gui_action_run_intent import build_gui_action_run_intent, render_gui_action_run_intent


@dataclass(frozen=True)
class Action:
    name: str
    safety_class: str
    description: str = ""


ACTIONS = [
    Action("dev", "read_only"),
    Action("release-prep", "local_only"),
    Action("agent-run", "remote_mutation"),
    Action("release-publish", "destructive"),
]


def test_read_only_action_creates_enabled_non_executing_intent():
    intent = build_gui_action_run_intent(ACTIONS, "dev", terminal_log="/tmp/gui.log")
    assert intent.known is True
    assert intent.safety_class == "read_only"
    assert intent.enabled is True
    assert intent.requires_confirmation is False
    assert intent.would_execute is False
    assert intent.output_target == "output-status-panel"
    assert intent.terminal_log == "/tmp/gui.log"


def test_unknown_action_is_blocked():
    intent = build_gui_action_run_intent(ACTIONS, "missing")
    assert intent.known is False
    assert intent.enabled is False
    assert intent.blocked_reason == "unknown action"


def test_remote_mutation_is_blocked_by_default():
    intent = build_gui_action_run_intent(ACTIONS, "agent-run")
    assert intent.enabled is False
    assert intent.requires_confirmation is True
    assert intent.confirmation_token == "confirm-agent-run"
    assert intent.blocked_reason == "remote mutation disabled in GUI safe mode"


def test_remote_mutation_can_be_enabled_only_with_confirmation():
    missing = build_gui_action_run_intent(ACTIONS, "agent-run", allow_remote_mutation=True)
    assert missing.enabled is False
    assert missing.blocked_reason == "missing confirmation token"
    confirmed = build_gui_action_run_intent(
        ACTIONS,
        "agent-run",
        allow_remote_mutation=True,
        confirmation="confirm-agent-run",
    )
    assert confirmed.enabled is True
    assert confirmed.would_execute is False


def test_destructive_action_is_blocked_by_default():
    intent = build_gui_action_run_intent(ACTIONS, "release-publish")
    assert intent.enabled is False
    assert intent.requires_confirmation is True
    assert intent.confirmation_token == "confirm-release-publish"
    assert intent.blocked_reason == "destructive action disabled in GUI safe mode"


def test_render_intent_is_machine_readable():
    intent = build_gui_action_run_intent(ACTIONS, "dev", terminal_log="/tmp/gui.log")
    output = render_gui_action_run_intent(intent)
    assert "GUI ACTION RUN INTENT" in output
    assert "action_name=dev" in output
    assert "enabled=true" in output
    assert "would_execute=false" in output
    assert "terminal_log=/tmp/gui.log" in output
