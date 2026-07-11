from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
import yaml

from agentic_project_kit.command_manifest import load_manifest
from agentic_project_kit.instruction_lint import command_manifest_ack_line
from agentic_project_kit.transfer_runner import (
    RESULT_FAIL,
    RESULT_PASS,
    RESULT_PENDING,
    apply_transfer_order,
    inspect_transfer_order,
    load_transfer_order,
    parse_transfer_order,
    transfer_result_as_json_data,
)


def _seed_manifest(root: Path) -> dict[str, object]:
    manifest = load_manifest(Path("."))
    target = root / "docs/reference/agentic-kit-commands.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def _ack(root: Path) -> str:
    return command_manifest_ack_line(_seed_manifest(root))


def _write_order(root: Path, payload_text: str = "hello\n") -> Path:
    payload = root / ".agentic/transfer/payloads/example.txt"
    payload.parent.mkdir(parents=True)
    payload.write_text(payload_text, encoding="utf-8")
    digest = hashlib.sha256(payload.read_bytes()).hexdigest()
    order = {
        "id": "example-transfer",
        "title": "Example transfer",
        "safety": "bounded-local-text-write",
        "report_path": "docs/reports/command_runs/example-transfer.md",
        "actions": [
            {
                "type": "write_text_file",
                "target_path": "generated/example.txt",
                "payload_path": ".agentic/transfer/payloads/example.txt",
                "sha256": digest,
            }
        ],
    }
    path = root / ".agentic/transfer/inbox/current.yaml"
    path.parent.mkdir(parents=True)
    path.write_text(
        _ack(root) + "\n" + yaml.safe_dump(order, sort_keys=False),
        encoding="utf-8",
    )
    return path


def _write_command_order(root: Path, command: list[str]) -> Path:
    order = {
        "id": "example-command-transfer",
        "title": "Example command transfer",
        "safety": "bounded-local-command",
        "report_path": "docs/reports/command_runs/example-command-transfer.md",
        "actions": [{"type": "run_command", "command": command}],
    }
    path = root / ".agentic/transfer/inbox/current.yaml"
    path.parent.mkdir(parents=True)
    path.write_text(
        _ack(root) + "\n" + yaml.safe_dump(order, sort_keys=False),
        encoding="utf-8",
    )
    return path


def test_parse_transfer_order_rejects_absolute_target_path():
    with pytest.raises(ValueError, match="repo-relative"):
        parse_transfer_order(
            {
                "id": "bad",
                "title": "Bad",
                "safety": "bounded",
                "report_path": "docs/reports/command_runs/bad.md",
                "actions": [
                    {
                        "type": "write_text_file",
                        "target_path": "/tmp/out.txt",
                        "payload_path": ".agentic/transfer/payloads/x.txt",
                    }
                ],
            }
        )


def test_parse_transfer_order_rejects_parent_segments():
    with pytest.raises(ValueError, match="parent"):
        parse_transfer_order(
            {
                "id": "bad",
                "title": "Bad",
                "safety": "bounded",
                "report_path": "docs/reports/command_runs/bad.md",
                "actions": [
                    {
                        "type": "write_text_file",
                        "target_path": "../out.txt",
                        "payload_path": ".agentic/transfer/payloads/x.txt",
                    }
                ],
            }
        )


def test_parse_transfer_order_rejects_shell_command_tokens():
    with pytest.raises(ValueError, match="shell control tokens"):
        parse_transfer_order(
            {
                "id": "bad",
                "title": "Bad",
                "safety": "bounded",
                "report_path": "docs/reports/command_runs/bad.md",
                "actions": [{"type": "run_command", "command": ["git", "status", "&&", "echo"]}],
            }
        )


def test_parse_transfer_order_rejects_direct_shell_invocation():
    with pytest.raises(ValueError, match="must not invoke a shell"):
        parse_transfer_order(
            {
                "id": "bad",
                "title": "Bad",
                "safety": "bounded",
                "report_path": "docs/reports/command_runs/bad.md",
                "actions": [{"type": "run_command", "command": ["bash", "-lc", "echo unsafe"]}],
            }
        )


