from agentic_project_kit.gui_viewmodel import build_gui_action_detail_panel


def test_action_detail_panel_exposes_registered_actions_with_safety_and_evidence_hints():
    panel = build_gui_action_detail_panel()
    names = {item.name for item in panel.actions}

    assert panel.title == "Action details"
    assert panel.status_message == "ready"
    assert "release-publish" in names
    assert all(item.safety_class != "unknown" for item in panel.actions)
    assert all(item.evidence_hint for item in panel.actions)
    assert all(item.parameter_hint for item in panel.actions)


def test_action_detail_panel_keeps_release_publish_disabled_with_reason():
    panel = build_gui_action_detail_panel(selected_action_name="release-publish")
    release_publish = next(item for item in panel.actions if item.name == "release-publish")

    assert panel.selected_action_name == "release-publish"
    assert "release-publish" in panel.disabled_action_names
    assert release_publish.enabled is False
    assert release_publish.requires_confirmation is False
    assert release_publish.disabled_reason == "disabled by GUI safety policy"
    assert release_publish.tooltip
    assert release_publish.icon_id


def test_action_detail_panel_ignores_unknown_selection():
    panel = build_gui_action_detail_panel(selected_action_name="does-not-exist")

    assert panel.selected_action_name == ""
