from agentic_project_kit.handoff_applicability import handoff_applicability


def test_legacy_authority_is_required_without_manifest(tmp_path):
    result = handoff_applicability(tmp_path)
    assert result["path"] == str(tmp_path / ".agentic/handoff_state.yaml")
    assert result["state"] == "HANDOFF_REQUIRED"


def test_external_declared_authority_is_single_and_explicit_missing_is_required(tmp_path):
    p = tmp_path / ".agentic/config.yaml"
    p.parent.mkdir()
    p.write_text(
        "kit_schema_version: 2\nproject: {name: external, type: generic}\nprofile: generic\npaths:\n  handoff_state_file: custom/state.yaml\nhygiene:\n  doc_lifecycle: warn\n  review_budgets: {governance: 180}\n"
    )
    result = handoff_applicability(tmp_path)
    assert result["path"] == str(tmp_path / ".agentic/custom/state.yaml")
    assert result["state"] == "NO_PREVIOUS_HANDOFF"
    assert handoff_applicability(tmp_path, "missing.yaml")["state"] == "HANDOFF_REQUIRED"


def test_valid_init_projection_is_not_previous_handoff(tmp_path, monkeypatch):
    from agentic_project_kit.workspace_init import build_workspace_init_plan, execute_workspace_init
    from agentic_project_kit.cli_commands.human_workflows import _external_first_cycle_without_successor_package
    from agentic_project_kit.external_handoff_projection import RUNTIME_PATH

    execute_workspace_init(build_workspace_init_plan(tmp_path, name="external", execute=True))
    assert handoff_applicability(tmp_path)["state"] == "NO_PREVIOUS_HANDOFF"
    assert _external_first_cycle_without_successor_package(tmp_path)
    assert handoff_applicability(tmp_path, "missing.yaml")["state"] == "HANDOFF_REQUIRED"
    runtime = tmp_path / RUNTIME_PATH
    runtime.parent.mkdir(parents=True)
    runtime.write_text("{}")
    assert handoff_applicability(tmp_path)["state"] == "HANDOFF_REQUIRED"
    assert not _external_first_cycle_without_successor_package(tmp_path)


def test_corrupt_init_projection_is_not_a_legitimate_first_cycle(tmp_path, monkeypatch):
    from agentic_project_kit.workspace_init import build_workspace_init_plan, execute_workspace_init
    from agentic_project_kit.cli_commands.human_workflows import _external_first_cycle_without_successor_package

    execute_workspace_init(build_workspace_init_plan(tmp_path, name="external", execute=True))
    package = tmp_path / ".agentic/state/handoff/packages/latest/execution_contract.json"
    package.write_text("{}")
    assert handoff_applicability(tmp_path)["state"] == "HANDOFF_REQUIRED"
    assert not _external_first_cycle_without_successor_package(tmp_path)
