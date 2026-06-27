from __future__ import annotations

import inspect
from pathlib import Path

from agentic_project_kit import gui_tkinter_shell
from agentic_project_kit.gui_button_catalog import GuiButtonDefinition, basic_gui_buttons
from agentic_project_kit.gui_cockpit import (
    CockpitGui,
    HEADER_TEXT,
    THEME,
    action_tree_columns,
    action_tree_tag_colors,
    action_tree_visible_rows,
    build_gui_action_views,
    format_recommended_action,
    format_action_details,
    format_basic_cockpit_summary,
    format_state_details,
    ordered_action_views,
    recommended_recovery_action_id,
)
from agentic_project_kit.gui_gatekeeper_status import GuiGatekeeperStatus
from agentic_project_kit.gui_presenter import build_basic_no_window_presenter_result
from agentic_project_kit.gui_tkinter_shell import (
    build_tkinter_shell_spec,
    run_basic_cockpit_button,
)
from agentic_project_kit.gui_viewmodel import build_basic_cockpit_view_model


def _status(
    *,
    git_dirty: bool = False,
    workflow_state: str = "IDLE",
    current_work_state: str | None = "READY",
    blockers: tuple[str, ...] = (),
    communication_context_fresh: bool = True,
    communication_context_reason: str = "communication_context_current",
    required_next_reply: str | None = None,
) -> GuiGatekeeperStatus:
    return GuiGatekeeperStatus(
        branch="main",
        git_dirty=git_dirty,
        workflow_state=workflow_state,
        current_work_present=current_work_state is not None,
        current_work_state=current_work_state,
        ready_for_read_only_actions=not git_dirty,
        ready_for_mutating_actions=not git_dirty and workflow_state in {"IDLE", "READY"},
        action_statuses=(),
        blockers=blockers,
        communication_context_fresh=communication_context_fresh,
        communication_context_reason=communication_context_reason,
        required_next_reply=required_next_reply,
    )


def _button(
    command_id: str,
    *,
    safety_class: str,
    enabled: bool = True,
) -> GuiButtonDefinition:
    return GuiButtonDefinition(
        command_id=command_id,
        label=command_id,
        category="Basic",
        tooltip=command_id,
        icon_text="test",
        safety_class=safety_class,
        implementation_state="implemented",
        enabled=enabled,
        wrapper_command=("agentic-kit", "test"),
        gui_gate="test_gate",
    )


def test_basic_cockpit_traffic_light_states_are_deterministic() -> None:
    assert build_basic_cockpit_view_model(gatekeeper_status=_status()).traffic_light_state == "READY"
    assert (
        build_basic_cockpit_view_model(
            gatekeeper_status=_status(workflow_state="RUNNING", current_work_state="RUNNING")
        ).traffic_light_state
        == "WAIT"
    )
    assert (
        build_basic_cockpit_view_model(
            gatekeeper_status=_status(git_dirty=True, blockers=("working tree is dirty",))
        ).traffic_light_state
        == "BLOCKED"
    )
    assert (
        build_basic_cockpit_view_model(
            gatekeeper_status=_status(current_work_state="FAILED")
        ).traffic_light_state
        == "FAILED"
    )
    assert (
        build_basic_cockpit_view_model(
            gatekeeper_status=_status(
                blockers=("communication_rule_refresh_pending",),
                communication_context_fresh=False,
                communication_context_reason="communication_rule_refresh_pending",
                required_next_reply="d2",
            )
        ).traffic_light_state
        == "WAIT_FOR_D2"
    )


def test_basic_cockpit_modes_keep_file_transfer_as_default_and_copy_paste_as_fallback() -> None:
    view_model = build_basic_cockpit_view_model(gatekeeper_status=_status())

    modes = {mode.mode_id: mode for mode in view_model.communication_modes}
    assert view_model.communication_mode == "file_transfer"
    assert modes["file_transfer"].label == "File Transfer"
    assert modes["file_transfer"].is_default is True
    assert modes["file_transfer"].selected is True
    assert modes["remote"].is_default is False
    assert modes["copy_paste"].is_default is False
    assert modes["copy_paste"].role == "Recovery/Fallback"


