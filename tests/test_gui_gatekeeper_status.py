import json
from types import SimpleNamespace

from agentic_project_kit.action_registry import SafetyClass
from agentic_project_kit.gui_gatekeeper_status import (
    build_gui_gatekeeper_status,
    classify_gui_gatekeeper_action,
    render_gui_gatekeeper_status,
)


def test_gui_gatekeeper_status_allows_readonly_actions_in_clean_repo(tmp_path, monkeypatch):
    agentic = tmp_path / ".agentic"
    agentic.mkdir()
    (agentic / "workflow_state").write_text("IDLE\n", encoding="utf-8")
    (agentic / "current_work.yaml").write_text("state: READY\n", encoding="utf-8")

    monkeypatch.setattr("agentic_project_kit.gui_gatekeeper_status._git_branch", lambda root: "main")
    monkeypatch.setattr("agentic_project_kit.gui_gatekeeper_status._git_dirty", lambda root: False)

    actions = [
        SimpleNamespace(name="git.status", safety_class=SafetyClass.READ_ONLY, mutation_scope="none"),
        SimpleNamespace(name="workflow.go", safety_class=SafetyClass.LOCAL_ONLY, mutation_scope="working-tree-files"),
    ]

    status = build_gui_gatekeeper_status(tmp_path, actions=actions)

    assert status.branch == "main"
    assert status.git_dirty is False
    assert status.workflow_state == "IDLE"
    assert status.current_work_present is True
    assert status.current_work_state == "READY"
    assert status.ready_for_read_only_actions is True
    assert status.ready_for_mutating_actions is True
    assert status.blockers == ()
    assert status.action_statuses[0].enabled is True
    assert status.action_statuses[1].enabled is True
    assert status.action_statuses[1].reason == "local-only action allowed in clean GUI gatekeeper state"


def test_gui_gatekeeper_status_blocks_readonly_actions_when_dirty(tmp_path, monkeypatch):
    agentic = tmp_path / ".agentic"
    agentic.mkdir()
    (agentic / "workflow_state").write_text("IDLE\n", encoding="utf-8")

    monkeypatch.setattr("agentic_project_kit.gui_gatekeeper_status._git_branch", lambda root: "feature/x")
    monkeypatch.setattr("agentic_project_kit.gui_gatekeeper_status._git_dirty", lambda root: True)

    actions = [
        SimpleNamespace(name="git.status", safety_class=SafetyClass.READ_ONLY, mutation_scope="none"),
    ]

    status = build_gui_gatekeeper_status(tmp_path, actions=actions)

    assert status.ready_for_read_only_actions is False
    assert status.ready_for_mutating_actions is False
    assert "working tree is dirty" in status.blockers
    assert status.action_statuses[0].enabled is False
    assert status.action_statuses[0].reason == "read-only action blocked because working tree is dirty"


def test_gui_gatekeeper_action_classifier_blocks_remote_actions_even_when_clean():
    action = SimpleNamespace(
        name="pr-check-merge",
        safety_class=SafetyClass.REMOTE_MUTATION,
        mutation_scope="remote",
    )

    result = classify_gui_gatekeeper_action(action, git_dirty=False, local_only_allowed=True)

    assert result.enabled is False
    assert result.reason == "GUI gatekeeper blocks remote mutation actions"


def test_gui_gatekeeper_action_classifier_allows_local_only_when_clean():
    action = SimpleNamespace(
        name="terminal-clean-evidence",
        safety_class=SafetyClass.LOCAL_ONLY,
        mutation_scope="docs/reports/terminal",
    )

    result = classify_gui_gatekeeper_action(action, git_dirty=False, local_only_allowed=True)

    assert result.enabled is True
    assert result.reason == "local-only action allowed in clean GUI gatekeeper state"


def test_gui_gatekeeper_action_classifier_blocks_local_only_when_dirty():
    action = SimpleNamespace(
        name="terminal-clean-evidence",
        safety_class=SafetyClass.LOCAL_ONLY,
        mutation_scope="docs/reports/terminal",
    )

    result = classify_gui_gatekeeper_action(action, git_dirty=True, local_only_allowed=False)

    assert result.enabled is False
    assert result.reason == "local-only action blocked because GUI gatekeeper is not clean"


def test_gui_gatekeeper_rendering_is_deterministic(tmp_path, monkeypatch):
    agentic = tmp_path / ".agentic"
    agentic.mkdir()
    (agentic / "workflow_state").write_text("IDLE\n", encoding="utf-8")

    monkeypatch.setattr("agentic_project_kit.gui_gatekeeper_status._git_branch", lambda root: "main")
    monkeypatch.setattr("agentic_project_kit.gui_gatekeeper_status._git_dirty", lambda root: False)

    actions = [
        SimpleNamespace(name="git.status", safety_class=SafetyClass.READ_ONLY, mutation_scope="none"),
    ]

    rendered = render_gui_gatekeeper_status(build_gui_gatekeeper_status(tmp_path, actions=actions))

    assert rendered.splitlines() == [
        "GUI_GATEKEEPER_STATUS",
        "branch=main",
        "git_dirty=false",
        "workflow_state=IDLE",
        "current_work_present=false",
        "current_work_state=<none>",
        "ready_for_read_only_actions=true",
        "ready_for_mutating_actions=true",
        "blockers=<none>",
        "action=git.status;safety=read-only;enabled=true;reason=read-only action allowed in clean GUI gatekeeper state",
    ]

def test_gui_gatekeeper_status_json_data_has_stable_schema(tmp_path, monkeypatch):
    agentic = tmp_path / ".agentic"
    agentic.mkdir()
    (agentic / "workflow_state").write_text("IDLE\n", encoding="utf-8")

    monkeypatch.setattr("agentic_project_kit.gui_gatekeeper_status._git_branch", lambda root: "main")
    monkeypatch.setattr("agentic_project_kit.gui_gatekeeper_status._git_dirty", lambda root: False)

    actions = [
        SimpleNamespace(name="git.status", safety_class=SafetyClass.READ_ONLY, mutation_scope="none"),
    ]

    from agentic_project_kit.gui_gatekeeper_status import gui_gatekeeper_status_as_json_data

    data = gui_gatekeeper_status_as_json_data(build_gui_gatekeeper_status(tmp_path, actions=actions))

    assert data["schema_version"] == 1
    assert data["branch"] == "main"
    assert data["git_dirty"] is False
    assert data["ready_for_read_only_actions"] is True
    assert data["ready_for_mutating_actions"] is True
    assert data["actions"][0]["action_id"] == "git.status"
    assert data["actions"][0]["enabled"] is True


def test_cockpit_gatekeeper_status_cli_renders_text():
    from typer.testing import CliRunner
    from agentic_project_kit.cli import app

    result = CliRunner().invoke(app, ["cockpit", "gatekeeper-status"])

    assert result.exit_code == 0, result.output
    assert "GUI_GATEKEEPER_STATUS" in result.output
    assert "ready_for_read_only_actions=" in result.output
    assert "ready_for_mutating_actions=" in result.output


def test_cockpit_gatekeeper_status_cli_outputs_json():
    from typer.testing import CliRunner
    from agentic_project_kit.cli import app

    result = CliRunner().invoke(app, ["cockpit", "gatekeeper-status", "--json"])

    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["schema_version"] == 1
    assert "actions" in data
    assert "ready_for_mutating_actions" in data

