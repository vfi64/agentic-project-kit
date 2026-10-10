from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess

import pytest
from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.kit_installation import (
    InstallationObservation,
    InterpreterCandidate,
    KitInstallationResolution,
)
from agentic_project_kit.kit_update import run_kit_update
from agentic_project_kit.kit_update_artifacts import PreparedTarget, released_artifacts
from agentic_project_kit.kit_update_config import DEFAULT_INDEX_URL, parse_kit_update_config
from agentic_project_kit.kit_update_pins import plan_ci_pins
from agentic_project_kit.kit_update_runtime import UpdateBlocked, UpdateRunner
from agentic_project_kit.workspace import load_workspace
from agentic_project_kit.workspace_init import (
    CI_TEMPLATE_PATH,
    CI_INJECTION_TARGET,
    MANAGED_CI_HEADER,
)


SOURCE = b'name: customized\njobs:\n  test:\n    steps:\n      - run: python -m pip install "agentic-project-kit==1.0.18"\n      - run: python app_specific_check.py\n'


class Fixture:
    def __init__(self, root):
        self.root = root
        self.version = "1.0.18"
        self.calls = []
        self.branch = "codex/update-kit"
        self.head = "a" * 40
        self.sync_status = "PASS"
        self.sync_ack = "1" * 12
        self.check_status = "PASS"
        self.doctor_rc = 0
        self.install_rc = 0
        self.on_preflight = None
        self.on_install = None
        self.identity_count = 0
        for name, content in {
            ".agentic/config.yaml": b"kit_schema_version: 2\nproject: {name: external, type: generic}\nhygiene: {doc_lifecycle: 'off'}\n",
            CI_TEMPLATE_PATH: SOURCE,
            CI_INJECTION_TARGET: MANAGED_CI_HEADER.encode() + b"\n" + SOURCE,
            ".venv/pyvenv.cfg": b"home = base-python\n",
        }.items():
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        self.wheel = root / ".agentic/tmp/fixture/agentic_project_kit-1.0.19-py3-none-any.whl"
        self.wheel.parent.mkdir(parents=True)
        self.wheel.write_bytes(b"immutable-wheel-fixture")
        digest = hashlib.sha256(self.wheel.read_bytes()).hexdigest()
        self.target = PreparedTarget(
            root / ".agentic/tmp/preview/bin/python",
            (self.wheel,),
            (
                {
                    "name": "agentic-project-kit",
                    "version": "1.0.19",
                    "filename": self.wheel.name,
                    "sha256": digest,
                    "url": "https://example.org/wheel",
                },
            ),
        )

    def discover(self, root, **kwargs):
        prefix = self.root / ".venv"
        item = InterpreterCandidate(prefix / "bin/python", "workspace_venv", prefix)
        observed = InstallationObservation(
            item,
            "FOUND",
            "installed",
            self.version,
            str(prefix),
            "/base",
            str(prefix / "lib/site-packages"),
            str(prefix / "lib/site-packages/agentic_project_kit/__init__.py"),
            wheel_sha256=self.target.artifacts[0]["sha256"] if self.version == "1.0.19" else "",
        )
        return KitInstallationResolution("FOUND", observed, (observed,))

    def prepare(self, tmp, python, index_url, version, run):
        assert index_url == DEFAULT_INDEX_URL
        assert version == "1.0.19"
        return self.target

    def run(self, argv, **kwargs):
        self.calls.append(argv)
        data = None
        rc = 0
        text = ""
        if argv[:3] == ["git", "symbolic-ref", "--short"]:
            self.identity_count += 1
            if self.on_preflight and self.identity_count == 2:
                self.on_preflight()
            text = self.branch
        elif argv[:3] == ["git", "rev-parse", "--show-toplevel"]:
            text = str(self.root)
        elif argv[:3] == ["git", "rev-parse", "HEAD"]:
            text = self.head
        elif "-c" in argv and "managed_ci_template_text" in argv[3]:
            from agentic_project_kit.workspace_ci_update import is_kit_written_ci_template
            from agentic_project_kit.workspace_ci_template import render_workspace_ci

            data = {"kit_written": is_kit_written_ci_template(json.loads(argv[4])),
                    "template": render_workspace_ci("1.0.19")}
        elif "packages" in argv[-1] and "-c" in argv:
            data = {"python": "Python 3.13", "packages": [["agentic-project-kit", self.version]]}
        elif "sync-entrypoints" in argv:
            paths = ["docs/reference/agentic-kit-commands.json", "AGENTS.md"]
            data = {
                "result_status": self.sync_status,
                "manifest_sha": self.sync_ack,
                "changed_paths": paths,
            }
            if "--execute" in argv:
                for path in paths:
                    target = self.root / path
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text("updated by target interpreter\n")
        elif "pip" in argv and "install" in argv:
            rc = self.install_rc
            if not rc:
                self.version = "1.0.19"
                if self.on_install:
                    self.on_install()
        elif "check" in argv:
            data = {"status": self.check_status, "error_count": 0, "errors": []}
        elif "doctor" in argv:
            rc = self.doctor_rc
            text = "Overall: PASS" if not rc else "Overall: FAIL"
        else:
            pytest.fail(f"unexpected argv: {argv[:5]}")
        return subprocess.CompletedProcess(
            argv, rc, json.dumps(data) if data is not None else text, ""
        )

    def update(self, **kwargs):
        return run_kit_update(
            self.root,
            "1.0.19",
            run=self.run,
            discover=self.discover,
            prepare=self.prepare,
            **kwargs,
        )

    @property
    def installs(self):
        return [argv for argv in self.calls if "pip" in argv and "install" in argv]


