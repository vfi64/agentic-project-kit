"""Installation return reuses the existing signed, two-phase update executor."""

from dataclasses import replace
import json
from pathlib import Path
import runpy
import subprocess

import pytest


@pytest.mark.parametrize("failure", [None, "install", "check", "doctor", "changed_paths"])
def test_bound_return_uses_update_executor_and_never_passes_partial_failure(tmp_path, monkeypatch, failure):
    from agentic_project_kit.kit_update import run_kit_update
    from agentic_project_kit import kit_return
    from agentic_project_kit.workspace_init import CI_TEMPLATE_PATH, CI_INJECTION_TARGET

    fixture_type = runpy.run_path(str(Path(__file__).with_name("test_kit_update.py")))["Fixture"]
    fixture = fixture_type(tmp_path)
    fixture.version = "1.1.11"
    fixture.branch = "main"
    fixture.target = replace(fixture.target, artifacts=({**fixture.target.artifacts[0], "version": "1.1.10"},))
    for name in (CI_TEMPLATE_PATH, CI_INJECTION_TARGET):
        path = tmp_path / name
        path.write_bytes(path.read_bytes().replace(b"==1.0.18", b"==1.1.10"))
    proof = {"adoption_id": "a" * 32, "target_version": "1.1.10", "installed_version_before": "1.1.11",
             "return_pr": 102, "return_merge": "b" * 40, "receipt_sha256": "c" * 64}
    monkeypatch.setattr(kit_return, "verify_install_return", lambda *args, **kwargs: proof)
    monkeypatch.setattr(kit_return, "record_install_return", lambda *args, **kwargs: None)
    if failure == "install":
        fixture.install_rc = 1
    if failure == "check":
        fixture.check_status = "FAIL"
    if failure == "doctor":
        fixture.doctor_rc = 1

    def run(argv, **kwargs):
        if "sync-entrypoints" in argv:
            fixture.calls.append(argv)
            paths = ["AGENTS.md"] if failure == "changed_paths" else []
            return subprocess.CompletedProcess(argv, 0, json.dumps({"result_status": "PASS", "manifest_sha": fixture.sync_ack, "changed_paths": paths}), "")
        result = fixture.run(argv, **kwargs)
        if "pip" in argv and "install" in argv and result.returncode == 0:
            fixture.version = "1.1.10"
        return result

    def discover(root, **kwargs):
        from agentic_project_kit.kit_installation import KitInstallationResolution
        resolution = fixture.discover(root, **kwargs)
        if fixture.version == "1.1.10":
            observation = replace(resolution.installation, wheel_sha256=fixture.target.artifacts[0]["sha256"])
            return KitInstallationResolution("FOUND", observation, (observation,))
        return resolution

    kwargs = {"run": run, "prepare": lambda *args: fixture.target, "discover": discover,
              "return_adoption": "a" * 32}
    plan = run_kit_update(tmp_path, "1.1.10", **kwargs)
    if failure == "changed_paths":
        assert plan["result_status"] == "BLOCKED"
        assert "return_requires_unchanged_workspace_plan" in plan["blocker"]
        return
    assert plan["result_status"] == "AWAITING_APPROVAL", plan
    assert plan["changed_paths"] == []
    assert "return-install" in plan["next_action"]
    result = run_kit_update(tmp_path, "1.1.10", execute=True, expected_signature=plan["approval_signature"], **kwargs)
    if failure:
        assert result["result_status"] != "PASS"
        assert result["mutation_started"] is True
    else:
        assert result["result_status"] == "PASS", result
        assert result["installed_version"] == "1.1.10"
        assert result["completed_steps"][-2:] == ["check", "doctor"]
        checks = [argv for argv in fixture.calls if "check" in argv or "doctor" in argv]
        assert all(argv[:4] == [str(tmp_path / ".venv/bin/python"), "-I", "-m", "agentic_project_kit.cli"] for argv in checks)


