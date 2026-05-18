from typer.testing import CliRunner

from agentic_project_kit.action_specs import SafetyClass, built_in_action_specs, get_action_spec, render_action_spec
from agentic_project_kit.cli import app

def test_builtin_action_specs_include_expected_actions():
    specs = built_in_action_specs()
    assert set(specs) >= {"pr-check-merge", "release-verify", "doi-record", "finalize-release"}
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

def test_actions_list_cli_is_read_only():
    result = CliRunner().invoke(app, ["actions", "list"])
    assert result.exit_code == 0
    assert "pr-check-merge" in result.output
    assert "release-verify" in result.output

def test_actions_show_cli_displays_spec():
    result = CliRunner().invoke(app, ["actions", "show", "release-verify"])
    assert result.exit_code == 0
    assert "Action: release-verify" in result.output
    assert "Safety: read_only" in result.output

def test_actions_show_unknown_fails():
    result = CliRunner().invoke(app, ["actions", "show", "missing-action"])
    assert result.exit_code == 1
    assert "unknown action spec" in result.output