@pytest.fixture
def workspace(tmp_path):
    return Fixture(tmp_path)


def test_pip_runner_disables_unsigned_system_and_environment_configuration(tmp_path, monkeypatch):
    import os

    observed = {}

    def run(argv, **kwargs):
        observed.update(kwargs)
        return subprocess.CompletedProcess(argv, 0, "", "")

    monkeypatch.setattr(subprocess, "run", run)
    monkeypatch.setenv("PIP_CONFIG_FILE", "/owner/custom/pip.conf")
    UpdateRunner(tmp_path, tmp_path / "update.jsonl")(
        ["python", "-I", "-m", "pip", "--isolated", "install"]
    )
    assert observed["env"]["PIP_CONFIG_FILE"] == os.devnull


def test_malformed_environment_inventory_blocks_before_target_installation(workspace):
    original = workspace.run

    def run(argv, **kwargs):
        if "-c" in argv:
            return subprocess.CompletedProcess(
                argv, 0, '{"python": "x", "packages": [[null, "1"]]}', ""
            )
        return original(argv, **kwargs)

    workspace.run = run
    result = workspace.update()
    assert result["blocker"] == "invalid_environment_inventory"
    assert workspace.installs == []


def test_concurrent_file_change_during_install_preserves_new_content(workspace):
    plan = workspace.update()
    path = workspace.root / CI_TEMPLATE_PATH
    replacement = b"concurrent owner edit\n"
    workspace.on_install = lambda: path.write_bytes(replacement)
    result = workspace.update(execute=True, expected_signature=plan["approval_signature"])
    assert result["result_status"] == "BLOCKED"
    assert result["blocker"] == "workspace_files_changed_after_install"
    assert result["completed_steps"] == ["install"]
    assert path.read_bytes() == replacement


def test_concurrent_branch_change_during_install_blocks_file_writes(workspace):
    plan = workspace.update()
    workspace.on_install = lambda: setattr(workspace, "branch", "codex/other")
    result = workspace.update(execute=True, expected_signature=plan["approval_signature"])
    assert result["blocker"] == "workspace_branch_or_head_changed_after_install"
    assert (workspace.root / CI_TEMPLATE_PATH).read_bytes() == SOURCE


def test_doctor_zero_exit_with_fail_text_is_blocked(workspace):
    plan = workspace.update()
    original = workspace.run

    def run(argv, **kwargs):
        if "doctor" in argv:
            return subprocess.CompletedProcess(argv, 0, "Overall: FAIL", "")
        return original(argv, **kwargs)

    workspace.run = run
    result = workspace.update(execute=True, expected_signature=plan["approval_signature"])
    assert result["result_status"] == "BLOCKED"
    assert result["blocker"] == "workspace_doctor_blocked"


def test_same_version_without_wheel_provenance_requires_install(workspace):
    workspace.version = "1.0.19"
    original = workspace.discover

    def discover(*args, **kwargs):
        from dataclasses import replace

        resolution = original(*args, **kwargs)
        installation = replace(resolution.installation, wheel_sha256="")
        return KitInstallationResolution("FOUND", installation, (installation,))

    workspace.discover = discover
    assert workspace.update()["plan"]["actions"][0] == "install_released_wheels"


