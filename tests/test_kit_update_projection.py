"""Projection bytes must participate in the existing signed update plan."""

from dataclasses import replace
import hashlib
from pathlib import Path
import runpy

import pytest


def test_same_version_update_cannot_silently_remove_projection_contract(tmp_path, monkeypatch):
    import json
    import subprocess
    from agentic_project_kit.kit_update import build_update_plan
    from agentic_project_kit.kit_update_runtime import UpdateBlocked
    from agentic_project_kit import kit_update_projection

    fixture_type = runpy.run_path(str(Path(__file__).with_name("test_kit_update.py")))["Fixture"]
    fixture = fixture_type(tmp_path)
    fixture.target = replace(fixture.target, artifacts=({**fixture.target.artifacts[0], "version": "1.1.10"},))
    monkeypatch.setattr(kit_update_projection, "preview_target_projection", lambda *args: {})

    def run(argv, **kwargs):
        result = fixture.run(argv, **kwargs)
        if "-c" in argv and "m.distributions()" in argv[argv.index("-c") + 1]:
            data = json.loads(result.stdout)
            data["projection_contract_version"] = 2
            return subprocess.CompletedProcess(argv, result.returncode, json.dumps(data), result.stderr)
        return result

    with pytest.raises(UpdateBlocked, match="projection_contract_downgrade_refused"):
        build_update_plan(tmp_path.resolve(), "1.1.10", run,
                          prepare=lambda *args: fixture.target, discover=fixture.discover)


def test_signed_update_plan_binds_projection_paths_and_bytes(tmp_path, monkeypatch):
    from agentic_project_kit.kit_update import build_update_plan, signature
    from agentic_project_kit import kit_update_projection

    fixture_type = runpy.run_path(str(Path(__file__).with_name("test_kit_update.py")))["Fixture"]
    fixture = fixture_type(tmp_path)
    fixture.target = replace(fixture.target, artifacts=({**fixture.target.artifacts[0], "version": "1.1.10"},))
    desired = {
        ".agentic/config.yaml": (tmp_path / ".agentic/config.yaml").read_bytes() + b"handoff: {projection_contract_min: 2}\n",
        ".gitignore": b"/.agentic/tmp/handoff/runtime_identity.json\n",
        ".agentic/state/handoff/packages/latest/validation_report.json": b'{"projection_contract_version":2}\n',
    }
    monkeypatch.setattr(kit_update_projection, "preview_target_projection", lambda *args: desired)
    plan = build_update_plan(tmp_path.resolve(), "1.1.10", fixture.run,
                             prepare=lambda *args: fixture.target, discover=fixture.discover)
    assert set(desired) <= set(plan.payload["changed_paths"])
    assert plan.payload["projection_hashes_after"] == {
        path: hashlib.sha256(content).hexdigest() for path, content in desired.items()
    }
    previous = signature(plan.payload)
    changed = {**plan.payload, "projection_hashes_after": {**plan.payload["projection_hashes_after"], ".gitignore": "0" * 64}}
    assert signature(changed) != previous


def test_same_version_different_wheel_is_explicitly_reinstalled(tmp_path):
    from agentic_project_kit.kit_update import run_kit_update
    from agentic_project_kit.kit_installation import KitInstallationResolution

    fixture_type = runpy.run_path(str(Path(__file__).with_name("test_kit_update.py")))["Fixture"]
    fixture = fixture_type(tmp_path)
    fixture.version = "1.0.19"
    installed = False

    def discover(root, **kwargs):
        resolution = fixture.discover(root, **kwargs)
        if installed:
            return resolution
        observation = replace(resolution.installation, wheel_sha256="0" * 64)
        return KitInstallationResolution("FOUND", observation, (observation,))

    def run(argv, **kwargs):
        nonlocal installed
        result = fixture.run(argv, **kwargs)
        if "pip" in argv and "install" in argv and not result.returncode:
            installed = True
        return result

    options = {"run": run, "prepare": fixture.prepare, "discover": discover}
    plan = run_kit_update(tmp_path, "1.0.19", **options)
    result = run_kit_update(tmp_path, "1.0.19", execute=True, expected_signature=plan["approval_signature"], **options)
    assert result["result_status"] == "PASS", result
    installation = next(argv for argv in fixture.calls if "pip" in argv and "install" in argv)
    assert "--force-reinstall" in installation
