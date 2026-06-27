from agentic_project_kit.access_level_policy import visible_actions
from agentic_project_kit.access_levels import ACCESS_LEVEL_ORDER, meets_min_access
from agentic_project_kit.cockpit import cockpit_actions


def test_access_level_order_is_basic_advanced_maintainer() -> None:
    assert ACCESS_LEVEL_ORDER == ("basic", "advanced", "maintainer")


def test_meets_min_access_basic_does_not_meet_maintainer() -> None:
    assert meets_min_access("basic", "maintainer") is False


def test_meets_min_access_maintainer_meets_all() -> None:
    assert meets_min_access("maintainer", "basic") is True
    assert meets_min_access("maintainer", "advanced") is True
    assert meets_min_access("maintainer", "maintainer") is True


def test_visible_actions_preserves_order() -> None:
    actions = cockpit_actions()

    visible = visible_actions(actions, "advanced")

    assert [action.action_id for action in visible] == [
        action.action_id
        for action in actions
        if action.min_access_level in {"basic", "advanced"}
    ]
