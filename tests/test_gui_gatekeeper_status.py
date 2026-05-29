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
    assert status.ready_for_mutating_actions is False
    assert status.blockers == ()
    assert status.action_statuses[0].enabled is True
    assert status.action_statuses[1].enabled is False


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


def test_gui_gatekeeper_action_classifier_blocks_non_readonly_actions_even_when_clean():
    action = SimpleNamespace(
        name="pr-check-merge",
        safety_class=SafetyClass.REMOTE_MUTATION,
        mutation_scope="remote",
    )

    result = classify_gui_gatekeeper_action(action, git_dirty=False)

    assert result.enabled is False
    assert result.reason == "GUI gatekeeper blocks non-read-only actions"


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
        "ready_for_mutating_actions=false",
        "blockers=<none>",
        "action=git.status;safety=read-only;enabled=true;reason=read-only action allowed in clean GUI gatekeeper state",
    ]
