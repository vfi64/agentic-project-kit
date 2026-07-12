from __future__ import annotations

import inspect
import json
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
    grouped_action_views,
    ordered_action_views,
    recommended_recovery_action_id,
)
from agentic_project_kit.gui_communication_modes import (
    communication_mode_definitions,
    communication_mode_next_step_hint,
    communication_mode_walkthrough_steps,
)
from agentic_project_kit.gui_gatekeeper_status import GuiGatekeeperStatus
from agentic_project_kit.gui_task_editor import CANONICAL_TRANSFER_INBOX_PATH, task_editor_visible_for_mode
from agentic_project_kit.gui_presenter import build_basic_no_window_presenter_result
from agentic_project_kit.gui_tk_widgets import attach_tooltip
from agentic_project_kit.gui_tkinter_shell import (
    build_tkinter_shell_spec,
    run_basic_cockpit_button,
)
from agentic_project_kit.gui_viewmodel import build_basic_cockpit_view_model


COCKPIT_SOURCE_PATHS = (
    Path("src/agentic_project_kit/gui_cockpit.py"),
    Path("src/agentic_project_kit/gui_cockpit_header.py"),
    Path("src/agentic_project_kit/gui_cockpit_sidebar.py"),
    Path("src/agentic_project_kit/gui_cockpit_actions.py"),
    Path("src/agentic_project_kit/gui_cockpit_task.py"),
)


def _cockpit_sources() -> str:
    return "\n".join(path.read_text(encoding="utf-8") for path in COCKPIT_SOURCE_PATHS)


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


class _TooltipSmokeWidget:
    def __init__(self) -> None:
        self.bind_counts: dict[str, int] = {}

    def bind(self, event: str, callback: object) -> None:
        self.bind_counts[event] = self.bind_counts.get(event, 0) + 1


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


def test_basic_cockpit_modes_are_built_from_shared_definitions() -> None:
    view_model = build_basic_cockpit_view_model(gatekeeper_status=_status())
    definitions = communication_mode_definitions()

    assert [mode.mode_id for mode in view_model.communication_modes] == [
        definition.mode_id for definition in definitions
    ]
    assert [mode.label for mode in view_model.communication_modes] == [
        definition.label for definition in definitions
    ]
    assert [mode.safety_note for mode in view_model.communication_modes] == [
        definition.safety_note for definition in definitions
    ]


def test_communication_mode_has_next_step_hint_for_each_mode() -> None:
    for definition in communication_mode_definitions():
        assert definition.next_step_hint
        assert communication_mode_next_step_hint(definition.mode_id) == definition.next_step_hint


def test_communication_mode_has_walkthrough_steps_for_each_mode() -> None:
    for definition in communication_mode_definitions():
        assert len(definition.walkthrough_steps) >= 4
        assert communication_mode_walkthrough_steps(definition.mode_id) == definition.walkthrough_steps


def test_sidebar_renders_communication_mode_hint_and_walkthrough_from_shared_definitions() -> None:
    source = Path("src/agentic_project_kit/gui_cockpit_sidebar.py").read_text(encoding="utf-8")

    assert "mode_explanation_var" in source
    assert "mode_next_step_var" in source
    assert "communication_mode_example" in source
    assert "communication_mode_next_step_hint" in source
    assert "communication_mode_walkthrough_steps" in source


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


def test_cockpit_smoke_contract_covers_actions_transfer_task_editor_and_tooltips() -> None:
    view_model = build_basic_cockpit_view_model(gatekeeper_status=_status())
    presenter = build_basic_no_window_presenter_result(gatekeeper_status=_status())
    shell = build_tkinter_shell_spec(_status())
    action_views = ordered_action_views(build_gui_action_views())
    widget = _TooltipSmokeWidget()

    attach_tooltip(widget, "First")
    attach_tooltip(widget, "Second")

    assert presenter.ok is True
    assert shell.action_count > 0
    assert action_views
    assert any(action.action_id == "gate.doctor" for action in action_views)
    assert view_model.communication_mode == "file_transfer"
    assert task_editor_visible_for_mode(view_model.communication_mode)
    assert widget.bind_counts == {"<Enter>": 1, "<Leave>": 1}


def test_basic_cockpit_summary_is_stable_for_entrypoint_output() -> None:
    text = format_basic_cockpit_summary(build_basic_cockpit_view_model(gatekeeper_status=_status()))

    assert "BASIC_COCKPIT" in text
    assert "traffic_light_state=READY" in text
    assert "required_next_reply=<none>" in text
    assert "buttons=status-refresh" in text


