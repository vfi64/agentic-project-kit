"""``workspace init --publication``: the publication policy is chosen through the Kit, not by hand.

Owner decision 2026-11-15 (journey J6, variant a): the documented path sets ``publication`` with a
Kit command, so no fixture or person edits ``.agentic/config.yaml``. The option works for the plain
init and for the signed recovery of a generated project; the routes that name the recovery keep it.
"""
from __future__ import annotations

import json
import os
import shlex
import subprocess
from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from agentic_project_kit.blocked_route import KIND_HUMAN, KIND_KIT, route_problems
from agentic_project_kit.cli import app
from agentic_project_kit.cli_commands.routed_output import kit_command
from agentic_project_kit.dpa_workspace_init_projection import DPA_WORKSPACE_INIT_MANIFEST_PATH
from agentic_project_kit.publication_policy import publication_policy_for
from agentic_project_kit.workspace import ALLOWED_PUBLICATION_POLICIES, DEFAULT_PUBLICATION_POLICY

runner = CliRunner()


@pytest.fixture(autouse=True)
def _git_identity(monkeypatch):
    """`init` commits only with a Git identity; CI runners have none (KIT-GF-104)."""
    for key, value in {"GIT_AUTHOR_NAME": "Fixture", "GIT_AUTHOR_EMAIL": "fixture@example.invalid",
                       "GIT_COMMITTER_NAME": "Fixture", "GIT_COMMITTER_EMAIL": "fixture@example.invalid"}.items():
        monkeypatch.setenv(key, value)


def _json(args: list[str], code: int) -> dict:
    result = runner.invoke(app, [*args, "--json"])
    assert result.exit_code == code, result.output
    return json.loads(result.output)


def _repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    return root


def _generated_project(tmp_path: Path) -> Path:
    previous = Path.cwd()
    os.chdir(tmp_path)
    try:
        result = runner.invoke(app, ["init", "demo", "--type", "python-lib", "--no-pre-commit", "--json"])
    finally:
        os.chdir(previous)
    assert result.exit_code == 0, result.output
    root = tmp_path / "demo"
    # Exercise the historical partial-init recovery route explicitly. Fresh init
    # now includes the whole operating layer and needs no recovery.
    preserved = {".agentic/project.yaml", ".agentic/todo.yaml", DPA_WORKSPACE_INIT_MANIFEST_PATH}
    for path in (root / ".agentic").rglob("*"):
        if path.is_file() and path.relative_to(root).as_posix() not in preserved:
            path.unlink()
    return root


def _publication(root: Path) -> str:
    return yaml.safe_load((root / ".agentic/config.yaml").read_text(encoding="utf-8"))["publication"]


def test_default_policy_is_unchanged(tmp_path: Path):
    plan = _json(["workspace", "init", "--root", str(_repo(tmp_path))], 0)
    assert plan["manifest"]["publication"] == DEFAULT_PUBLICATION_POLICY


@pytest.mark.parametrize("policy", sorted(ALLOWED_PUBLICATION_POLICIES))
def test_every_policy_is_written_and_read_back(tmp_path: Path, policy: str):
    root = _repo(tmp_path)
    plan = _json(["workspace", "init", "--root", str(root), "--publication", policy], 0)
    assert plan["manifest"]["publication"] == policy and plan["written"] is False
    assert not (root / ".agentic").exists()
    _json(["workspace", "init", "--root", str(root), "--publication", policy, "--execute"], 0)
    assert _publication(root) == policy and publication_policy_for(root).value == policy


def test_invalid_policy_fails_before_any_write(tmp_path: Path):
    root = _repo(tmp_path)
    payload = _json(["workspace", "init", "--root", str(root), "--publication", "pypi", "--execute"], 1)
    assert payload["result_status"] == "FAIL" and payload["code"] == "INVALID_PUBLICATION"
    assert payload["next_command_kind"] == KIND_HUMAN and route_problems(payload) == []
    assert not (root / ".agentic").exists()


def test_remove_still_recognizes_the_generated_manifest(tmp_path: Path):
    root = _repo(tmp_path)
    _json(["workspace", "init", "--root", str(root), "--publication", "none", "--execute"], 0)
    plan = _json(["workspace", "remove", "--root", str(root)], 0)
    assert plan["result_status"] == "PASS" and not plan["blockers"]
    assert ".agentic/config.yaml" in json.dumps(plan["files_to_remove"])


def test_recovery_writes_the_policy_and_its_signature_binds_it(tmp_path: Path):
    root = _generated_project(tmp_path)
    args = ["workspace", "init", "--recover-partial", "--root", str(root)]
    default = _json(args, 0)
    plan = _json([*args, "--publication", "none"], 0)
    assert plan["result_status"] == "AWAITING_APPROVAL"
    assert plan["approval_signature"] != default["approval_signature"]
    stale = _json([*args, "--publication", "github", "--execute", "--expected-signature", plan["approval_signature"],
                   "--approved-by", "owner", "--consent-source", "test"], 2)
    assert stale["result_status"] == "BLOCKED" and not (root / ".agentic/config.yaml").exists()
    done = _json([*args, "--publication", "none", "--execute", "--expected-signature", plan["approval_signature"],
                  "--approved-by", "owner", "--consent-source", "test"], 0)
    assert done["result_status"] == "PASS" and _publication(root) == "none"
    # Repeating keeps an initialized workspace; a different policy is not changed by recovery.
    assert _json([*args, "--publication", "none"], 0)["result_status"] == "PASS"
    other = _json([*args, "--publication", "github"], 2)
    assert other["result_status"] == "BLOCKED" and "does not change the publication policy" in other["reason"]
    assert _publication(root) == "none"


def test_recovery_rejects_an_invalid_policy(tmp_path: Path):
    root = _generated_project(tmp_path)
    payload = _json(["workspace", "init", "--recover-partial", "--root", str(root), "--publication", "pypi"], 2)
    assert payload["result_status"] == "BLOCKED" and "invalid publication policy" in payload["reason"]
    assert payload["next_command_kind"] == KIND_HUMAN and route_problems(payload) == []


def test_routes_to_the_recovery_keep_the_policy(tmp_path: Path):
    root = _generated_project(tmp_path)
    expected = kit_command("workspace", "init", "--recover-partial", "--publication", "none", root=root)
    foreign = _json(["workspace", "init", "--root", str(root), "--publication", "none"], 1)
    assert foreign["code"] == "FOREIGN_AGENTIC" and foreign["next_command"] == expected
    assert foreign["next_command_kind"] == KIND_KIT and route_problems(foreign) == []
    injected = _json(["workspace", "init", "--root", str(root), "--recover-partial", "--inject-ci",
                      "--publication", "none"], 2)
    assert injected["code"] == "RECOVERY_NO_INJECTION" and injected["next_command"] == expected
    # The named command is the plan that writes this policy.
    plan = _json(shlex.split(expected)[1:], 0)
    assert plan["result_status"] == "AWAITING_APPROVAL"
    assert any(path == ".agentic/config.yaml" for path in plan["changed_paths"])
