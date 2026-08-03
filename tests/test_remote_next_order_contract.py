from __future__ import annotations

import json
import subprocess
from pathlib import Path

from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.command_manifest import load_manifest
from agentic_project_kit.remote_next_order_contract import (
    create_remote_next_order,
    validate_remote_next_order,
)


def _run(root: Path, *argv: str) -> str:
    completed = subprocess.run(
        list(argv),
        cwd=root,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return completed.stdout.strip()


def _init_repo(root: Path) -> None:
    _run(root, "git", "init", "--initial-branch", "main")
    _run(root, "git", "config", "user.email", "test@example.invalid")
    _run(root, "git", "config", "user.name", "Test User")
    (root / "README.md").write_text("test\n", encoding="utf-8")
    _run(root, "git", "add", "README.md")
    _run(root, "git", "commit", "-m", "init")


def _add_origin(root: Path, remote: Path) -> None:
    _run(remote.parent, "git", "init", "--bare", "--initial-branch", "main", remote.name)
    _run(root, "git", "remote", "add", "origin", str(remote))
    _run(root, "git", "push", "-u", "origin", "main")


def _seed_manifest(root: Path) -> None:
    manifest_path = root / "docs/reference/agentic-kit-commands.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(load_manifest(Path(".")), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _seed_payload(root: Path) -> str:
    payload = root / ".agentic/transfer/payloads/example.txt"
    payload.parent.mkdir(parents=True, exist_ok=True)
    payload.write_text("hello\n", encoding="utf-8")
    return ".agentic/transfer/payloads/example.txt"


def _ready_repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    _init_repo(root)
    _add_origin(root, tmp_path / "origin.git")
    _seed_manifest(root)
    _seed_payload(root)
    return root


def test_create_remote_next_order_dry_run_does_not_write(tmp_path: Path) -> None:
    root = _ready_repo(tmp_path)

    result = create_remote_next_order(
        root,
        branch="feature/transfer-order",
        write_actions=("generated/example.txt=.agentic/transfer/payloads/example.txt",),
    )

    assert result.result_status == "PASS"
    assert result.written is False
    assert not (root / ".agentic/transfer/inbox/current.yaml").exists()
    assert "COMMAND_MANIFEST_ACK " in result.preview_text
    assert "kind: llm_to_local_transfer_order" in result.preview_text
    assert result.order["expected_current_head"] == _run(root, "git", "rev-parse", "HEAD")
    assert result.safe_push_target
    assert result.safe_push_target["status"] == "PASS"


def test_create_remote_next_order_execute_writes_hash_and_validator_passes(tmp_path: Path) -> None:
    root = _ready_repo(tmp_path)

    create_result = create_remote_next_order(
        root,
        branch="feature/transfer-order",
        write_actions=("generated/example.txt=.agentic/transfer/payloads/example.txt",),
        execute=True,
    )
    validate_result = validate_remote_next_order(root)

    assert create_result.result_status == "PASS"
    assert create_result.written is True
    text = (root / ".agentic/transfer/inbox/current.yaml").read_text(encoding="utf-8")
    assert "sha256:" in text
    assert validate_result.result_status == "PASS"
    assert validate_result.transfer_inspect
    assert validate_result.transfer_inspect["result_status"] == "PENDING"


def test_validate_remote_next_order_blocks_protected_branch(tmp_path: Path) -> None:
    root = _ready_repo(tmp_path)
    create_remote_next_order(
        root,
        branch="feature/transfer-order",
        write_actions=("generated/example.txt=.agentic/transfer/payloads/example.txt",),
        execute=True,
    )
    order_path = root / ".agentic/transfer/inbox/current.yaml"
    order_path.write_text(
        order_path.read_text(encoding="utf-8").replace(
            "branch: feature/transfer-order",
            "branch: main",
            1,
        ),
        encoding="utf-8",
    )

    result = validate_remote_next_order(root)

    assert result.result_status == "BLOCKED"
    assert "protected_branch_refused:main" in result.blockers


def test_validate_remote_next_order_blocks_stale_head(tmp_path: Path) -> None:
    root = _ready_repo(tmp_path)
    create_remote_next_order(
        root,
        branch="feature/transfer-order",
        write_actions=("generated/example.txt=.agentic/transfer/payloads/example.txt",),
        execute=True,
    )
    (root / "changed.txt").write_text("new head\n", encoding="utf-8")
    _run(root, "git", "add", "changed.txt")
    _run(root, "git", "commit", "-m", "move head")

    result = validate_remote_next_order(root)

    assert result.result_status == "BLOCKED"
    assert "expected_current_head_mismatch" in result.blockers


def test_transfer_order_validate_cli_json(tmp_path: Path, monkeypatch) -> None:
    root = _ready_repo(tmp_path)
    create_remote_next_order(
        root,
        branch="feature/transfer-order",
        write_actions=("generated/example.txt=.agentic/transfer/payloads/example.txt",),
        execute=True,
    )
    monkeypatch.chdir(root)

    result = CliRunner().invoke(app, ["transfer", "order-validate", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["result_status"] == "PASS"
    assert payload["valid"] is True
