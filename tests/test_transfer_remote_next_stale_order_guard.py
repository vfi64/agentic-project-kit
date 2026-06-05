from __future__ import annotations

import subprocess
from pathlib import Path

import yaml

from agentic_project_kit.transfer_remote_next import run_remote_next_transfer


def _init_repo(root: Path) -> None:
    subprocess.run(["git", "init"], cwd=root, check=True, stdout=subprocess.PIPE)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=root, check=True)
    subprocess.run(["git", "commit", "--allow-empty", "-m", "init"], cwd=root, check=True, stdout=subprocess.PIPE)


def _head(root: Path) -> str:
    return subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=root,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    ).stdout.strip()


def _write_order(root: Path, data: dict[str, object]) -> None:
    inbox = root / ".agentic/transfer/inbox/current.yaml"
    inbox.parent.mkdir(parents=True)
    inbox.write_text(yaml.safe_dump(data), encoding="utf-8")


def test_remote_next_blocks_inactive_transfer_order_without_branch_before_branch_validation(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    _write_order(
        tmp_path,
        {
            "schema_version": 1,
            "id": "no-current-transfer-order",
            "status": "inactive",
        },
    )

    result = run_remote_next_transfer(tmp_path)

    assert result.returncode == 2
    assert result.result_status == "BLOCKED"
    assert result.as_json_data()["primary_state"] == "NEW_ORDER_REQUIRED"
    assert result.next_action == "Create or queue a fresh remote-next transfer order, then rerun the canonical command."
    assert "no_current_transfer_order" in result.reasons
    assert "invalid_transfer_order" not in result.reasons
    assert result.local_run.apply is None
    assert result.local_run.state["primary_state"] == "NEW_ORDER_REQUIRED"
    assert result.preflight["transfer_order_guard"]["status"] == "inactive"


def test_remote_next_blocks_inactive_transfer_order_before_apply(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    _write_order(
        tmp_path,
        {
            "schema_version": 1,
            "id": "no-current-transfer-order",
            "status": "inactive",
            "branch": "main",
            "expected_current_head": _head(tmp_path),
        },
    )

    result = run_remote_next_transfer(tmp_path)

    assert result.returncode == 2
    assert result.result_status == "BLOCKED"
    assert "no_current_transfer_order" in result.reasons
    assert result.local_run.apply is None
    assert result.preflight["transfer_order_guard"]["status"] == "inactive"


def test_remote_next_blocks_order_missing_freshness_anchor_before_apply(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    _write_order(
        tmp_path,
        {
            "schema_version": 1,
            "id": "old-order-without-anchor",
            "status": "active",
            "branch": "main",
        },
    )

    result = run_remote_next_transfer(tmp_path)

    assert result.returncode == 2
    assert result.result_status == "BLOCKED"
    assert "stale_order_missing_freshness_anchor" in result.reasons
    assert result.local_run.apply is None


def test_remote_next_blocks_head_mismatch_before_apply(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    _write_order(
        tmp_path,
        {
            "schema_version": 1,
            "id": "stale-order",
            "status": "active",
            "branch": "main",
            "expected_current_head": "deadbee",
        },
    )

    result = run_remote_next_transfer(tmp_path)

    assert result.returncode == 2
    assert result.result_status == "BLOCKED"
    assert "stale_transfer_order_head_mismatch" in result.reasons
    assert result.local_run.apply is None
