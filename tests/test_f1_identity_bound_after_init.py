"""F1: an origin added after workspace init must not block work start.

The baseline projection then carries the fallback name (project name or folder) as repository
identity. When nothing else changed, check_projection classifies the difference as a late identity
binding; work start continues and work finish regenerates the package (G4 live-run probe 0085).
"""
from __future__ import annotations

import subprocess

from agentic_project_kit.cli_commands import human_workflows
from agentic_project_kit.external_handoff_projection import IDENTITY_BOUND_AFTER_INIT, check_projection
from agentic_project_kit.successor_handoff_package import write_successor_handoff_package


def _git(root, *args):
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)


def _workspace_without_origin(root):
    from agentic_project_kit.successor_handoff_package import _external_long_term_sources
    from agentic_project_kit.workspace import load_workspace

    config = root / ".agentic/config.yaml"
    config.parent.mkdir(parents=True)
    config.write_text("kit_schema_version: 1\nproject: {name: external-demo, type: generic}\n")
    ws = load_workspace(root)
    for relative in _external_long_term_sources(ws):
        path = root / relative
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("version: 1\n" if path.suffix == ".yaml" else "# Workspace authority\n")
    ws.status_path().write_text("# Workspace Status\n")
    ws.handoff_file("README.md").write_text("# Workspace Handoff\n")
    for args in (
        ["init", "-b", "main"], ["config", "user.email", "fixture@example.invalid"],
        ["config", "user.name", "Fixture"], ["config", "maintenance.auto", "false"], ["config", "gc.auto", "0"],
    ):
        _git(root, *args)
    write_successor_handoff_package(root)
    _git(root, "add", ".")
    _git(root, "commit", "-m", "Initial")
    assert check_projection(root)["status"] == "PASS"
    return ws


def test_origin_added_after_init_is_classified_as_identity_binding(tmp_path):
    _workspace_without_origin(tmp_path)
    _git(tmp_path, "remote", "add", "origin", "https://github.com/ExampleOwner/live.git")
    result = check_projection(tmp_path)
    assert result["status"] == "FAIL"
    assert result["code"] == IDENTITY_BOUND_AFTER_INIT
    assert result["identity_binding"] == {"stored": "external-demo", "origin": "ExampleOwner/live"}
    assert set(result["changed_inputs"]) >= {"repository_name"}


def test_identity_binding_plus_another_change_still_blocks(tmp_path):
    ws = _workspace_without_origin(tmp_path)
    _git(tmp_path, "remote", "add", "origin", "https://github.com/ExampleOwner/live.git")
    ws.status_path().write_text("# Workspace Status\n\nChanged authority\n")
    assert check_projection(tmp_path)["code"] == "projection_inputs_changed"


def test_refreshed_package_with_origin_is_current(tmp_path):
    _workspace_without_origin(tmp_path)
    _git(tmp_path, "remote", "add", "origin", "https://github.com/ExampleOwner/live.git")
    write_successor_handoff_package(tmp_path)
    assert check_projection(tmp_path)["code"] == "projection_current"


def test_work_start_continues_only_on_identity_binding(monkeypatch):
    failed = human_workflows._failed_local_step("post-merge-check", "STATE=NEEDS_SUCCESSOR_PACKAGE_REFRESH")
    monkeypatch.setattr(human_workflows, "_run_step", lambda name, argv, **kwargs: dict(failed))
    monkeypatch.setattr(human_workflows, "_identity_bound_after_init", lambda root: None)
    assert human_workflows._start_post_merge_check_step()["ok"] is False

    binding = {"stored": "external-demo", "origin": "ExampleOwner/live"}
    monkeypatch.setattr(human_workflows, "_identity_bound_after_init", lambda root: binding)
    step = human_workflows._start_post_merge_check_step()
    assert step["ok"] is True and step["name"] == "post-merge-check"
    assert "ExampleOwner/live replaces external-demo" in step["stdout"]


def test_identity_bound_after_init_reads_the_classification(tmp_path):
    _workspace_without_origin(tmp_path)
    assert human_workflows._identity_bound_after_init(tmp_path) is None
    _git(tmp_path, "remote", "add", "origin", "https://github.com/ExampleOwner/live.git")
    assert human_workflows._identity_bound_after_init(tmp_path) == {
        "stored": "external-demo", "origin": "ExampleOwner/live",
    }