@pytest.mark.parametrize("route,handler", [("return-revert", "run_return_revert"), ("return-install", "run_install_return")])
def test_return_cli_is_a_thin_bound_route(tmp_path, monkeypatch, route, handler):
    from typer.testing import CliRunner
    from agentic_project_kit.cli import app
    from agentic_project_kit import kit_return

    calls = []

    def fake(root, adoption_id, **kwargs):
        calls.append((root, adoption_id, kwargs))
        return {"result_status": "AWAITING_APPROVAL", "next_action": "Review signed plan"}

    monkeypatch.setattr(kit_return, handler, fake)
    result = CliRunner().invoke(app, ["kit", route, "--root", str(tmp_path), "--adoption", "a" * 32, "--json"])
    assert result.exit_code == 0, result.output
    assert calls[0][1] == "a" * 32
    assert "--allow-downgrade" not in CliRunner().invoke(app, ["kit", route, "--help"]).output


def test_return_rechecks_evidence_inside_mutation_lock(tmp_path, monkeypatch):
    from agentic_project_kit import kit_return
    from agentic_project_kit.kit_update import run_kit_update
    from agentic_project_kit.kit_update_runtime import UpdateBlocked

    fixture_type = runpy.run_path(str(Path(__file__).with_name("test_kit_update.py")))["Fixture"]
    fixture = fixture_type(tmp_path)
    proof = {"installed_version_before": fixture.version}
    observations = 0

    def verify(*args, **kwargs):
        nonlocal observations
        observations += 1
        if observations == 3:
            raise UpdateBlocked("return_evidence_changed")
        return proof

    monkeypatch.setattr(kit_return, "verify_install_return", verify)
    fixture.target = replace(fixture.target, artifacts=({**fixture.target.artifacts[0], "version": "1.0.18"},))
    kwargs = {"run": fixture.run, "prepare": lambda *args: fixture.target, "discover": fixture.discover,
              "return_adoption": "a" * 32}
    # Same target pins and unchanged entrypoints make the return plan empty.
    fixture.sync_changed = []
    original = fixture.run

    def run(argv, **options):
        if "sync-entrypoints" in argv:
            return subprocess.CompletedProcess(argv, 0, json.dumps({"result_status": "PASS", "manifest_sha": fixture.sync_ack, "changed_paths": []}), "")
        return original(argv, **options)

    kwargs["run"] = run
    plan = run_kit_update(tmp_path, "1.0.18", **kwargs)
    assert plan["result_status"] == "AWAITING_APPROVAL", plan
    result = run_kit_update(tmp_path, "1.0.18", execute=True, expected_signature=plan["approval_signature"], **kwargs)
    assert result["result_status"] == "BLOCKED", result
    assert result.get("mutation_started", False) is False
    assert result["blocker"] == "return_evidence_changed"


def test_existing_work_finish_preserves_verified_v1_return_and_never_claims_completion(monkeypatch, tmp_path):
    from agentic_project_kit.cli_commands import human_workflows

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(human_workflows, "default_agentic_kit", lambda root: "./.venv/bin/agentic-kit")
    monkeypatch.setattr(human_workflows, "default_python", lambda root: "./.venv/bin/python")

    helper = runpy.run_path(str(Path(__file__).with_name("test_human_workflows.py")))["_work_finish_execute"]
    context = {"adoption_id": "a" * 32, "target_version": "1.1.10", "paths": ["src/demo.py"]}
    monkeypatch.setattr(human_workflows, "_return_closeout_preflight", lambda root: context, raising=False)
    result, calls = helper(monkeypatch, handoff_status_stdout="")
    assert not any("chat-switch-complete" in argv for argv in calls)
    payload = json.loads(result.output)
    assert payload["result_status"] != "PASS"
    assert payload["post_merge_handoff"] == "pending_installation_return"
    assert "return-install" in payload["next_action"]
