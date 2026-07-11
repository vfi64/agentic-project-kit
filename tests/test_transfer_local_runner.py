from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import yaml
from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.command_manifest import load_manifest
from agentic_project_kit.instruction_lint import command_manifest_ack_line
from agentic_project_kit.transfer_local_runner import run_local_transfer
from tests.test_rule_source_validator import write_minimal_sources


def _init_repo(root: Path) -> None:
    subprocess.run(["git", "init"], cwd=root, check=True, stdout=subprocess.PIPE)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=root, check=True)
    subprocess.run(
        ["git", "remote", "add", "origin", "git@github.com:vfi64/agentic-project-kit.git"],
        cwd=root,
        check=True,
    )
    subprocess.run(
        ["git", "commit", "--allow-empty", "-m", "init"],
        cwd=root,
        check=True,
        stdout=subprocess.PIPE,
    )


def _seed_command_manifest(root: Path) -> str:
    manifest = load_manifest(Path("."))
    target = root / "docs/reference/agentic-kit-commands.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return command_manifest_ack_line(manifest)


def _write_transfer_order(root: Path, *, include_ack: bool = True) -> None:
    ack = _seed_command_manifest(root)
    payload = root / ".agentic/transfer/payloads/example.txt"
    payload.parent.mkdir(parents=True)
    payload.write_text("example payload\n", encoding="utf-8")
    digest = hashlib.sha256(payload.read_bytes()).hexdigest()
    order = {
        "id": "local-run-test",
        "title": "Local run test",
        "safety": "bounded-local-text-write",
        "report_path": "docs/reports/command_runs/local-run-test.md",
        "actions": [
            {
                "type": "write_text_file",
                "target_path": "generated/example.txt",
                "payload_path": ".agentic/transfer/payloads/example.txt",
                "sha256": digest,
            }
        ],
    }
    inbox = root / ".agentic/transfer/inbox/current.yaml"
    inbox.parent.mkdir(parents=True)
    body = yaml.safe_dump(order, sort_keys=False)
    if include_ack:
        body = ack + "\n" + body
    inbox.write_text(body, encoding="utf-8")


def _commit_all(root: Path, message: str) -> None:
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    subprocess.run(["git", "commit", "-m", message], cwd=root, check=True, stdout=subprocess.PIPE)


def _prepare_acknowledged_transfer_repo(root: Path) -> None:
    write_minimal_sources(root)
    _write_transfer_order(root)
    _commit_all(root, "Add minimal sources and transfer order")
    result = CliRunner().invoke(app, ["rules", "acknowledge", "--root", str(root)])
    assert result.exit_code == 0, result.output


def test_run_local_transfer_inspects_applies_and_reports_state(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    _prepare_acknowledged_transfer_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    result = run_local_transfer(tmp_path)

    assert result.transfer_id == "local-run-test"
    assert result.result_status == "PASS"
    assert result.returncode == 0
    assert result.inspect["result_status"] == "PENDING"
    assert result.apply is not None
    assert result.apply["result_status"] == "PASS"
    assert result.state["primary_state"] == "BLOCKED"
    assert (tmp_path / "generated/example.txt").read_text(encoding="utf-8") == "example payload\n"


def test_run_local_cli_emits_json(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    _prepare_acknowledged_transfer_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(app, ["transfer", "run-local"])

    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["schema_version"] == 1
    assert data["transfer_id"] == "local-run-test"
    assert data["result_status"] == "PASS"
    assert data["inspect"]["result_status"] == "PENDING"
    assert data["apply"]["result_status"] == "PASS"


def test_run_local_help_lists_command():
    result = CliRunner().invoke(app, ["transfer", "--help"])

    assert result.exit_code == 0
    assert "run-local" in result.stdout


def test_run_local_blocks_without_rule_acknowledgement(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    _write_transfer_order(tmp_path, include_ack=False)
    _commit_all(tmp_path, "Add transfer order without acknowledgement")
    monkeypatch.chdir(tmp_path)

    result = run_local_transfer(tmp_path)

    assert result.result_status == "BLOCKED"
    assert result.returncode == 2
    assert result.apply is None
    assert result.next_action == "Transfer blocked because run_next_command is false."
    assert "missing_rule_acknowledgement" in result.state["reasons"]
    assert not (tmp_path / "generated/example.txt").exists()


def test_run_local_refuses_instruction_lint_block_before_command(
    tmp_path,
    monkeypatch,
):
    _init_repo(tmp_path)
    write_minimal_sources(tmp_path)
    _seed_command_manifest(tmp_path)

    order = {
        "id": "local-run-lint-block",
        "title": "Local run lint block",
        "safety": "bounded-local-command",
        "report_path": "docs/reports/command_runs/local-run-lint-block.md",
        "actions": [
            {
                "type": "run_command",
                "command": ["git", "push"],
            }
        ],
    }
    inbox = tmp_path / ".agentic/transfer/inbox/current.yaml"
    inbox.parent.mkdir(parents=True, exist_ok=True)
    manifest = load_manifest(tmp_path)
    inbox.write_text(
        command_manifest_ack_line(manifest) + "\n" + yaml.safe_dump(order, sort_keys=False),
        encoding="utf-8",
    )
    _commit_all(tmp_path, "Add blocked transfer order")

    result = CliRunner().invoke(
        app,
        ["rules", "acknowledge", "--root", str(tmp_path)],
    )
    assert result.exit_code == 0, result.output

    called = False

    def fake_run_command_action(root, action):
        nonlocal called
        called = True
        raise AssertionError("blocked command must not execute")

    monkeypatch.setattr(
        "agentic_project_kit.transfer_runner._run_command_action",
        fake_run_command_action,
    )
    monkeypatch.chdir(tmp_path)

    result = run_local_transfer(tmp_path)

    assert result.result_status == "FAIL"
    assert result.returncode == 2
    assert result.apply is not None
    assert result.apply["instruction_lint"]["result_status"] == "BLOCKED"
    assert "RAW_REPLACED" in result.apply["instruction_lint"]["blockers"]
    assert called is False