def test_dry_run_lists_install_both_pins_and_entrypoints_with_signature(workspace):
    result = workspace.update()
    assert result["result_status"] == "AWAITING_APPROVAL"
    assert len(result["approval_signature"]) == 24
    assert {CI_TEMPLATE_PATH, CI_INJECTION_TARGET, "AGENTS.md"} <= set(result["changed_paths"])
    assert result["plan"]["actions"] == [
        "install_released_wheels",
        "update_ci_pins",
        "sync_entrypoints",
        "check",
        "doctor",
    ]
    assert workspace.installs == []
    assert (workspace.root / CI_TEMPLATE_PATH).read_bytes() == SOURCE
    assert not (workspace.root / "AGENTS.md").exists()
    assert Path(result["state_path"]).exists()


def test_signed_execute_uses_same_interpreter_and_preserves_custom_ci(workspace):
    plan = workspace.update()
    result = workspace.update(execute=True, expected_signature=plan["approval_signature"])
    assert result["result_status"] == "PASS", result
    assert result["installed_version"] == "1.0.19"
    assert result["manifest_ack"] == "1" * 12
    assert len(workspace.installs) == 1
    assert workspace.installs[0][0] == str(workspace.root / ".venv/bin/python")
    assert "--no-index" in workspace.installs[0]
    expected = SOURCE.replace(b"1.0.18", b"1.0.19")
    assert (workspace.root / CI_TEMPLATE_PATH).read_bytes() == expected
    assert (
        workspace.root / CI_INJECTION_TARGET
    ).read_bytes() == MANAGED_CI_HEADER.encode() + b"\n" + expected
    executed_sync = next(
        argv for argv in workspace.calls if "sync-entrypoints" in argv and "--execute" in argv
    )
    assert executed_sync[0] == str(workspace.root / ".venv/bin/python")
    assert result["completed_steps"] == ["install", "ci_pins", "entrypoints", "check", "doctor"]


def test_signature_does_not_depend_on_staging_paths_or_log_ids(workspace):
    a = workspace.update()
    workspace.target = PreparedTarget(
        workspace.root / ".agentic/tmp/other-preview/bin/python",
        workspace.target.wheels,
        workspace.target.artifacts,
    )
    b = workspace.update()
    assert a["approval_signature"] == b["approval_signature"]
    assert a["state_path"] != b["state_path"]


@pytest.mark.parametrize("change", ["wrong_signature", "file", "head", "environment", "artifact"])
def test_stale_signature_has_no_target_effect(workspace, change):
    initial = workspace.update()
    signature = initial["approval_signature"]
    if change == "wrong_signature":
        signature = "wrong"
    elif change == "file":
        (workspace.root / "AGENTS.md").write_text("changed\n")
    elif change == "head":
        workspace.head = "b" * 40
    elif change == "environment":
        workspace.version = "1.0.17"
    elif change == "artifact":
        a = dict(workspace.target.artifacts[0], sha256="f" * 64)
        workspace.target = PreparedTarget(workspace.target.python, workspace.target.wheels, (a,))
    result = workspace.update(execute=True, expected_signature=signature)
    assert result["result_status"] == "BLOCKED"
    assert "signature" in result["blocker"]
    assert workspace.installs == []
    assert (workspace.root / CI_TEMPLATE_PATH).read_bytes() == SOURCE


def test_last_preflight_rechecks_files_after_signature(workspace):
    initial = workspace.update()
    workspace.identity_count = 0
    workspace.on_preflight = lambda: (workspace.root / "AGENTS.md").write_text("concurrent edit")
    result = workspace.update(execute=True, expected_signature=initial["approval_signature"])
    assert result["result_status"] == "BLOCKED"
    assert result["blocker"] == "workspace_files_changed"
    assert workspace.installs == []


def test_corrupted_download_blocks_before_install(workspace):
    initial = workspace.update()
    workspace.wheel.write_bytes(b"corrupted")
    result = workspace.update(execute=True, expected_signature=initial["approval_signature"])
    assert result["result_status"] == "BLOCKED"
    assert result["blocker"] == "release_artifact_hash_mismatch"
    assert workspace.installs == []


@pytest.mark.parametrize("mode", ["install", "check", "doctor"])
def test_failure_preserves_actual_partial_state_and_receipt(workspace, mode):
    plan = workspace.update()
    if mode == "install":
        workspace.install_rc = 1
    elif mode == "check":
        workspace.check_status = "FAIL"
    else:
        workspace.doctor_rc = 1
    result = workspace.update(execute=True, expected_signature=plan["approval_signature"])
    assert result["result_status"] == "BLOCKED"
    assert result["mutation_started"]
    assert json.loads(Path(result["state_path"]).read_text())["result_status"] == "BLOCKED"
    if mode == "install":
        assert (workspace.root / CI_TEMPLATE_PATH).read_bytes() == SOURCE
    else:
        assert workspace.version == "1.0.19"
        assert b"1.0.19" in (workspace.root / CI_TEMPLATE_PATH).read_bytes()
        assert "ci_pins" in result["completed_steps"]