def test_gui_theme_output_is_readable_without_dominating_layout() -> None:
    assert THEME.output_height == 20
    assert THEME.output_font == ("TkFixedFont", 10)
    assert THEME.body_font == ("TkDefaultFont", 10)
    assert THEME.frame_padding == 16


def test_gui_theme_action_rows_visible() -> None:
    assert THEME.action_rows_visible == 4


def test_recommended_zone_shows_next_safe_action() -> None:
    view_model = build_basic_cockpit_view_model(gatekeeper_status=_status())

    text = format_recommended_action(view_model)

    assert view_model.recommended_action.label == "Run next work order"
    assert view_model.recommended_action.command_id == "run-next-work-order"
    assert view_model.next_safe_action in text
    assert view_model.reason in text


def test_view_model_exposes_central_next_step_guidance() -> None:
    view_model = build_basic_cockpit_view_model(gatekeeper_status=_status())

    assert view_model.next_step.state_label == "READY"
    assert view_model.next_step.title == "Ready for the next safe step"
    assert view_model.next_step.message == view_model.recommended_action.description
    assert view_model.next_step.primary_label == view_model.recommended_action.label
    assert view_model.next_step.primary_kind == view_model.recommended_action.kind
    assert view_model.next_step.primary_command_id == view_model.recommended_action.command_id


def test_view_model_next_step_uses_blocked_recovery_language() -> None:
    view_model = build_basic_cockpit_view_model(
        gatekeeper_status=_status(git_dirty=True, blockers=("working tree is dirty",))
    )

    assert view_model.next_step.state_label == "BLOCKED"
    assert view_model.next_step.title == "Fix blockers before continuing"
    assert view_model.next_step.primary_label == "Open diagnostics"
    assert view_model.next_step.primary_kind == "select_action"
    assert view_model.next_step.primary_cockpit_action_id == "gate.doctor"


def test_recommended_zone_recovery_only_selects_does_not_run() -> None:
    view_model = build_basic_cockpit_view_model(
        gatekeeper_status=_status(git_dirty=True, blockers=("working tree is dirty",))
    )
    source = inspect.getsource(CockpitGui.load_recovery_action)

    assert recommended_recovery_action_id(view_model) == "gate.doctor"
    assert view_model.recommended_action.kind == "select_action"
    text = format_recommended_action(view_model)
    assert "without running it" in text
    assert "_select_action" in source
    assert "_agentic_command" not in source
    assert "run_cockpit_action" not in source


def test_recommended_zone_recovery_hidden_when_not_blocked() -> None:
    view_model = build_basic_cockpit_view_model(gatekeeper_status=_status())

    assert recommended_recovery_action_id(view_model) is None
    assert "Recovery:" not in format_recommended_action(view_model)


def test_view_model_exposes_button_groups_for_didactic_guidance() -> None:
    view_model = build_basic_cockpit_view_model(gatekeeper_status=_status())

    groups = {group.group_id: group for group in view_model.button_groups}

    assert "routine" in groups
    assert "transfer" in groups
    assert "diagnostics" in groups
    assert "status-refresh" in groups["routine"].button_ids
    assert "run-next-work-order" in groups["routine"].button_ids
    assert "communication-rules-refresh" in groups["transfer"].button_ids
    assert "diagnose" in groups["diagnostics"].button_ids


def test_action_cards_are_grouped_by_routine_transfer_diagnostics_and_advanced() -> None:
    grouped = grouped_action_views(ordered_action_views(build_gui_action_views(access_level="advanced")))
    groups = {group.group_id: group for group in grouped}

    assert [group.group_id for group in grouped] == ["routine", "transfer", "diagnostics", "advanced"]
    assert any(action.action_id == "git.status" for action in groups["routine"].actions)
    assert any(action.action_id == "dialog.rn" for action in groups["transfer"].actions)
    assert any(action.action_id == "gate.doctor" for action in groups["diagnostics"].actions)
    assert any(action.action_id == "release.plan" for action in groups["advanced"].actions)


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


def test_action_cards_have_scrollbar_and_four_visible_rows() -> None:
    source = _cockpit_sources()

    assert action_tree_visible_rows() == 4
    assert "ttk.Scrollbar" in source
    assert "yscrollcommand" in source
    assert "action_card_container" in source
    assert "action_list_height = THEME.action_rows_visible * THEME.action_card_height" in source
    assert "action_shell_width = THEME.action_list_width + THEME.action_scrollbar_width" in source
    assert "height=action_list_height" in source
    assert "self.action_scroll_shell = action_scroll_shell" in source
    assert "_bind_action_card_scroll_events" in source
    assert "_on_action_card_mousewheel" in source
    assert "ttk.Treeview" not in source
    assert "THEME.action_card_height" in source


