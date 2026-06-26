from __future__ import annotations

from agentic_project_kit.gui_button_catalog import GuiButtonDefinition, basic_gui_buttons
from agentic_project_kit.gui_cockpit import format_basic_cockpit_summary
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


def test_basic_cockpit_buttons_are_derived_from_registered_basic_catalog() -> None:
    view_model = build_basic_cockpit_view_model(gatekeeper_status=_status())

    assert [button.command_id for button in view_model.buttons] == [
        button.command_id for button in basic_gui_buttons()
    ]
    by_id = {button.command_id: button for button in view_model.buttons}
    assert by_id["status-refresh"].enabled is True
    assert by_id["status-refresh"].tooltip
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
    assert "buttons=status-refresh" in text


def test_basic_button_execution_revalidates_gatekeeper_before_dispatch() -> None:
    output = run_basic_cockpit_button(
        "communication-rules-refresh",
        gatekeeper_status=_status(git_dirty=True, blockers=("working tree is dirty",)),
    )

    assert "action=communication-rules-refresh" in output
    assert "allowed=false" in output
    assert "executed=false" in output