def test_rc_zero_blocked_preview_is_not_a_pass(workspace):
    workspace.sync_status = "BLOCKED"
    result = workspace.update()
    assert result["result_status"] == "BLOCKED"
    assert workspace.installs == []


def test_same_version_after_partial_failure_does_not_reinstall(workspace):
    initial = workspace.update()
    workspace.check_status = "FAIL"
    workspace.update(execute=True, expected_signature=initial["approval_signature"])
    workspace.calls.clear()
    workspace.check_status = "PASS"
    fresh = workspace.update()
    assert fresh["plan"]["actions"][0] == "verify_installed_version"
    result = workspace.update(execute=True, expected_signature=fresh["approval_signature"])
    assert result["result_status"] == "PASS"
    assert not workspace.installs


@pytest.mark.parametrize("branch", ["main", "master"])
def test_protected_primary_branch_is_refused(workspace, branch):
    workspace.branch = branch
    result = workspace.update()
    assert result["result_status"] == "BLOCKED"
    assert "work_branch_required" in result["blocker"]
    assert workspace.installs == []


def test_undeclared_release_is_refused(workspace):
    def unavailable(*args):
        raise UpdateBlocked("requested_release_not_resolved")

    workspace.prepare = unavailable
    result = workspace.update()
    assert result["result_status"] == "BLOCKED"
    assert workspace.installs == []


def test_symlinked_projection_is_refused(workspace, tmp_path):
    outside = tmp_path.parent / "outside-projection"
    outside.write_text("preserve")
    (workspace.root / "AGENTS.md").symlink_to(outside)
    result = workspace.update()
    assert result["result_status"] == "BLOCKED"
    assert outside.read_text() == "preserve"


@pytest.mark.parametrize("ending", [b"\n", b"\r\n"])
def test_pin_plan_preserves_custom_bytes_and_line_endings(ending):
    source = SOURCE.replace(b"\n", ending)
    workflow = MANAGED_CI_HEADER.encode() + ending + source
    desired = plan_ci_pins(source, workflow, "1.0.19")
    assert desired[CI_TEMPLATE_PATH] == source.replace(b"1.0.18", b"1.0.19")
    assert desired[CI_INJECTION_TARGET] == workflow.replace(b"1.0.18", b"1.0.19")


@pytest.mark.parametrize(
    "source,workflow",
    [
        (SOURCE, b"unmanaged\n" + SOURCE),
        (SOURCE, MANAGED_CI_HEADER.encode() + b"\n" + SOURCE + b"# changed workflow\n"),
        (SOURCE + SOURCE, MANAGED_CI_HEADER.encode() + b"\n" + SOURCE + SOURCE),
        (
            SOURCE.replace(b"==1.0.18", b">=1.0.18"),
            MANAGED_CI_HEADER.encode() + b"\n" + SOURCE.replace(b"==1.0.18", b">=1.0.18"),
        ),
        (
            b"# agentic-project-kit==1.0.18\n",
            MANAGED_CI_HEADER.encode() + b"\n# agentic-project-kit==1.0.18\n",
        ),
    ],
)
def test_ambiguous_or_unmanaged_ci_is_refused(source, workflow):
    with pytest.raises(ValueError):
        plan_ci_pins(source, workflow, "1.0.19")


@pytest.mark.parametrize(
    "arguments",
    [
        b"other-package # agentic-project-kit==1.0.18",
        b"other-package; echo agentic-project-kit==1.0.18",
        b'"$(echo agentic-project-kit==1.0.18)"',
        b'"other-package agentic-project-kit==1.0.18"',
    ],
)
def test_pin_in_comment_shell_expression_or_another_argument_is_refused(arguments):
    source = b"jobs:\n  steps:\n    - run: python -m pip install " + arguments + b"\n"
    with pytest.raises(ValueError):
        plan_ci_pins(source, MANAGED_CI_HEADER.encode() + b"\n" + source, "1.0.19")


@pytest.mark.parametrize(
    "value",
    [
        {"unknown": 1},
        [],
        {"interpreter": False},
        {"index_url": "http://example.com/simple"},
        {"index_url": "https://user:secret@example.com/simple"},
        {"index_url": "https://example.com/simple?secret=token"},
    ],
)
def test_invalid_update_config_is_refused(value):
    with pytest.raises(ValueError):
        parse_kit_update_config(value)


