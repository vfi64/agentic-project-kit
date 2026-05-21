from __future__ import annotations

from dataclasses import dataclass

from agentic_project_kit.gui_action_execution import action_safety_class
from agentic_project_kit.gui_action_execution import find_action
from agentic_project_kit.gui_action_execution import is_bounded_read_only_action
from agentic_project_kit.gui_action_execution import normalize_safety_class
from agentic_project_kit.gui_action_execution import run_bounded_read_only_action


@dataclass(frozen=True)
class Action:
    name: str
    safety_class: str


def test_normalizes_safety_class_aliases():
    assert normalize_safety_class("remote_mutation") == "remote-mutation"
    assert normalize_safety_class(" READ-ONLY ") == "read-only"


def test_finds_action_by_name():
    actions = [Action("dev", "read-only"), Action("agent-run", "remote-mutation")]
    assert find_action(actions, "dev") == actions[0]
    assert find_action(actions, "missing") is None


def test_read_only_action_is_allowed_but_not_executed_without_executor():
    result = run_bounded_read_only_action([Action("dev", "read-only")], "dev")
    assert result.allowed is True
    assert result.executed is False
    assert result.returncode == 0
    assert "no executor" in result.message


def test_read_only_action_executes_only_through_injected_executor():
    result = run_bounded_read_only_action(
        [Action("dev", "read-only")],
        "dev",
        executor=lambda action: (0, f"executed:{action.name}"),
    )
    assert result.allowed is True
    assert result.executed is True
    assert result.output == "executed:dev"


def test_local_only_and_remote_mutation_are_blocked():
    calls = []
    def executor(action):
        calls.append(action.name)
        return 0, "should-not-run"
    for safety in ("local-only", "remote-mutation", "remote_mutation", "destructive", "release", "mutation", "remote"):
        result = run_bounded_read_only_action([Action("x", safety)], "x", executor=executor)
        assert result.allowed is False
        assert result.executed is False
        assert result.returncode == 2
    assert calls == []


def test_unknown_or_missing_action_is_blocked():
    missing = run_bounded_read_only_action([Action("dev", "read-only")], "missing")
    assert missing.allowed is False
    assert missing.returncode == 2
    unknown = run_bounded_read_only_action([Action("x", "unknown")], "x")
    assert unknown.allowed is False
    assert action_safety_class(Action("x", "remote_mutation")) == "remote-mutation"
    assert is_bounded_read_only_action(Action("dev", "read-only")) is True
