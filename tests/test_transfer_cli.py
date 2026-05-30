from __future__ import annotations

import hashlib
from pathlib import Path

import yaml
from typer.testing import CliRunner

from agentic_project_kit.cli import app


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


def test_transfer_inspect_cli_reports_pending_without_writing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_order(tmp_path)

    result = CliRunner().invoke(app, ["transfer", "inspect"])

    assert result.exit_code == 0
    assert "transfer_id=cli-transfer" in result.stdout
    assert "result_status=PENDING" in result.stdout
    assert not (tmp_path / "generated/cli.txt").exists()


def test_transfer_apply_cli_writes_payload_and_report(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_order(tmp_path)

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
