"""Projection bytes must participate in the existing signed update plan."""

from dataclasses import replace
import hashlib
from pathlib import Path
import runpy

import pytest


@pytest.mark.parametrize("origin", [
    "https://github.com/example/fixture.git",
    'path\\with"quote; and space',
    "https://github.com/example/répô.git",
])
def test_preview_origin_config_is_valid_git_syntax(tmp_path, monkeypatch, origin):
    import json
    import subprocess
    from agentic_project_kit import repo_identity
    from agentic_project_kit.kit_update_projection import preview_target_projection

    root = tmp_path / "consumer"
    fixture_type = runpy.run_path(str(Path(__file__).with_name("test_kit_update.py")))["Fixture"]
    fixture_type(root)
    monkeypatch.setattr(repo_identity, "_origin_url_from_git_config", lambda root: origin)

    def run(argv, **kwargs):
        payload = json.loads(Path(argv[-1]).read_bytes())
        config = tmp_path / "syntax.config"
        config.write_text(payload["git_config"], encoding="utf-8")
        actual = subprocess.run(["git", "config", "--file", str(config), "--get", "remote.origin.url"],
                                capture_output=True, text=True)
        assert actual.returncode == 0, actual.stderr
        assert actual.stdout[:-1] == origin
        return subprocess.CompletedProcess(argv, 0, json.dumps({"supported": False, "files": {}}), "")

    assert preview_target_projection(root.resolve(), Path("/fixture/python"), {}, run) == {}


@pytest.mark.parametrize("legacy_111_payload", [False, True])
def test_target_preview_preserves_distinct_origin_inputs(tmp_path, monkeypatch, legacy_111_payload):
    import json
    import os
    import subprocess
    from agentic_project_kit.external_handoff_projection import collect_projection_inputs, input_hashes, check_projection
    from agentic_project_kit.greenfield_retest_runtime import prepare_owned_runtime
    from agentic_project_kit.kit_update_projection import preview_target_projection
    from agentic_project_kit.successor_handoff_package import write_successor_handoff_package
    from agentic_project_kit.workspace_init import build_workspace_init_plan, execute_workspace_init

    env = dict(os.environ)
    python = prepare_owned_runtime(tmp_path / "target", env, console=False)
    root = tmp_path / "consumer"
    root.mkdir()
    origin = "https://github.com/example/remote-identity.git"
    for args in (["init", "-b", "main"], ["remote", "add", "origin", origin]):
        subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)
    execute_workspace_init(build_workspace_init_plan(root, name="different-project", execute=True))
    subprocess.run([str(python), "-I", "-m", "agentic_project_kit.cli", "commands",
                    "sync-entrypoints", "--root", str(root), "--execute", "--json"],
                   env=env, check=True, capture_output=True)
    write_successor_handoff_package(root)

    def run(argv, **kwargs):
        if legacy_111_payload:
            path = Path(argv[-1])
            payload = json.loads(path.read_bytes())
            # Exact origin serialization emitted by published 1.1.11.
            payload["git_config"] = '[remote "origin"]\n\turl = ' + json.dumps(origin) + "\n"
            path.write_text(json.dumps(payload))
        return subprocess.run(argv, cwd=root, env=env, capture_output=True,
                              text=not kwargs.get("binary", False), check=False)

    preview = preview_target_projection(root.resolve(), python, {}, run)
    package = ".agentic/state/handoff/packages/latest/"
    context = json.loads(preview[package + "successor_context.yaml"])
    assert context["repo"]["full_name"] == "example/remote-identity"
    hashes = json.loads(preview[package + "validation_report.json"])["input_hashes"]
    actual = collect_projection_inputs(root)
    for key in ("repository_name", "execution_contract"):
        assert hashes[key] == input_hashes(actual)[key], key
    assert check_projection(root)["status"] == "PASS"
    assert all((root / name).read_bytes() == content for name, content in preview.items())


def _newer_than_running() -> str:
    from agentic_project_kit import __version__
    major, minor, patch = (int(part) for part in __version__.split(".")[:3])
    return f"{major}.{minor}.{patch + 1}"


def test_target_preview_transfers_large_inputs_without_large_process_arguments(tmp_path):
    import base64
    import json
    import subprocess
    from agentic_project_kit.kit_update_projection import preview_target_projection

    fixture_type = runpy.run_path(str(Path(__file__).with_name("test_kit_update.py")))["Fixture"]
    fixture_type(tmp_path)
    reference = tmp_path / "docs/reference/agentic-kit-commands.json"
    reference.parent.mkdir(parents=True, exist_ok=True)
    reference.write_bytes(b"x" * 180_000)
    paths = []

    def run(argv, **kwargs):
        assert max(map(len, argv)) < 128 * 1024, "Linux rejects oversized individual exec arguments"
        path = Path(argv[-1])
        paths.append(path)
        payload = json.loads(path.read_bytes())
        assert base64.b64decode(payload["files"]["docs/reference/agentic-kit-commands.json"]) == reference.read_bytes()
        return subprocess.CompletedProcess(argv, 0, json.dumps({"supported": False, "files": {}}), "")

    assert preview_target_projection(tmp_path.resolve(), Path("/fixture/python"), {}, run) == {}
    assert paths and not paths[0].exists()


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
    # The planner previews the target projection only for a target at or above its own version (never on a
    # downgrade). A fixed target such as "1.1.10" stopped satisfying that once release preparation raised the
    # package version (release 1.1.11, PR #2714), so the target follows the running version.
    target = _newer_than_running()
    fixture.target = replace(fixture.target, artifacts=({**fixture.target.artifacts[0], "version": target},))
    desired = {
        ".agentic/config.yaml": (tmp_path / ".agentic/config.yaml").read_bytes() + b"handoff: {projection_contract_min: 2}\n",
        ".gitignore": b"/.agentic/tmp/handoff/runtime_identity.json\n",
        ".agentic/state/handoff/packages/latest/validation_report.json": b'{"projection_contract_version":2}\n',
    }
    monkeypatch.setattr(kit_update_projection, "preview_target_projection", lambda *args: desired)
    plan = build_update_plan(tmp_path.resolve(), target, fixture.run,
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


@pytest.mark.parametrize("running", ["1.1.10", "1.1.11", "1.2.0"])
def test_the_projection_plan_does_not_depend_on_the_running_release(tmp_path, monkeypatch, running):
    """Release preparation raises the package version; the signed plan must still bind the projection of a newer
    target (regression for the release 1.1.11 CI failure of the test above)."""
    import agentic_project_kit
    from agentic_project_kit import kit_update_projection
    from agentic_project_kit.kit_update import build_update_plan

    monkeypatch.setattr(agentic_project_kit, "__version__", running)
    target = _newer_than_running()
    fixture_type = runpy.run_path(str(Path(__file__).with_name("test_kit_update.py")))["Fixture"]
    fixture = fixture_type(tmp_path)
    fixture.target = replace(fixture.target, artifacts=({**fixture.target.artifacts[0], "version": target},))
    desired = {".gitignore": b"/.agentic/tmp/handoff/runtime_identity.json\n"}
    monkeypatch.setattr(kit_update_projection, "preview_target_projection", lambda *args: desired)
    plan = build_update_plan(tmp_path.resolve(), target, fixture.run,
                             prepare=lambda *args: fixture.target, discover=fixture.discover)
    assert ".gitignore" in plan.payload["changed_paths"]
