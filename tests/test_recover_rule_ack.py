import json
import subprocess

import pytest
import yaml
from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.cli_commands import human_workflows
from agentic_project_kit.cli_commands.transfer_context_helpers import _restore_known_volatile_paths
from agentic_project_kit.workspace import default_hygiene_manifest
from tests.test_rule_source_validator import write_external_workspace_sources


def git(root, *args):
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=True).stdout.strip()


def init_workspace(root):
    git(root, "init", "-b", "main")
    git(root, "config", "user.email", "test@example.invalid")
    git(root, "config", "user.name", "Test User")
    write_external_workspace_sources(root)
    config_path = root / ".agentic/config.yaml"
    config = yaml.safe_load(config_path.read_text())
    config["hygiene"] = default_hygiene_manifest()
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")
    (root / "product.txt").write_text("before\n", encoding="utf-8")
    git(root, "add", ".")
    git(root, "commit", "-m", "Initialize external workspace")
    git(root, "switch", "-c", "codex/recover")


def test_recover_then_transfer_commit_without_reacknowledging(tmp_path, monkeypatch):
    init_workspace(tmp_path)
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    ack = runner.invoke(app, ["rules", "acknowledge", "--json"])
    assert ack.exit_code == 0, ack.output
    path = tmp_path / ".agentic/rule_ack/current.json"
    before = path.read_bytes()
    (tmp_path / "product.txt").write_text("after\n", encoding="utf-8")

    def local_step(name, argv, **kwargs):
        # CI status is unrelated to acknowledgement preservation; no external network.
        if name == "patch-cycle-status":
            return human_workflows._noop_step(name, "Skipped remote CI in external fixture")
        result = runner.invoke(app, argv[1:])
        return {"name": name, "argv": argv, "returncode": result.exit_code, "ok": result.exit_code == 0, "stdout": result.stdout, "stderr": ""}
    monkeypatch.setattr(human_workflows, "_run_step", local_step)
    recovered = runner.invoke(app, ["work", "recover", "--json"])
    # Dirty product work can remain BLOCKED; it must be preserved for the commit.
    assert recovered.exit_code in {0, 2}, recovered.output
    assert path.read_bytes() == before
    assert (tmp_path / "product.txt").read_text() == "after\n"
    committed = runner.invoke(app, ["transfer", "commit", "--branch", "codex/recover", "--message", "Fix product", "--path", "product.txt", "--json"])
    assert committed.exit_code == 0, committed.output
    assert json.loads(committed.stdout)["result_status"] == "PASS"
    assert git(tmp_path, "show", "HEAD:product.txt") == "after"


@pytest.mark.parametrize("tracked", [False, True])
def test_volatile_restore_preserves_ack_bytes_even_for_legacy_tracked_state(tmp_path, tracked):
    init_workspace(tmp_path)
    ack = tmp_path / ".agentic/rule_ack/current.json"
    ack.parent.mkdir(parents=True)
    ack.write_text('{"snapshot_id":"old"}\n')
    if tracked:
        git(tmp_path, "add", str(ack))
        git(tmp_path, "commit", "-m", "Legacy tracked ack")
    ack.write_text('{"snapshot_id":"current"}\n')
    before = ack.read_bytes()
    result = _restore_known_volatile_paths(tmp_path)
    assert result["ok"]
    assert ack.read_bytes() == before


def test_commit_missing_ack_names_acknowledge_first_and_emits_only_json(tmp_path, monkeypatch):
    init_workspace(tmp_path)
    monkeypatch.chdir(tmp_path)
    (tmp_path / "product.txt").write_text("after\n")
    result = CliRunner().invoke(app, ["transfer", "commit", "--message", "Fix", "--path", "product.txt", "--json"])
    assert result.exit_code == 2, result.output
    payload = json.loads(result.stdout)
    assert "missing_rule_acknowledgement" in payload["reasons"]
    assert payload["next_action"].startswith("agentic-kit rules acknowledge")
    assert git(tmp_path, "log", "-1", "--format=%s") == "Initialize external workspace"
