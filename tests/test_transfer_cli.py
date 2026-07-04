from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

import yaml
from typer.testing import CliRunner

from agentic_project_kit.cli import app
from tests.test_rule_source_validator import write_minimal_sources


def _write_order(root: Path) -> None:
    payload = root / ".agentic/transfer/payloads/example.txt"
    payload.parent.mkdir(parents=True)
    payload.write_text("cli payload\n", encoding="utf-8")
    digest = hashlib.sha256(payload.read_bytes()).hexdigest()
    order = {
        "id": "cli-transfer",
        "title": "CLI transfer",
        "safety": "bounded-local-text-write",
        "report_path": "docs/reports/command_runs/cli-transfer.md",
        "actions": [
            {
                "type": "write_text_file",
                "target_path": "generated/cli.txt",
                "payload_path": ".agentic/transfer/payloads/example.txt",
                "sha256": digest,
            }
        ],
    }
    path = root / ".agentic/transfer/inbox/current.yaml"
    path.parent.mkdir(parents=True)
    path.write_text(yaml.safe_dump(order, sort_keys=False), encoding="utf-8")


def _init_repo(root: Path) -> None:
    subprocess.run(["git", "init"], cwd=root, check=True, stdout=subprocess.PIPE)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=root, check=True)
    subprocess.run(
        ["git", "remote", "add", "origin", "git@github.com:vfi64/agentic-project-kit.git"],
        cwd=root,
        check=True,
    )


def _commit_all(root: Path, message: str) -> None:
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    subprocess.run(["git", "commit", "-m", message], cwd=root, check=True, stdout=subprocess.PIPE)


def _prepare_acknowledged_transfer_repo(root: Path) -> None:
    _init_repo(root)
    write_minimal_sources(root)
    _write_order(root)
    _commit_all(root, "Add minimal sources and transfer order")
    result = CliRunner().invoke(app, ["rules", "acknowledge", "--root", str(root)])
    assert result.exit_code == 0, result.output


def test_transfer_inspect_cli_reports_pending_without_writing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_order(tmp_path)

    result = CliRunner().invoke(app, ["transfer", "inspect"])

    assert result.exit_code == 0
    assert "transfer_id=cli-transfer" in result.stdout
    assert "result_status=PENDING" in result.stdout
    assert not (tmp_path / "generated/cli.txt").exists()


def test_transfer_apply_cli_writes_payload_and_report(tmp_path, monkeypatch):
    _prepare_acknowledged_transfer_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(app, ["transfer", "apply"])

    assert result.exit_code == 0
    assert "result_status=PASS" in result.stdout
    assert (tmp_path / "generated/cli.txt").read_text(encoding="utf-8") == "cli payload\n"
    assert (tmp_path / "docs/reports/command_runs/cli-transfer.md").exists()


def test_transfer_inspect_cli_json(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_order(tmp_path)

    result = CliRunner().invoke(app, ["transfer", "inspect", "--json"])

    assert result.exit_code == 0
    assert '"schema_version": 1' in result.stdout
    assert '"transfer_id": "cli-transfer"' in result.stdout


def test_transfer_apply_cli_blocks_without_rule_acknowledgement(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_order(tmp_path)

    result = CliRunner().invoke(app, ["transfer", "apply"])

    assert result.exit_code == 2
    assert '"required_capability": "run_next_command"' in result.stdout
    assert '"result_status": "BLOCKED"' in result.stdout
    assert '"chat_reply": "f"' in result.stdout
    assert '"next_safe_action"' in result.stdout
    assert not (tmp_path / "generated/cli.txt").exists()

def test_sync_main_uses_restore_known_volatile_wrapper_for_mixed_tracked_and_untracked_carriers():
    from pathlib import Path

    source = Path("src/agentic_project_kit/cli_commands/transfer_context_flow.py").read_text(encoding="utf-8")

    assert 'step("restore-before-sync", ["./.venv/bin/agentic-kit", "transfer", "restore-known-volatile", "--json"])' in source
    assert 'step("restore-before-sync", ["git", "restore", "--", *KNOWN_VOLATILE_TRANSFER_PATHS])' not in source
