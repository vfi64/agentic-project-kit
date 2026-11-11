"""Current external v2 policy and historical release A behavior."""

import json
import subprocess
import sys

import pytest
from agentic_project_kit import transfer_repo_actions  # Bind the current policy before historical simulations.


@pytest.mark.parametrize("active", [False, True])
def test_external_generation_and_init_follow_one_package_policy(tmp_path, monkeypatch, active):
    from agentic_project_kit import external_projection_policy as policy
    from agentic_project_kit.workspace_init import build_workspace_init_plan, execute_workspace_init
    from agentic_project_kit.successor_handoff_package import write_successor_handoff_package
    from agentic_project_kit.workspace import load_workspace
    import subprocess

    if not active:
        monkeypatch.setattr(policy, "external_projection_contract_version", lambda: 1)
        monkeypatch.setattr(policy, "uses_external_projection_v2", lambda _root: False)
        monkeypatch.setattr("agentic_project_kit.workspace_init.external_projection_contract_version", lambda: 1)
    execute_workspace_init(build_workspace_init_plan(tmp_path, name="external", execute=True))
    ws = load_workspace(tmp_path)
    assert ws.handoff_projection_contract_min == (2 if active else None)
    assert ws.package_file("validation_report.json").exists() is active
    for args in (["init", "-b", "main"], ["config", "user.name", "Fixture"],
                 ["config", "user.email", "fixture@example.invalid"], ["add", "."], ["commit", "-m", "Seed"]):
        subprocess.run(["git", *args], cwd=tmp_path, check=True, capture_output=True)
    result = write_successor_handoff_package(tmp_path)
    saved = json.loads(ws.package_file("validation_report.json").read_bytes())
    assert ("input_digest" in saved) is active
    assert ("generated_head" in saved) is not active
    assert (result.runtime_identity is not None) is active
    assert result.validation_report["status"] == "PASS"


def test_shipped_default_is_projection_v2():
    from agentic_project_kit.external_projection_policy import external_projection_contract_version
    from agentic_project_kit import external_projection_policy
    from agentic_project_kit.kit_update import _INVENTORY

    assert not hasattr(external_projection_policy, "EXTERNAL_PROJECTION_V2_ACTIVE")
    assert external_projection_contract_version() == 2
    inventory = subprocess.run([sys.executable, "-I", "-c", _INVENTORY], capture_output=True, text=True, check=True)
    assert json.loads(inventory.stdout)["projection_contract_version"] == 2


def test_release_a_default_is_not_an_implicit_migration(tmp_path, monkeypatch):
    monkeypatch.setattr("agentic_project_kit.external_projection_policy.external_projection_contract_version", lambda: 1)
    monkeypatch.setattr("agentic_project_kit.external_projection_policy.uses_external_projection_v2", lambda _root: False)
    monkeypatch.setattr("agentic_project_kit.workspace_init.external_projection_contract_version", lambda: 1)
    from agentic_project_kit.external_projection_policy import external_projection_contract_version
    from agentic_project_kit.workspace_init import build_workspace_init_plan, execute_workspace_init
    from agentic_project_kit.checks import check_all

    assert external_projection_contract_version() == 1
    execute_workspace_init(build_workspace_init_plan(tmp_path, name="external", execute=True))
    assert check_all(tmp_path) == []


def test_release_a_target_probes_do_not_treat_module_presence_as_activation(monkeypatch):
    from agentic_project_kit.kit_update import _INVENTORY
    from agentic_project_kit.kit_update_projection import TARGET_PROJECTION_PREVIEW

    # -I starts a separate interpreter; scope the same A policy explicitly
    # inside that process rather than adding a production environment switch.
    def release_a_script(script):
        return (
            "from unittest.mock import patch\n"
            "from agentic_project_kit import external_projection_policy as policy\n"
            "with patch.object(policy, 'external_projection_contract_version', return_value=1):\n"
            f"    exec({script!r})\n"
        )

    inventory = subprocess.run([sys.executable, "-I", "-c", release_a_script(_INVENTORY)], capture_output=True, text=True, check=True)
    assert json.loads(inventory.stdout)["projection_contract_version"] == 1
    preview = subprocess.run([sys.executable, "-I", "-c", release_a_script(TARGET_PROJECTION_PREVIEW)], capture_output=True, text=True)
    assert preview.returncode == 0, preview.stderr
    assert json.loads(preview.stdout) == {"supported": False, "files": {}}


def test_release_a_update_records_adoption_without_a_projection_migration(tmp_path, monkeypatch):
    monkeypatch.setattr("agentic_project_kit.external_projection_policy.external_projection_contract_version", lambda: 1)
    monkeypatch.setattr("agentic_project_kit.external_projection_policy.uses_external_projection_v2", lambda _root: False)
    from pathlib import Path
    import runpy
    from agentic_project_kit import kit_return

    fixture_type = runpy.run_path(str(Path(__file__).with_name("test_kit_update.py")))["Fixture"]
    fixture = fixture_type(tmp_path)
    recorded = []

    def record(root, **kwargs):
        recorded.append(kwargs)
        return {"adoption_id": kwargs["adoption_id"]}

    monkeypatch.setattr(kit_return, "record_adoption", record)
    plan = fixture.update()
    result = fixture.update(execute=True, expected_signature=plan["approval_signature"])
    assert result["result_status"] == "PASS", result
    assert len(recorded) == 1
    assert result["adoption_id"] == recorded[0]["adoption_id"]
    assert recorded[0]["plan"]["installation"]["version"] == "1.0.18"


def test_release_a_malformed_return_evidence_is_a_structured_stop(tmp_path, monkeypatch):
    monkeypatch.setattr("agentic_project_kit.external_projection_policy.uses_external_projection_v2", lambda _root: False)
    monkeypatch.setattr(transfer_repo_actions, "uses_external_projection_v2", lambda _root: False)
    from agentic_project_kit.transfer_repo_actions import post_merge_check
    path = tmp_path / ".agentic/kit-update/ledger.jsonl"
    path.parent.mkdir(parents=True)
    path.write_text("invalid json\n")
    monkeypatch.chdir(tmp_path)
    result = post_merge_check()
    assert result.result_status == "BLOCKED"
    assert "return_ledger_invalid" in result.stderr
