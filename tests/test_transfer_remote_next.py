from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import yaml

from agentic_project_kit.transfer_remote_next import (
    _validate_branch_name,
    resolve_remote_next_branch,
    run_remote_next_transfer,
)


def _init_repo(root: Path) -> None:
    subprocess.run(["git", "init"], cwd=root, check=True, stdout=subprocess.PIPE)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=root, check=True)
    subprocess.run(["git", "commit", "--allow-empty", "-m", "init"], cwd=root, check=True, stdout=subprocess.PIPE)


def test_validate_branch_name_accepts_transfer_branch():
    assert _validate_branch_name("transfer/example-1") == "transfer/example-1"


def test_validate_branch_name_rejects_unsafe_branch():
    for value in ["", "-bad", "bad..name", "bad name", "bad.lock"]:
        try:
            _validate_branch_name(value)
        except ValueError:
            continue
        raise AssertionError(f"unsafe branch accepted: {value!r}")


def test_resolve_remote_next_branch_accepts_explicit_branch(tmp_path):
    assert resolve_remote_next_branch(tmp_path, "transfer/example") == "transfer/example"


def test_resolve_remote_next_branch_reads_transfer_order_branch(tmp_path):
    inbox = tmp_path / ".agentic/transfer/inbox/current.yaml"
    inbox.parent.mkdir(parents=True)
    inbox.write_text(yaml.safe_dump({"branch": "feature/example"}), encoding="utf-8")

    assert resolve_remote_next_branch(tmp_path) == "feature/example"


def test_resolve_remote_next_branch_requires_order_branch(tmp_path):
    inbox = tmp_path / ".agentic/transfer/inbox/current.yaml"
    inbox.parent.mkdir(parents=True)
    inbox.write_text(yaml.safe_dump({"id": "missing-branch"}), encoding="utf-8")

    try:
        resolve_remote_next_branch(tmp_path)
    except ValueError as exc:
        assert "must define a non-empty branch" in str(exc)
    else:
        raise AssertionError("missing branch accepted")


def test_remote_next_blocks_dirty_worktree_before_fetch(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    (tmp_path / "dirty.txt").write_text("dirty\n", encoding="utf-8")

    result = run_remote_next_transfer(tmp_path, "transfer/example")

    assert result.returncode == 2
    assert result.result_status == "BLOCKED"
    assert "dirty_worktree" in result.reasons
    assert result.published_report_path
    assert (tmp_path / result.published_report_path).exists()


def test_remote_next_report_includes_protocol_header(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    (tmp_path / "dirty.txt").write_text("dirty\n", encoding="utf-8")

    result = run_remote_next_transfer(tmp_path, "transfer/example")
    report = json.loads((tmp_path / result.published_report_path).read_text(encoding="utf-8"))

    assert report["kind"] == "local_to_llm_remote_next_report"
    assert report["protocol_header"]["kind"] == "transfer_protocol_header"
    assert report["protocol_header"]["one_command_transfer_protocol"]["id"] == (
        "one-command-transfer-protocol"
    )
    remote_report = report["remote_next_report"]
    assert remote_report["result_status"] == "BLOCKED"
    assert remote_report["command_id"] == remote_report["transfer_id"]
    assert remote_report["state"] == remote_report["primary_state"]
    assert remote_report["next"] == remote_report["next_action"]
    assert report["last_result"] == remote_report
    post_actions = report["remote_next_report"]["post_report_actions"]
    assert post_actions["attempted"] is True
    assert post_actions.get("status") != "pending_until_report_files_are_written"
    assert "steps" in post_actions


def test_remote_next_without_branch_requires_order_branch(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    inbox = tmp_path / ".agentic/transfer/inbox/current.yaml"
    inbox.parent.mkdir(parents=True)
    inbox.write_text(yaml.safe_dump({"id": "missing-branch"}), encoding="utf-8")

    result = run_remote_next_transfer(tmp_path)

    assert result.returncode == 2
    assert result.result_status == "BLOCKED"
    assert "invalid_transfer_order" in result.reasons
    assert "must define a non-empty branch" in result.blocked_message
    assert result.published_report_path
    assert (tmp_path / result.published_report_path).exists()


def test_transfer_help_lists_remote_next():
    completed = subprocess.run(
        [sys.executable, "-m", "agentic_project_kit.cli", "transfer", "--help"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert completed.returncode == 0
    assert "remote-next" in completed.stdout


def test_remote_next_log_includes_state_next_and_command_id(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    (tmp_path / "dirty.txt").write_text("dirty\n", encoding="utf-8")

    result = run_remote_next_transfer(tmp_path, "transfer/example")
    log_text = (tmp_path / result.published_report_path.replace(".json", ".log")).read_text(encoding="utf-8")

    assert "COMMAND_ID=remote-next-blocked" in log_text
    assert "STATE=BLOCKED" in log_text
    assert "NEXT=Inspect the published remote-next diagnostic report before retrying." in log_text