def test_optional_config_is_loaded_by_workspace(workspace):
    config = workspace.root / ".agentic/config.yaml"
    config.write_text(
        config.read_text()
        + "kit:\n  interpreter: env/bin/python\n  index_url: https://index.example/simple\n"
    )
    parsed = load_workspace(workspace.root).kit
    assert parsed.interpreter == "env/bin/python"
    assert parsed.index_url == "https://index.example/simple"
    assert parse_kit_update_config(None).index_url == DEFAULT_INDEX_URL


def report_entry(**changes):
    result = {
        "metadata": {"name": "agentic-project-kit", "version": "1.0.19"},
        "is_yanked": False,
        "download_info": {
            "url": "https://index.example/agentic_project_kit-1.0.19-py3-none-any.whl",
            "archive_info": {"hashes": {"sha256": "a" * 64}},
        },
    }
    result.update(changes)
    return result


def test_exact_binary_release_resolution_is_accepted():
    artifacts = released_artifacts({"install": [report_entry()]}, "1.0.19")
    assert artifacts[0]["sha256"] == "a" * 64


@pytest.mark.parametrize(
    "entry",
    [
        report_entry(is_yanked=True),
        report_entry(metadata={"name": "agentic-project-kit", "version": "1.0.18"}),
        report_entry(
            download_info={
                "url": "https://index.example/a.tar.gz",
                "archive_info": {"hashes": {"sha256": "a" * 64}},
            }
        ),
        report_entry(
            download_info={"url": "https://index.example/a.whl", "archive_info": {"hashes": {}}}
        ),
    ],
)
def test_yanked_wrong_or_unhashed_source_release_is_refused(entry):
    with pytest.raises(UpdateBlocked):
        released_artifacts({"install": [entry]}, "1.0.19")


def test_cli_failure_is_one_json_document(tmp_path):
    result = CliRunner().invoke(
        app, ["kit", "update", "--root", str(tmp_path), "--version", "1.0.19", "--json"]
    )
    assert result.exit_code == 2
    assert json.loads(result.stdout)["result_status"] == "BLOCKED"
    assert "Traceback" not in result.stdout


def test_new_route_declares_remote_read_signature_and_cli_parameters():
    from agentic_project_kit.command_manifest import build_current_reference

    data = build_current_reference()
    command = next(c for c in data["commands"] if c["qualified_name"] == "agentic-kit kit update")
    assert command["remote_effects"] == ["network_read"]
    assert command["safety"] == "BOUNDED"
    assert command["surface"] == "orchestrator"
    assert command["dry_run_available"]
    options = {o for p in command["params"] for o in p.get("opts", [])}
    assert {"--version", "--execute", "--expected-signature", "--root", "--json"} <= options


def test_subprocess_log_preserves_intent_and_result(tmp_path):
    import sys

    log = tmp_path / "calls.jsonl"
    run = UpdateRunner(tmp_path, log)
    result = run([sys.executable, "-c", 'print("evidence")'])
    assert result.returncode == 0
    records = [json.loads(line) for line in log.read_text().splitlines()]
    assert [r["event"] for r in records] == ["START", "END"]
    assert records[1]["rc"] == 0
    assert records[1]["stdout"] == "evidence\n"
    assert records[1]["duration"] >= 0


def test_target_runtime_upgrades_registered_managed_template(workspace):
    from agentic_project_kit.workspace_ci_template import render_workspace_ci

    source = (Path(__file__).parent / "fixtures/workspace_ci_1_0_22.yaml").read_bytes()
    (workspace.root / CI_TEMPLATE_PATH).write_bytes(source)
    (workspace.root / CI_INJECTION_TARGET).write_bytes(MANAGED_CI_HEADER.encode() + b"\n" + source)
    plan = workspace.update()
    assert plan["result_status"] == "AWAITING_APPROVAL"
    assert (workspace.root / CI_TEMPLATE_PATH).read_bytes() == source
    result = workspace.update(execute=True, expected_signature=plan["approval_signature"])
    assert result["result_status"] == "PASS"
    assert (workspace.root / CI_TEMPLATE_PATH).read_text() == render_workspace_ci("1.0.19")
    assert "workspace-refresh" in (workspace.root / CI_INJECTION_TARGET).read_text()


def test_ci_template_replacement_is_bound_to_target_version():
    with pytest.raises(ValueError, match="invalid_target_template_pin"):
        plan_ci_pins(SOURCE, MANAGED_CI_HEADER.encode() + b"\n" + SOURCE, "1.0.19",
                     target_template=SOURCE.decode())
