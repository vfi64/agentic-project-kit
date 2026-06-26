from pathlib import Path

from agentic_project_kit.cockpit import (
    BOUNDED,
    CockpitAction,
    DESTRUCTIVE,
    READ_ONLY,
    cockpit_actions,
    cockpit_registry_contract_as_json_data,
    run_cockpit_action,
    validate_cockpit_action_registry,
)


def test_default_cockpit_action_registry_is_valid() -> None:
    assert validate_cockpit_action_registry() == []
    data = cockpit_registry_contract_as_json_data()
    assert data["schema_version"] == 1
    assert data["registry_only"] is True
    assert data["valid"] is True
    assert data["errors"] == []
    assert "git.status" in data["allowed_action_ids"]
    assert data["allowed_safety_classes"] == [READ_ONLY, BOUNDED, DESTRUCTIVE]

def test_registry_rejects_duplicate_action_ids() -> None:
    action = cockpit_actions()[0]
    errors = validate_cockpit_action_registry([action, action])
    assert any("duplicate action_id: git.status" in error for error in errors)

def test_registry_rejects_invalid_safety_and_empty_command() -> None:
    action = CockpitAction("bad.action", "Bad", "bad", (), "unsafe", "Bad action.", "Run bad action")
    errors = validate_cockpit_action_registry([action])
    assert any("invalid safety for bad.action: unsafe" in error for error in errors)
    assert any("empty command for bad.action" in error for error in errors)

def test_unknown_action_is_blocked_by_registry_only_contract(tmp_path: Path) -> None:
    result = run_cockpit_action("not.in.registry", tmp_path)
    assert result.allowed is False
    assert result.executed is False
    assert result.result_status == "FAIL"
    assert result.safety == "unknown"
    assert result.next_allowed_actions == ("cockpit.actions",)
    assert "Unknown cockpit action" in result.message
