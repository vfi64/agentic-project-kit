from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
import shutil

import yaml
from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.instruction_lint import command_manifest_ack_line
from tests.test_rule_source_validator import write_minimal_sources


REFERENCE_ROOT = Path(__file__).resolve().parents[1] / "docs/reference"


def _copy_command_reference(root: Path) -> None:
    target = root / "docs/reference"
    target.mkdir(parents=True, exist_ok=True)
    shutil.copy2(REFERENCE_ROOT / "agentic-kit-commands.json", target / "agentic-kit-commands.json")
    shutil.copy2(REFERENCE_ROOT / "AGENTIC_KIT_COMMANDS.md", target / "AGENTIC_KIT_COMMANDS.md")


def _ack(root: Path) -> str:
    manifest = json.loads((root / "docs/reference/agentic-kit-commands.json").read_text(encoding="utf-8"))
    return command_manifest_ack_line(manifest)


def _write_order(root: Path, *, extra_fields: dict[str, object] | None = None) -> None:
    _copy_command_reference(root)
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
    if extra_fields:
        order.update(extra_fields)
    path = root / ".agentic/transfer/inbox/current.yaml"
    path.parent.mkdir(parents=True)
    path.write_text(_ack(root) + "\n" + yaml.safe_dump(order, sort_keys=False), encoding="utf-8")


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


def _prepare_acknowledged_transfer_repo(
    root: Path, *, extra_order_fields: dict[str, object] | None = None
) -> None:
    _init_repo(root)
    write_minimal_sources(root)
    _write_order(root, extra_fields=extra_order_fields)
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


def test_transfer_apply_logs_instruction_lint_warnings_without_blocking(tmp_path, monkeypatch):
    _prepare_acknowledged_transfer_repo(
        tmp_path,
        extra_order_fields={"shell": "git status --short"},
    )
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(app, ["transfer", "apply"])

    assert result.exit_code == 0, result.stdout
    warning_log = tmp_path / "tmp/instruction-lint-warnings.log"
    assert warning_log.exists()
    warning_text = warning_log.read_text(encoding="utf-8")
    assert "STATUS=WARN" in warning_text
    assert "UNKNOWN_RAW" in warning_text
    assert (tmp_path / "generated/cli.txt").read_text(encoding="utf-8") == "cli payload\n"


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
