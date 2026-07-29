from typer.testing import CliRunner

from dataclasses import replace

from agentic_project_kit.action_specs import (
    CURRENT_HANDOFF_MUTATION,
    CURRENT_HANDOFF_TARGET_PATH,
    DPA_ACTION_SURFACE_WRITER_ID,
    SafetyClass,
    built_in_action_specs,
    get_action_spec,
    render_action_spec,
    validate_current_handoff_action_surfaces,
)
from agentic_project_kit.cli import app

def test_builtin_action_specs_include_expected_actions():
    specs = built_in_action_specs()
    assert set(specs) >= {
        "pr-check-merge",
        "release-verify",
        "release-prepare",
        "doi-record",
        "finalize-release",
    }
    assert specs["release-verify"].safety_class == SafetyClass.READ_ONLY
    assert specs["pr-check-merge"].safety_class == SafetyClass.REMOTE_MUTATION

def test_all_action_specs_have_parameters_and_evidence():
    for spec in built_in_action_specs().values():
        assert spec.action_id
        assert spec.title
        assert spec.parameters
        assert spec.preconditions
        assert spec.postconditions
        assert spec.evidence
        assert spec.dry_run_default is True

def test_render_action_spec_contains_safety_and_preconditions():
    rendered = render_action_spec(get_action_spec("pr-check-merge"))
    assert "Safety: remote_mutation" in rendered
    assert "Preconditions:" in rendered
    assert "mergeStateStatus CLEAN" in rendered

def test_current_handoff_mutating_action_specs_have_dpa_surface_routes():
    specs = built_in_action_specs()

    assert validate_current_handoff_action_surfaces(specs) == ()
    for spec in specs.values():
        if CURRENT_HANDOFF_MUTATION not in spec.allowed_mutations:
            continue
        assert spec.dpa_surface_writer_id == DPA_ACTION_SURFACE_WRITER_ID
        assert spec.dpa_target_path == CURRENT_HANDOFF_TARGET_PATH
        assert spec.dpa_selected_writer_ids
        assert spec.dpa_lifecycle_route

def test_current_handoff_action_surface_validation_rejects_missing_dpa_route():
    specs = built_in_action_specs()
    specs["doi-record"] = replace(specs["doi-record"], dpa_selected_writer_ids=(), dpa_lifecycle_route=())

    errors = validate_current_handoff_action_surfaces(specs)

    assert "doi-record: missing selected DPA lifecycle writer route" in errors
    assert "doi-record: missing DPA lifecycle route command" in errors


def test_current_handoff_action_surface_validation_rejects_unapproved_action_id():
    specs = built_in_action_specs()
    specs["rogue-handoff-writer"] = replace(
        specs["release-verify"],
        action_id="rogue-handoff-writer",
        allowed_mutations=(CURRENT_HANDOFF_MUTATION,),
        dpa_surface_writer_id=DPA_ACTION_SURFACE_WRITER_ID,
        dpa_target_path=CURRENT_HANDOFF_TARGET_PATH,
        dpa_selected_writer_ids=("WRT-CH-002",),
        dpa_lifecycle_route=("agentic-kit release prepare --write",),
    )

    errors = validate_current_handoff_action_surfaces(specs)

    assert (
        "rogue-handoff-writer: CURRENT_HANDOFF mutation is not an approved action surface"
        in errors
    )


def test_render_action_spec_displays_dpa_routing():
    rendered = render_action_spec(get_action_spec("release-prepare"))

    assert "DPA current handoff routing:" in rendered
    assert "surface writer: WRT-CH-004" in rendered
    assert "selected lifecycle writers: WRT-CH-002" in rendered
    assert "agentic-kit release prepare --write" in rendered

def test_actions_list_cli_is_read_only():
    result = CliRunner().invoke(app, ["actions", "list"])
    assert result.exit_code == 0
    assert "pr-check-merge" in result.output
    assert "release-verify" in result.output

def test_actions_show_cli_displays_spec():
    result = CliRunner().invoke(app, ["actions", "show", "release-prepare"])
    assert result.exit_code == 0
    assert "Action: release-prepare" in result.output
    assert "Safety: local_only" in result.output
    assert "DPA current handoff routing:" in result.output

def test_actions_show_unknown_fails():
    result = CliRunner().invoke(app, ["actions", "show", "missing-action"])
    assert result.exit_code == 1
    assert "unknown action spec" in result.output