def test_basic_cockpit_view_model_carries_access_level() -> None:
    view_model = build_basic_cockpit_view_model(gatekeeper_status=_status(), access_level="advanced")

    assert view_model.access_level == "advanced"
    assert view_model.access_level_options == ("basic", "advanced", "maintainer")
    assert "release" in view_model.access_level_explanation


def test_basic_cockpit_buttons_are_derived_from_registered_basic_catalog() -> None:
    view_model = build_basic_cockpit_view_model(gatekeeper_status=_status())

    assert [button.command_id for button in view_model.buttons] == [
        button.command_id for button in basic_gui_buttons()
    ]
    by_id = {button.command_id: button for button in view_model.buttons}
    assert by_id["status-refresh"].enabled is True
    assert by_id["status-refresh"].tooltip
    assert by_id["restore-volatile"].enabled is True
    assert by_id["restore-volatile"].tooltip
    assert by_id["restore-volatile"].wrapper_command == (
        "agentic-kit",
        "transfer",
        "restore-known-volatile",
        "--json",
    )
    assert by_id["diagnose"].enabled is True
    assert by_id["diagnose"].tooltip
    assert by_id["communication-rules-refresh"].enabled is False
    assert by_id["run-next-work-order"].enabled is False
    assert by_id["close-out-last-run"].enabled is False


def test_basic_cockpit_blocks_remote_destructive_and_release_actions() -> None:
    buttons = (
        _button("remote-demo", safety_class="remote-mutation"),
        _button("destructive-demo", safety_class="destructive"),
        _button("release-publish", safety_class="read-only"),
    )

    view_model = build_basic_cockpit_view_model(gatekeeper_status=_status(), buttons=buttons)

    assert {button.command_id for button in view_model.buttons if not button.enabled} == {
        "remote-demo",
        "destructive-demo",
        "release-publish",
    }
    assert all(button.disabled_reason for button in view_model.buttons)


def test_basic_cockpit_dirty_worktree_blocks_mutating_actions() -> None:
    view_model = build_basic_cockpit_view_model(
        gatekeeper_status=_status(git_dirty=True, blockers=("working tree is dirty",)),
        buttons=(_button("local-demo", safety_class="local-only"),),
    )

    button = view_model.buttons[0]
    assert button.enabled is False
    assert "dirty" in button.disabled_reason


def test_basic_cockpit_allows_restore_volatile_as_dirty_recovery() -> None:
    restore_button = next(button for button in basic_gui_buttons() if button.command_id == "restore-volatile")
    view_model = build_basic_cockpit_view_model(
        gatekeeper_status=_status(git_dirty=True, blockers=("working tree is dirty",)),
        buttons=(restore_button,),
    )

    button = view_model.buttons[0]

    assert button.enabled is True
    assert button.wrapper_command == ("agentic-kit", "transfer", "restore-known-volatile", "--json")
    assert "bounded recovery" in button.why


def test_basic_cockpit_blocks_restore_volatile_when_failed_evidence_must_be_preserved() -> None:
    restore_button = next(button for button in basic_gui_buttons() if button.command_id == "restore-volatile")
    view_model = build_basic_cockpit_view_model(
        gatekeeper_status=_status(current_work_state="FAILED"),
        buttons=(restore_button,),
    )

    button = view_model.buttons[0]

    assert button.enabled is False
    assert "failed workflow evidence" in button.disabled_reason


def test_restore_volatile_basic_button_uses_registered_wrapper(monkeypatch) -> None:
    monkeypatch.setitem(
        gui_tkinter_shell.MANUAL_GUI_READONLY_RUNNERS,
        "restore-volatile",
        lambda: (0, "volatile restored"),
    )

    output = run_basic_cockpit_button(
        "restore-volatile",
        gatekeeper_status=_status(git_dirty=True, blockers=("working tree is dirty",)),
    )

    assert "action=restore-volatile" in output
    assert "allowed=true" in output
    assert "executed=true" in output
    assert "volatile restored" in output


