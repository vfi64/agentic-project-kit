"""Keep GUI and website workflow projections tied to manifest-backed data."""
from pathlib import Path

from agentic_project_kit.command_manifest import load_manifest
from agentic_project_kit.gui_communication_modes import (
    DEFAULT_COMMUNICATION_MODE,
    communication_mode_definitions,
)
from agentic_project_kit.workflow_modes import ROLE_LABELS, WORKFLOW_MODES, modes_for


def test_workflow_mode_projections_share_roles_and_actions() -> None:
    assert DEFAULT_COMMUNICATION_MODE == "file_transfer"
    site_modes = {mode.mode_id: mode for mode in modes_for("site")}
    gui_modes = {mode.mode_id: mode for mode in modes_for("gui")}
    assert set(site_modes) == {"agent_direct", "file_transfer", "copy_paste", "gui"}
    assert set(gui_modes) == {"file_transfer", "remote", "copy_paste"}
    assert modes_for("site")[0].mode_id == "agent_direct"
    assert [mode.mode_id for mode in WORKFLOW_MODES if mode.role == "primary"] == ["agent_direct"]
    assert gui_modes["remote"].role == "optional"
    assert site_modes["copy_paste"].role == "emergency"
    for definition in communication_mode_definitions():
        mode = gui_modes[definition.mode_id]
        assert definition.label == mode.label
        assert definition.role == ROLE_LABELS[mode.role]
        assert definition.walkthrough_steps == tuple(step.action for step in mode.flow)


def test_all_mode_steps_name_known_actors_and_manifest_commands() -> None:
    root = Path(__file__).resolve().parents[1]
    manifest = {entry["qualified_name"] for entry in load_manifest(root)["commands"]}
    actors = {"you", "assistant", "kit"}
    for mode in WORKFLOW_MODES:
        assert len(mode.flow) >= 2
        assert set(mode.commands) <= manifest
        for step in mode.flow:
            assert {step.actor_from, step.actor_to} <= actors
            assert step.action
            if step.command:
                assert step.command in mode.commands