def test_inspect_transfer_order_does_not_write_target(tmp_path):
    order_path = _write_order(tmp_path)
    order = load_transfer_order(order_path)

    result = inspect_transfer_order(order, tmp_path)

    assert result.result_status == RESULT_PENDING
    assert result.returncode == 0
    assert not (tmp_path / "generated/example.txt").exists()


def test_inspect_transfer_order_reports_command_without_running(tmp_path):
    marker = tmp_path / "marker.txt"
    order_path = _write_command_order(tmp_path, ["git", "status", "--short"])
    order = load_transfer_order(order_path)

    result = inspect_transfer_order(order, tmp_path)

    assert result.result_status == RESULT_PENDING
    assert result.returncode == 0
    assert result.action_results[0]["would_run"] is True
    assert not marker.exists()


def test_apply_transfer_order_writes_target_and_report(tmp_path):
    order_path = _write_order(tmp_path, "written\n")
    order = load_transfer_order(order_path)

    result = apply_transfer_order(order, tmp_path)

    assert result.result_status == RESULT_PASS
    assert result.returncode == 0
    assert (tmp_path / "generated/example.txt").read_text(encoding="utf-8") == "written\n"
    assert (tmp_path / "docs/reports/command_runs/example-transfer.md").exists()
    assert (tmp_path / "docs/reports/command_runs/LATEST_COMMAND_RUN.txt").read_text(
        encoding="utf-8"
    ) == "docs/reports/command_runs/example-transfer.md\n"


def test_apply_transfer_order_runs_bounded_command_and_writes_report(tmp_path):
    order_path = _write_command_order(tmp_path, ["git", "init"])
    order = load_transfer_order(order_path)

    result = apply_transfer_order(order, tmp_path)

    assert result.result_status == RESULT_PASS
    assert result.returncode == 0
    assert result.action_results[0]["type"] == "run_command"
    assert result.action_results[0]["returncode"] == 0
    assert (tmp_path / "docs/reports/command_runs/example-command-transfer.md").exists()


def test_apply_transfer_order_stops_on_failed_command_and_writes_report(tmp_path):
    order_path = _write_command_order(tmp_path, ["git", "not-a-command"])
    order = load_transfer_order(order_path)

    result = apply_transfer_order(order, tmp_path)

    assert result.result_status == RESULT_FAIL
    assert result.returncode != 0
    assert "failed" in result.message
    assert (tmp_path / "docs/reports/command_runs/example-command-transfer.md").exists()


def test_apply_transfer_order_rejects_hash_mismatch_and_writes_report(tmp_path):
    order_path = _write_order(tmp_path, "original\n")
    payload = tmp_path / ".agentic/transfer/payloads/example.txt"
    payload.write_text("changed\n", encoding="utf-8")
    order = load_transfer_order(order_path)

    result = apply_transfer_order(order, tmp_path)

    assert result.result_status == RESULT_FAIL
    assert result.returncode == 3
    assert "sha256 mismatch" in result.message
    assert not (tmp_path / "generated/example.txt").exists()
    assert (tmp_path / "docs/reports/command_runs/example-transfer.md").exists()


def test_transfer_result_json_exposes_command_id_state_and_next(tmp_path):
    order_path = _write_order(tmp_path)
    order = load_transfer_order(order_path)

    result = inspect_transfer_order(order, tmp_path)
    data = transfer_result_as_json_data(result)

    assert data["command_id"] == "example-transfer"
    assert data["transfer_id"] == "example-transfer"
    assert data["state"] == RESULT_PENDING
    assert data["next"] == data["next_action"]


def test_transfer_report_exposes_state_next_and_command_id(tmp_path):
    order_path = _write_order(tmp_path, "written\n")
    order = load_transfer_order(order_path)

    apply_transfer_order(order, tmp_path)
    report = (tmp_path / "docs/reports/command_runs/example-transfer.md").read_text(
        encoding="utf-8"
    )

    assert "COMMAND_ID=example-transfer" in report
    assert "STATE=PASS" in report
    assert "NEXT=review_transfer_state_and_evidence" in report