def test_basic_no_window_presenter_and_tkinter_smoke_expose_basic_state() -> None:
    presenter = build_basic_no_window_presenter_result(gatekeeper_status=_status())
    shell = build_tkinter_shell_spec(_status())

    assert presenter.ok is True
    assert "traffic_light_state=READY" in presenter.rendered
    assert "communication_mode=file_transfer" in presenter.rendered
    assert shell.traffic_light_state == "READY"
    assert shell.basic_button_count == len(basic_gui_buttons())


def test_basic_cockpit_summary_is_stable_for_entrypoint_output() -> None:
    text = format_basic_cockpit_summary(build_basic_cockpit_view_model(gatekeeper_status=_status()))

    assert "BASIC_COCKPIT" in text
    assert "traffic_light_state=READY" in text
    assert "required_next_reply=<none>" in text
    assert "buttons=status-refresh" in text


def test_gui_theme_output_height_increased() -> None:
    assert THEME.output_height == 21


def test_gui_theme_action_rows_visible() -> None:
    assert THEME.action_rows_visible == 4


def test_recommended_zone_shows_next_safe_action() -> None:
    view_model = build_basic_cockpit_view_model(gatekeeper_status=_status())

    text = format_recommended_action(view_model)

    assert view_model.next_safe_action in text
    assert view_model.reason in text


def test_recommended_zone_recovery_only_selects_does_not_run() -> None:
    view_model = build_basic_cockpit_view_model(
        gatekeeper_status=_status(git_dirty=True, blockers=("working tree is dirty",))
    )
    source = inspect.getsource(CockpitGui.load_recovery_action)

    assert recommended_recovery_action_id(view_model) == "gate.doctor"
    text = format_recommended_action(view_model)
    assert "without running it" in text
    assert "selection_set" in source
    assert "_agentic_command" not in source
    assert "run_cockpit_action" not in source


def test_recommended_zone_recovery_hidden_when_not_blocked() -> None:
    view_model = build_basic_cockpit_view_model(gatekeeper_status=_status())

    assert recommended_recovery_action_id(view_model) is None
    assert "Recovery:" not in format_recommended_action(view_model)


def test_action_tree_orders_read_only_first() -> None:
    actions = ordered_action_views(build_gui_action_views())
    safety_order = {"read_only": 0, "bounded": 1, "destructive": 2}

    assert [safety_order[action.safety] for action in actions] == sorted(
        safety_order[action.safety] for action in actions
    )


def test_view_model_basic_excludes_maintainer_actions() -> None:
    actions = build_gui_action_views(access_level="basic")
    action_ids = {action.action_id for action in actions}

    assert "git.status" in action_ids
    assert "workflow.state" in action_ids
    assert "transfer.restore-known-volatile" in action_ids
    assert "release.plan" not in action_ids
    assert "audit.pr-hygiene" not in action_ids


def test_view_model_advanced_shows_release_hides_audit() -> None:
    actions = build_gui_action_views(access_level="advanced")
    action_ids = {action.action_id for action in actions}

    assert "release.plan" in action_ids
    assert "rules.communication-refresh" in action_ids
    assert "audit.doc-mesh" not in action_ids


def test_view_model_maintainer_includes_all_actions() -> None:
    actions = build_gui_action_views(access_level="maintainer")

    assert len(actions) == 18
    assert {action.action_id for action in actions if action.min_access_level == "maintainer"} == {
        "audit.doc-mesh",
        "audit.doc-lifecycle",
        "audit.pr-hygiene",
    }


def test_access_level_does_not_override_safety_gating() -> None:
    actions = {action.action_id: action for action in build_gui_action_views(access_level="maintainer")}

    assert actions["transfer.restore-known-volatile"].safety == "bounded"
    assert actions["transfer.restore-known-volatile"].can_run_by_default is False


def test_action_tree_has_safety_color_tags() -> None:
    assert action_tree_tag_colors() == {
        "read_only": THEME.color_read_only,
        "bounded": THEME.color_bounded,
        "destructive": THEME.color_destructive,
    }


