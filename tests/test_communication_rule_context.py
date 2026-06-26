from __future__ import annotations

import json
import subprocess

from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.communication_rule_context import (
    PENDING_STATE_PATH,
    REQUIRED_LOADED_SECTIONS,
    acknowledge_communication_refresh,
    require_current_communication_context,
)
from tests.test_rule_refresh import write_sources


def test_communication_refresh_without_publish_reports_local_only(tmp_path) -> None:
    write_sources(tmp_path)

    result = CliRunner().invoke(
        app,
        ["rules", "communication-refresh", "--root", str(tmp_path), "--json"],
    )

    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["local_only"] is True
    assert data["remote_readable"] is False
    assert data["next_reply"] == "d2"
    assert not (tmp_path / PENDING_STATE_PATH).exists()


def test_communication_refresh_publish_writes_d2_pending_state(tmp_path) -> None:
    write_sources(tmp_path)

    result = CliRunner().invoke(
        app,
        ["rules", "communication-refresh", "--root", str(tmp_path), "--publish", "--json"],
    )

    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    pending = json.loads((tmp_path / PENDING_STATE_PATH).read_text(encoding="utf-8"))
    assert data["kind"] == "communication_rule_refresh"
    assert data["must_read_before_continue"] is True
    assert data["blob_sha"] == pending["expected_blob_sha"]
    assert pending["required_next_reply"] == "d2"
    assert pending["blocks_normal_go"] is True
    assert pending["remote_path"] == "docs/reports/communication_rules/CURRENT_COMMUNICATION_RULES.md"


def test_require_current_communication_context_blocks_pending_without_ack(tmp_path) -> None:
    write_sources(tmp_path)
    CliRunner().invoke(
        app,
        ["rules", "communication-refresh", "--root", str(tmp_path), "--publish", "--json"],
    )

    result = require_current_communication_context(tmp_path)

    assert result.result_status == "BLOCK"
    assert result.required_next_reply == "d2"
    assert result.communication_context_fresh is False


def test_require_current_communication_context_rechecks_published_pending_state(tmp_path) -> None:
    write_sources(tmp_path)
    CliRunner().invoke(
        app,
        ["rules", "communication-refresh", "--root", str(tmp_path), "--publish", "--json"],
    )

    subprocess.run(["git", "init"], cwd=tmp_path, check=True, stdout=subprocess.PIPE)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "add", "docs/reports/communication_rules/CURRENT_COMMUNICATION_RULES.md"],
        cwd=tmp_path,
        check=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "publish communication rules"],
        cwd=tmp_path,
        check=True,
        stdout=subprocess.PIPE,
    )
    subprocess.run(
        ["git", "update-ref", "refs/remotes/origin/main", "HEAD"],
        cwd=tmp_path,
        check=True,
    )

    result = require_current_communication_context(tmp_path)

    assert result.result_status == "BLOCK"
    assert result.reason == "communication_rule_refresh_pending"
    assert result.required_next_reply == "d2"
    assert "ACK" in result.next_action


def test_acknowledge_communication_refresh_accepts_valid_ack(tmp_path) -> None:
    write_sources(tmp_path)
    CliRunner().invoke(
        app,
        ["rules", "communication-refresh", "--root", str(tmp_path), "--publish", "--json"],
    )
    pending = json.loads((tmp_path / PENDING_STATE_PATH).read_text(encoding="utf-8"))
    ack = {
        "kind": "communication_rule_refresh_ack",
        "result_status": "PASS",
        "source": pending["remote_path"],
        "remote": "main",
        "blob_sha": pending["expected_blob_sha"],
        "generated_at": pending["generated_at"],
        "loaded_sections": list(REQUIRED_LOADED_SECTIONS),
        "rules_loaded": True,
    }
    ack_path = tmp_path / "ack.json"
    ack_path.write_text(json.dumps(ack), encoding="utf-8")

    result = acknowledge_communication_refresh(tmp_path, ack_path)

    assert result.result_status == "PASS"
    assert not (tmp_path / PENDING_STATE_PATH).exists()
    assert require_current_communication_context(tmp_path).result_status == "PASS"


def test_acknowledge_communication_refresh_blocks_wrong_blob_sha(tmp_path) -> None:
    write_sources(tmp_path)
    CliRunner().invoke(
        app,
        ["rules", "communication-refresh", "--root", str(tmp_path), "--publish", "--json"],
    )
    pending = json.loads((tmp_path / PENDING_STATE_PATH).read_text(encoding="utf-8"))
    ack_path = tmp_path / "ack.json"
    ack_path.write_text(
        json.dumps(
            {
                "kind": "communication_rule_refresh_ack",
                "result_status": "PASS",
                "source": pending["remote_path"],
                "blob_sha": "wrong",
                "generated_at": pending["generated_at"],
                "loaded_sections": list(REQUIRED_LOADED_SECTIONS),
                "rules_loaded": True,
            }
        ),
        encoding="utf-8",
    )

    result = acknowledge_communication_refresh(tmp_path, ack_path)

    assert result.result_status == "BLOCK"
    assert "blob_sha_mismatch" in result.reason


def test_acknowledge_communication_refresh_blocks_wrong_source(tmp_path) -> None:
    write_sources(tmp_path)
    CliRunner().invoke(
        app,
        ["rules", "communication-refresh", "--root", str(tmp_path), "--publish", "--json"],
    )
    pending = json.loads((tmp_path / PENDING_STATE_PATH).read_text(encoding="utf-8"))
    ack_path = tmp_path / "ack.json"
    ack_path.write_text(
        json.dumps(
            {
                "kind": "communication_rule_refresh_ack",
                "result_status": "PASS",
                "source": "wrong.md",
                "blob_sha": pending["expected_blob_sha"],
                "generated_at": pending["generated_at"],
                "loaded_sections": list(REQUIRED_LOADED_SECTIONS),
                "rules_loaded": True,
            }
        ),
        encoding="utf-8",
    )

    result = acknowledge_communication_refresh(tmp_path, ack_path)

    assert result.result_status == "BLOCK"
    assert "source_mismatch" in result.reason


def test_rules_require_current_communication_context_cli_blocks_pending(tmp_path) -> None:
    write_sources(tmp_path)
    CliRunner().invoke(
        app,
        ["rules", "communication-refresh", "--root", str(tmp_path), "--publish", "--json"],
    )

    result = CliRunner().invoke(
        app,
        ["rules", "require-current-communication-context", "--root", str(tmp_path), "--json"],
    )

    assert result.exit_code == 2
    data = json.loads(result.output)
    assert data["result_status"] == "BLOCK"
    assert data["required_next_reply"] == "d2"


def test_pr_create_complete_blocks_when_d2_pending(tmp_path, monkeypatch) -> None:
    write_sources(tmp_path)
    CliRunner().invoke(
        app,
        ["rules", "communication-refresh", "--root", str(tmp_path), "--publish", "--json"],
    )
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(
        app,
        [
            "transfer",
            "pr-create-complete",
            "--title",
            "Blocked",
            "--skip-llm-context-gate",
            "--json",
        ],
    )

    assert result.exit_code == 2
    data = json.loads(result.output)
    assert data["kind"] == "communication_context_gate"
    assert data["required_next_reply"] == "d2"