def test_cockpit_output_has_copy_button() -> None:
    source = _cockpit_sources()

    assert "text=\"Copy\"" in source
    assert "def copy_output" in source
    assert "clipboard_append" in source


def test_d2_pending_status_detail_has_tooltip() -> None:
    source = _cockpit_sources()

    assert "d2 means a communication-rule refresh is pending" in source
    assert "RULE_REFRESH_ACK" in source


def test_basic_cockpit_header_text() -> None:
    assert HEADER_TEXT == "Agentic Project Kit — Cockpit"


def test_cockpit_has_access_level_selector() -> None:
    source = _cockpit_sources()

    assert "Access level" in source
    assert "access_level_option_values()" in source
    assert "update_access_level" in source


def test_changing_access_level_rebuilds_action_table() -> None:
    source = inspect.getsource(CockpitGui.update_access_level)

    assert "build_basic_cockpit_view_model" in source
    assert "build_gui_action_views" in source
    assert "_rebuild_main_content" in source
    assert "populate_action_tree" in source


def test_task_send_uses_publish_and_success_status_mentions_gui_transfer_branch() -> None:
    source = _cockpit_sources()

    assert '"--publish"' in source
    assert "Task carrier published to gui-transfer-tasks as mode" in source
    assert "CANONICAL_TRANSFER_INBOX_PATH" in source
    assert CANONICAL_TRANSFER_INBOX_PATH.as_posix() == ".agentic/transfer/inbox/current.yaml"
    assert '"--communication-mode"' in source
    assert "self.current_communication_mode()" in source
    assert '"state", "--json"' in source
    assert "transfer read-user-task" not in source
    assert ".agentic/transfer/outbox/last_result.txt" in source
    assert "docs/reports/transfer_tasks/current_user_task.json" not in source


def test_task_editor_exposes_terminal_and_transfer_continue_buttons() -> None:
    source = _cockpit_sources()
    task_editor_source = Path("src/agentic_project_kit/gui_task_editor.py").read_text(encoding="utf-8")

    assert 'text="Open local terminal"' in source
    assert "standard_command_label_for_communication_mode" in source
    assert "Run mode-b standard" in task_editor_source
    assert "Run mode-a standard" in task_editor_source
    assert '"transfer", "continue", "--json"' in task_editor_source
    assert '"transfer", "patch-cycle-status", "--json"' in task_editor_source
    assert "open_transfer_terminal_for_project" in source
    assert "run_mode_standard_command" in source


def test_action_cards_use_single_tooltip_source_per_card() -> None:
    source = inspect.getsource(CockpitGui._create_action_card)

    assert "attach_tooltip(card, tooltip)" in source
    assert "attach_tooltip(widget, tooltip)" not in source


def test_cockpit_builds_work_cycle_bar_above_body() -> None:
    source = _cockpit_sources()

    cockpit_source = Path("src/agentic_project_kit/gui_cockpit.py").read_text(encoding="utf-8")
    assert "self._build_header(shell)" not in cockpit_source
    assert "self._build_work_cycle_bar(shell)\n\n        body =" in cockpit_source
    assert "WORK CYCLE" in source
    assert "build_work_cycle_views" in source


def test_branch_label_moves_from_large_header_to_status_detail() -> None:
    source = Path("src/agentic_project_kit/gui_cockpit_sidebar.py").read_text(encoding="utf-8")

    assert 'self._detail_row(sidebar, "Branch", self._branch_label())' in source


def test_work_cycle_bar_exposes_human_phase_labels() -> None:
    source = Path("src/agentic_project_kit/work_cycle.py").read_text(encoding="utf-8")

    assert "Start work" in source
    assert "Make changes" in source
    assert "Check" in source
    assert "Finish & publish" in source
    assert "Needs recovery" in source
    assert "Confirm publish" in source


def test_work_cycle_finish_requires_dry_run_before_execute() -> None:
    source = _cockpit_sources()

    assert "preview_work_finish" in source
    assert "confirm_work_finish" in source
    assert "pending_finish_preview" in source
    assert "allow_confirm_from_preview=True" in source
    assert "execute=False" in source
    assert "execute=True" in source
    assert "Run Finish & publish first" in source


