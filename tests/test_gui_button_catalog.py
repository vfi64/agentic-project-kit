from agentic_project_kit.gui_button_catalog import (
    all_gui_buttons,
    disabled_gui_button_ids,
    enabled_gui_button_ids,
    get_gui_button,
    gui_buttons_by_category,
    toolbar_gui_buttons,
)


def test_gui_button_catalog_covers_communication_and_workflow_surface():
    command_ids = {button.command_id for button in all_gui_buttons()}
    assert len(command_ids) == len(all_gui_buttons())
    assert len(command_ids) >= 30
    assert {
        "branch-status-check",
        "next-turn-status",
        "last-result",
        "handoff-check",
        "handoff-prompt",
        "bootstrap-show",
        "terminal-remote-preflight",
        "workflow-guard-check",
        "protected-change-plan",
        "merge-if-green",
        "agent-run",
        "work-order-show",
        "work-order-validate",
        "work-order-run",
        "work-order-upload",
    } <= command_ids


def test_gui_button_catalog_keeps_only_readonly_buttons_enabled():
    enabled = [button for button in all_gui_buttons() if button.enabled]
    assert {button.command_id for button in enabled} == set(enabled_gui_button_ids())
    assert all(button.safety_class == "read-only" or button.command_id == "work-order-upload" for button in enabled)\n    assert any(button.command_id == "work-order-upload" and button.safety_class == "bounded-mutation" for button in enabled)
    assert {"agent-run", "merge-if-green", "release-publish"} <= set(disabled_gui_button_ids())
    assert all(button.disabled_reason for button in all_gui_buttons() if not button.enabled)


def test_gui_button_catalog_groups_buttons_and_toolbar_from_catalog():
    categories = gui_buttons_by_category()
    assert {
        "Session",
        "Evidence",
        "Quality Gates",
        "Diagnostics",
        "Git Workflow",
        "Release",
        "Workflow Automation",
    } <= set(categories)
    assert [button.command_id for button in toolbar_gui_buttons()] == [
        "branch-status-check",
        "next-turn-status",
        "last-result",
        "handoff-check",
        "doctor",
        "check-docs",
        "docs-audit",
        "workflow-guard-check",
    ]


def test_gui_button_lookup_preserves_button_metadata():
    button = get_gui_button("protected-change-plan")
    assert button is not None
    assert button.category == "Evidence"
    assert button.implementation_state == "planned"
    assert button.enabled is False
    assert "diff" in button.disabled_reason
