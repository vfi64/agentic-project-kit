from pathlib import Path

CONTRACT = Path("docs/archive/V0.4.0_GUI_ACTION_READINESS_CONTRACT.md")


def test_gui_action_readiness_contract_exists_with_lifecycle_header():
    text = CONTRACT.read_text(encoding="utf-8")
    assert "Status: proposed" in text
    assert "Decision status: proposed" in text
    assert "Lifecycle: active" in text


def test_gui_action_readiness_contract_requires_action_metadata():
    text = CONTRACT.read_text(encoding="utf-8")
    for phrase in [
        "a stable action name",
        "a user-facing description",
        "a safety class",
        "parameter rules or an explicit no-parameter declaration",
        "expected outcomes",
        "evidence behavior",
        "execution-mode requirements",
    ]:
        assert phrase in text


def test_gui_action_readiness_contract_blocks_destructive_mvp_execution():
    text = CONTRACT.read_text(encoding="utf-8")
    assert "Destructive, release, publish, merge, tag, delete, and remote-mutating actions must be disabled" in text
    assert "release-publish" in text
    assert "merge" in text
    assert "tag" in text
    assert "delete" in text


def test_gui_action_readiness_contract_uses_existing_action_layer():
    text = CONTRACT.read_text(encoding="utf-8")
    assert "existing Python action registry or action specs" in text
    assert "must not create a second command registry" in text
    assert "must not call removed shell adapters" in text
    assert "must not bypass the mode guard" in text


def test_current_action_modules_expose_gui_relevant_primitives():
    registry = Path("src/agentic_project_kit/action_registry.py").read_text(encoding="utf-8")
    specs = Path("src/agentic_project_kit/action_specs.py").read_text(encoding="utf-8")
    combined = registry + "\n" + specs
    assert "release-verify" in combined
    assert "release-prep" in combined
    assert "SafetyClass" in combined
    assert "READ_ONLY" in combined or "read-only" in combined


def test_no_tracked_ns_shell_adapters_exist_for_gui_path():
    tracked_shell_adapters = list(Path("tools").glob("ns_*.sh"))
    assert tracked_shell_adapters == []