def test_work_cycle_discard_changes_is_separate_destructive_confirm_flow() -> None:
    source = _cockpit_sources()
    preview_source = inspect.getsource(CockpitGui.preview_discard_changes)
    confirm_source = inspect.getsource(CockpitGui.confirm_discard_changes)
    recover_source = inspect.getsource(CockpitGui.run_work_recover)

    assert "Discard all changes" in source
    assert "Confirm discard" in source
    assert "pending_discard_preview" in source
    assert '"discard-changes"' in preview_source
    assert '"--execute"' not in preview_source
    assert '"--execute"' in confirm_source
    assert '"--expected-signature"' in confirm_source
    assert "self._work_cycle_signature()" in confirm_source
    assert '"discard-changes"' not in recover_source


def test_work_cycle_uses_existing_work_wrappers_not_direct_remote_mutation() -> None:
    source = _cockpit_sources()

    start_source = inspect.getsource(CockpitGui.start_work_cycle)
    assert '"work"' in start_source
    assert '"start"' in start_source
    assert '"work", "check"' in source
    assert '"work", "recover"' in source
    assert "build_work_finish_args" in source
    assert '"gh"' not in source
    assert '"push"' not in inspect.getsource(CockpitGui.preview_work_finish)
    assert '"push"' not in inspect.getsource(CockpitGui.confirm_work_finish)


def test_work_cycle_make_changes_focuses_existing_task_editor() -> None:
    source = inspect.getsource(CockpitGui.focus_make_changes)

    assert "self.task_text.focus_set()" in source
    assert "file-transfer task editor" in source


def test_work_cycle_start_generates_safe_branch_name_from_task() -> None:
    source = inspect.getsource(CockpitGui.start_work_cycle)

    assert "simpledialog.askstring" in source
    assert "slugify_work_title" in source
    assert '"--branch"' in source
    assert '"--from-ref"' in source


def test_work_cycle_start_ref_picker_uses_based_on_language() -> None:
    source = Path("src/agentic_project_kit/gui_cockpit_header.py").read_text(encoding="utf-8")

    assert "Start new work based on" in source
    assert "It does not rewind history." in source
    assert "go back" not in source.casefold()
    assert 'self._agentic_command("transfer", "list-refs", "--json")' in source


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


def test_doc_lifecycle_sweep_runner_uses_agentic_kit_wrapper(monkeypatch) -> None:
    calls: list[tuple[str, ...]] = []

    def fake_run_kit_command(*args: str, project_root: Path | str = ".") -> tuple[int, str]:
        calls.append(args)
        assert project_root == Path.cwd()
        return 0, "DOC_LIFECYCLE_SWEEP"

    monkeypatch.setattr(gui_tkinter_shell, "run_kit_command", fake_run_kit_command)

    returncode, output = gui_tkinter_shell.MANUAL_GUI_READONLY_RUNNERS[
        "doc-lifecycle-sweep-dry-run"
    ]()

    assert returncode == 0
    assert output == "DOC_LIFECYCLE_SWEEP"
    assert calls == [("docs", "lifecycle", "sweep", "--dry-run")]


def test_lifecycle_badge_text_reads_audit_json(monkeypatch) -> None:
    payload = {
        "findings": [
            {"code": "HEADER_MISSING"},
            {"code": "REVIEW_DUE_DATE"},
            {"code": "SOURCE_OF_CLOSED_ITEM_STILL_ACTIVE"},
        ]
    }

    def fake_run_kit_command(*args: str, project_root: Path | str = ".") -> tuple[int, str]:
        assert args == ("doc-lifecycle-audit", "--json")
        return 0, json.dumps(payload)

    monkeypatch.setattr(gui_tkinter_shell, "run_kit_command", fake_run_kit_command)

    assert gui_tkinter_shell.lifecycle_badge_text(Path.cwd()) == "lifecycle: 3 warn / 2 due"


def test_manual_launch_status_contains_lifecycle_badge() -> None:
    source = Path("src/agentic_project_kit/gui_tkinter_shell.py").read_text(encoding="utf-8")

    assert "lifecycle_badge_text(Path.cwd())" in source
    assert "{lifecycle_badge}" in source


def test_inspect_selected_shows_structured_explanation() -> None:
    actions = {
        action.action_id: action
        for action in build_gui_action_views(access_level="advanced")
    }

    text = format_action_details(actions["rules.communication-refresh"])

    assert "structured_explanation:" in text
    assert "PURPOSE:" in text
    assert "AFTER PASS:" in text
