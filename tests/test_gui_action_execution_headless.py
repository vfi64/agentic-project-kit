from dataclasses import dataclass

from agentic_project_kit.gui_action_execution import (
    GuiActionExecutionResult,
    action_identity,
    action_safety_class,
    find_action,
    is_bounded_read_only_action,
    normalize_safety_class,
    run_bounded_read_only_action,
)


@dataclass(frozen=True)
class FakeAction:
    name: str
    safety_class: object


@dataclass(frozen=True)
class FakeActionIdOnly:
    action_id: str
    safety: object


class FakeSafetyEnum:
    def __str__(self) -> str:
        return "SafetyClass.READ_ONLY"


def test_normalize_safety_class_accepts_enum_like_values():
    assert normalize_safety_class(FakeSafetyEnum()) == "read-only"
    assert normalize_safety_class("read_only") == "read-only"
    assert normalize_safety_class(" remote-mutation ") == "remote-mutation"


def test_action_identity_accepts_name_action_id_or_id_fields():
    assert action_identity(FakeAction("doctor", "read-only")) == "doctor"
    assert action_identity(FakeActionIdOnly("check-docs", "read-only")) == "check-docs"

    class IdOnly:
        id = "cockpit-readiness"

    assert action_identity(IdOnly()) == "cockpit-readiness"


def test_action_safety_class_accepts_safety_alias():
    assert action_safety_class(FakeActionIdOnly("x", "read_only")) == "read-only"
    assert action_safety_class(object()) == "unknown"


def test_find_action_uses_normalized_identity_fields():
    actions = [FakeAction("doctor", "read-only"), FakeActionIdOnly("check-docs", "read-only")]
    assert find_action(actions, "check-docs") == actions[1]
    assert find_action(actions, "missing") is None


def test_is_bounded_read_only_action_is_strict():
    assert is_bounded_read_only_action(FakeAction("doctor", "read_only")) is True
    assert is_bounded_read_only_action(FakeAction("publish", "destructive")) is False
    assert is_bounded_read_only_action(FakeAction("remote", "remote")) is False


def test_missing_action_returns_blocked_result_without_executor_call():
    called = False

    def executor(_action):
        nonlocal called
        called = True
        return 0, "should not run"

    result = run_bounded_read_only_action([], "missing", executor=executor)

    assert result == GuiActionExecutionResult(
        "missing",
        "unknown",
        False,
        False,
        2,
        "Action not found.",
    )
    assert called is False


def test_non_readonly_action_is_blocked_without_executor_call():
    called = False

    def executor(_action):
        nonlocal called
        called = True
        return 0, "should not run"

    result = run_bounded_read_only_action([FakeAction("release-publish", "destructive")], "release-publish", executor=executor)

    assert result.action_name == "release-publish"
    assert result.safety_class == "destructive"
    assert result.allowed is False
    assert result.executed is False
    assert result.returncode == 2
    assert "limited to read-only" in result.message
    assert called is False


def test_readonly_action_without_executor_is_allowed_but_not_executed():
    result = run_bounded_read_only_action([FakeAction("doctor", "read_only")], "doctor")

    assert result.action_name == "doctor"
    assert result.safety_class == "read-only"
    assert result.allowed is True
    assert result.executed is False
    assert result.returncode == 0
    assert "no executor" in result.message


def test_readonly_action_executes_bounded_executor_and_preserves_output():
    seen = []

    def executor(action):
        seen.append(action.name)
        return "0", "doctor output"

    result = run_bounded_read_only_action([FakeAction("doctor", "read_only")], "doctor", executor=executor)

    assert seen == ["doctor"]
    assert result.action_name == "doctor"
    assert result.safety_class == "read-only"
    assert result.allowed is True
    assert result.executed is True
    assert result.returncode == 0
    assert result.output == "doctor output"


def test_readonly_action_preserves_nonzero_executor_returncode():
    result = run_bounded_read_only_action(
        [FakeAction("check-docs", "read-only")],
        "check-docs",
        executor=lambda _action: (1, "check-docs failed"),
    )

    assert result.allowed is True
    assert result.executed is True
    assert result.returncode == 1
    assert result.output == "check-docs failed"
