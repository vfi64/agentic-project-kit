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
