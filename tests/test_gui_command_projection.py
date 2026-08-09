from pathlib import Path

from agentic_project_kit.command_manifest import load_manifest
from agentic_project_kit.gui_button_catalog import (
    GuiButtonDefinition,
    gui_button_command_projection,
    gui_button_manifest_bindings,
    validate_gui_button_manifest_bindings,
)
from agentic_project_kit.gui_command_projection import (
    GUI_SURFACE_LAYERS,
    build_gui_command_projection,
    resolve_manifest_command,
    validate_gui_command_bindings,
)


def test_gui_command_projection_groups_every_manifest_command_by_surface() -> None:
    manifest = load_manifest(Path("."))
    projection = gui_button_command_projection(manifest=manifest)

    assert projection.ok
    assert projection.command_count == len(manifest["commands"])
    assert len(projection.entries) == projection.command_count
    assert projection.default_layer == "primary"
    assert projection.default_entries == projection.entries_for_layer("primary")
    assert set(projection.surface_counts()) == set(GUI_SURFACE_LAYERS)
    assert projection.layer_counts()["primary"] > 0
    assert projection.layer_counts()["diagnostics"] > 0
    assert projection.layer_counts()["expert"] > 0


def test_gui_command_projection_marks_orchestrators_as_default_primary_layer() -> None:
    manifest = load_manifest(Path("."))
    projection = build_gui_command_projection(manifest=manifest)
    by_name = {entry.qualified_name: entry for entry in projection.entries}

    sync_main = by_name["agentic-kit transfer sync-main"]
    assert sync_main.surface == "orchestrator"
    assert sync_main.layer == "primary"
    assert sync_main in projection.default_entries


def test_gui_button_wrappers_resolve_to_manifest_surfaces() -> None:
    manifest = load_manifest(Path("."))

    assert validate_gui_button_manifest_bindings(manifest=manifest) == ()
    bindings = {binding.source_id: binding for binding in gui_button_manifest_bindings(manifest=manifest)}

    assert bindings["restore-volatile"].qualified_name == (
        "agentic-kit transfer restore-known-volatile"
    )
    assert bindings["restore-volatile"].surface == "primitive"
    assert bindings["work-order-upload"].qualified_name == "agentic-kit work-order upload"
    assert bindings["work-order-upload"].surface == "primitive"
    assert bindings["diagnose"].surface == "diagnostic"


def test_gui_button_binding_validation_blocks_stale_agentic_kit_wrappers() -> None:
    manifest = {
        "commands": [
            {
                "qualified_name": "agentic-kit doctor",
                "surface": "diagnostic",
                "safety": "READ_ONLY",
            }
        ]
    }
    button = GuiButtonDefinition(
        command_id="stale",
        label="Stale",
        category="Test",
        tooltip="Stale wrapper.",
        icon_text="stale",
        safety_class="read-only",
        implementation_state="implemented",
        enabled=True,
        wrapper_command=("agentic-kit", "missing"),
    )

    findings = validate_gui_command_bindings((button,), manifest=manifest)

    assert findings == (
        "stale: wrapper command is not registered in command manifest: agentic-kit missing",
    )


def test_resolve_manifest_command_uses_longest_command_prefix_before_options() -> None:
    manifest = load_manifest(Path("."))

    command = resolve_manifest_command(
        ("agentic-kit", "transfer", "restore-known-volatile", "--json"),
        manifest,
    )

    assert command is not None
    assert command["qualified_name"] == "agentic-kit transfer restore-known-volatile"
