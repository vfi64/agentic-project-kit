from __future__ import annotations

import json
import subprocess
from pathlib import Path

from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.transfer_state import build_transfer_state
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


def _write_and_commit_minimal_sources(root: Path) -> None:
    write_minimal_sources(root)
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    subprocess.run(
        ["git", "commit", "-m", "Add minimal rule sources"],
        cwd=root,
        check=True,
        stdout=subprocess.PIPE,
    )


def test_rules_snapshot_cli_text_passes_for_repository() -> None:
    result = CliRunner().invoke(app, ["rules", "snapshot"])

    assert result.exit_code == 0, result.output
    assert "RULE_SNAPSHOT" in result.output
    assert "schema_version=1" in result.output
    assert "is_valid=True" in result.output
    assert "fail_closed=False" in result.output
    assert "snapshot_id=" in result.output
    assert "source_digests_total=" in result.output


def test_rules_snapshot_cli_json_passes_for_repository() -> None:
    result = CliRunner().invoke(app, ["rules", "snapshot", "--json"])

    assert result.exit_code == 0, result.output
    data = json.loads(result.output)

    assert data["schema_version"] == 1
    assert isinstance(data["snapshot_id"], str)
    assert len(data["snapshot_id"]) == 64
    assert data["is_valid"] is True
    assert data["fail_closed"] is False
    assert isinstance(data["source_digests"], list)
    assert data["sources_total"] == data["validation"]["sources_total"]


def test_rules_snapshot_cli_fails_closed_for_missing_source(tmp_path: Path) -> None:
    write_minimal_sources(tmp_path)
    (tmp_path / ".agentic/compiled_agent_context.yaml").unlink()

    result = CliRunner().invoke(app, ["rules", "snapshot", "--root", str(tmp_path)])

    assert result.exit_code == 1
    assert "RULE_SNAPSHOT" in result.output
    assert "is_valid=False" in result.output
    assert "fail_closed=True" in result.output
    assert (
        "blocking_reason=missing required rule source: .agentic/compiled_agent_context.yaml"
        in result.output
    )


def test_rules_snapshot_cli_json_fails_closed_for_missing_source(tmp_path: Path) -> None:
    write_minimal_sources(tmp_path)
    (tmp_path / ".agentic/compiled_agent_context.yaml").unlink()

    result = CliRunner().invoke(app, ["rules", "snapshot", "--root", str(tmp_path), "--json"])

    assert result.exit_code == 1
    data = json.loads(result.output)

    assert data["is_valid"] is False
    assert data["fail_closed"] is True
    assert ".agentic/compiled_agent_context.yaml" in data["validation"]["missing_required_paths"]


def test_rules_acknowledge_cli_writes_current_acknowledgement(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    _write_and_commit_minimal_sources(tmp_path)

    result = CliRunner().invoke(app, ["rules", "acknowledge", "--root", str(tmp_path)])

    assert result.exit_code == 0, result.output
    assert "RULE_ACKNOWLEDGEMENT" in result.output
    assert "written=True" in result.output

    path = tmp_path / ".agentic/rule_ack/current.json"
    assert path.exists()
    data = json.loads(path.read_text(encoding="utf-8"))

    assert data["schema_version"] == 1
    assert isinstance(data["snapshot_id"], str)
    assert len(data["snapshot_id"]) == 64
    assert data["repo_head"]
    assert data["sources_total"] > 0
    assert data["missing_sources_total"] == 0
    assert data["declared_next_allowed_action"] == "run_next_command"


def test_rules_acknowledge_cli_makes_transfer_state_rules_confirmed(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    _write_and_commit_minimal_sources(tmp_path)

    result = CliRunner().invoke(app, ["rules", "acknowledge", "--root", str(tmp_path)])

    assert result.exit_code == 0, result.output

    state = build_transfer_state(tmp_path)

    assert state.capabilities["rules_confirmed"] is True
    assert state.rule_acknowledgement["present"] is True
    assert state.rule_acknowledgement["decision"]["is_confirmed"] is True


def test_rules_acknowledge_cli_fails_closed_for_missing_source(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    _write_and_commit_minimal_sources(tmp_path)
    (tmp_path / ".agentic/compiled_agent_context.yaml").unlink()

    result = CliRunner().invoke(app, ["rules", "acknowledge", "--root", str(tmp_path)])

    assert result.exit_code == 1
    assert "RULE_ACKNOWLEDGEMENT" in result.output
    assert "written=False" in result.output
    assert not (tmp_path / ".agentic/rule_ack/current.json").exists()