def test_action_tree_hides_raw_command_column() -> None:
    assert action_tree_columns() == ("action", "what_it_does", "safety")
    assert "command" not in action_tree_columns()


def test_action_tree_shows_short_description_column() -> None:
    assert "what_it_does" in action_tree_columns()
    assert all(action.short_description for action in ordered_action_views(build_gui_action_views()))


def test_action_tree_has_scrollbar_and_four_visible_rows() -> None:
    source = Path("src/agentic_project_kit/gui_cockpit.py").read_text(encoding="utf-8")

    assert action_tree_visible_rows() == 4
    assert "ttk.Scrollbar" in source
    assert "yscrollcommand" in source


def test_basic_cockpit_header_text() -> None:
    assert HEADER_TEXT == "Agentic-Project-Kit — Basic Cockpit"


def test_cockpit_has_access_level_selector() -> None:
    source = Path("src/agentic_project_kit/gui_cockpit.py").read_text(encoding="utf-8")

    assert "Access level" in source
    assert "access_level_option_values()" in source
    assert "update_access_level" in source


def test_changing_access_level_rebuilds_action_table() -> None:
    source = inspect.getsource(CockpitGui.update_access_level)

    assert "build_basic_cockpit_view_model" in source
    assert "build_gui_action_views" in source
    assert "populate_action_tree" in source


def test_task_send_uses_publish_and_success_status_mentions_gui_transfer_branch() -> None:
    source = Path("src/agentic_project_kit/gui_cockpit.py").read_text(encoding="utf-8")

    assert '"--publish"' in source
    assert "Transfer order published to gui-transfer-tasks. Send g/go in chat." in source
    assert '"state", "--json"' in source
    assert "transfer read-user-task" not in source
    assert ".agentic/transfer/outbox/last_result.txt" in source
    assert "docs/reports/transfer_tasks/current_user_task.json" not in source


def test_cockpit_gui_shows_wait_for_d2_label_when_pending() -> None:
    view_model = build_basic_cockpit_view_model(
        gatekeeper_status=_status(
            blockers=("communication_rule_refresh_pending",),
            communication_context_fresh=False,
            communication_context_reason="communication_rule_refresh_pending",
            required_next_reply="d2",
        )
    )

    details = format_state_details(view_model)

    assert "STATE: WAIT_FOR_D2 (yellow)" in details
    assert "Send 'd2' to the chat" in details
    assert "provide ACK before mutation" in details


def test_cockpit_gui_disables_bounded_buttons_when_d2_pending() -> None:
    view_model = build_basic_cockpit_view_model(
        gatekeeper_status=_status(
            blockers=("communication_rule_refresh_pending",),
            communication_context_fresh=False,
            communication_context_reason="communication_rule_refresh_pending",
            required_next_reply="d2",
        ),
        buttons=(_button("bounded-demo", safety_class="bounded-mutation"),),
    )

    button = view_model.buttons[0]

    assert button.enabled is False
    assert "WAIT_FOR_D2" in button.disabled_reason


def test_cockpit_gui_shows_ready_when_no_pending() -> None:
    view_model = build_basic_cockpit_view_model(gatekeeper_status=_status())

    details = format_state_details(view_model)

    assert "STATE: READY (green)" in details
    assert "Send 'd2'" not in details


def test_basic_button_execution_revalidates_gatekeeper_before_dispatch() -> None:
    output = run_basic_cockpit_button(
        "communication-rules-refresh",
        gatekeeper_status=_status(git_dirty=True, blockers=("working tree is dirty",)),
    )

    assert "action=communication-rules-refresh" in output
    assert "allowed=false" in output
    assert "executed=false" in output


def test_inspect_selected_shows_structured_explanation() -> None:
    actions = {
        action.action_id: action
        for action in build_gui_action_views(access_level="advanced")
    }

    text = format_action_details(actions["rules.communication-refresh"])

    assert "structured_explanation:" in text
    assert "PURPOSE:" in text
    assert "AFTER PASS:" in text
