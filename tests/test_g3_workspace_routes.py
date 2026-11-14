"""G3 for the workspace orchestrators, the docs lifecycle sweep and the DPA final closeout check:
every result that ends the command with a non-zero exit names its way on, as a Kit command to a
planning run or as the human marker with a reason (owner decision 2026-11-13)."""
from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from agentic_project_kit.blocked_route import KIND_HUMAN, KIND_KIT, route_problems, with_blocked_route
from agentic_project_kit.cli import app
from agentic_project_kit.cli_commands.routed_output import emit_routed, kit_command

runner = CliRunner()


def _json(args: list[str], code: int) -> dict:
    result = runner.invoke(app, [*args, "--json"])
    assert result.exit_code == code, result.output
    return json.loads(result.output)


def _routed(payload: dict) -> None:
    assert route_problems({**payload, "result_status": "BLOCKED"}) == []


def test_a_blocked_alias_gets_the_route_and_keeps_its_status():
    payload = with_blocked_route({"result_status": "BLOCKED_FOR_X", "next_command_reason": "owner decides"})
    assert payload["result_status"] == "BLOCKED_FOR_X" and payload["next_command_kind"] == KIND_HUMAN
    _routed(payload)
    kit = with_blocked_route({"result_status": "BLOCK", "next_command": "agentic-kit workspace init"})
    assert kit["next_command_kind"] == KIND_KIT and kit["next_command_autonomous"] is False


def test_emit_routed_routes_block_and_leaves_pass_alone(capsys):
    assert "next_command_kind" not in emit_routed({"result_status": "PASS"}, json_output=True)
    routed = emit_routed({"result_status": "BLOCK", "reason": "x"}, json_output=False, text=lambda p: "STATUS=BLOCK\n")
    out = capsys.readouterr().out
    assert routed["next_command_kind"] == KIND_HUMAN and "STATUS=BLOCK\nNEXT_COMMAND_KIND=human\n" in out
    assert "NEXT_COMMAND_REASON=" in out


def test_kit_command_names_a_root_only_when_given():
    assert kit_command("workspace", "upgrade") == "agentic-kit workspace upgrade"
    assert kit_command("workspace", "upgrade", root=Path(".")) == "agentic-kit workspace upgrade"
    assert kit_command("workspace", "init", root=Path("my repo")) == "agentic-kit workspace init --root 'my repo'"


def test_init_on_an_initialized_workspace_routes_to_the_upgrade_plan(tmp_path: Path):
    assert runner.invoke(app, ["workspace", "init", "--root", str(tmp_path), "--execute"]).exit_code == 0
    payload = _json(["workspace", "init", "--root", str(tmp_path)], 1)
    assert payload["code"] == "ALREADY_INITIALIZED" and payload["next_command_kind"] == KIND_KIT
    assert payload["next_command"] == kit_command("workspace", "upgrade", root=tmp_path)
    assert payload["next_command_autonomous"] is True and route_problems(payload) == []
    text = runner.invoke(app, ["workspace", "init", "--root", str(tmp_path)])
    assert text.exit_code == 1 and f"NEXT_COMMAND={payload['next_command']}" in text.output


def test_upgrade_without_manifest_routes_to_the_init_plan(tmp_path: Path):
    payload = _json(["workspace", "upgrade", "--root", str(tmp_path)], 1)
    assert payload["code"] == "NO_MANIFEST" and payload["next_command"].startswith("agentic-kit workspace init")
    assert route_problems(payload) == []


def test_upgrade_error_without_kit_route_carries_the_human_marker(tmp_path: Path):
    (tmp_path / ".agentic").mkdir()
    (tmp_path / ".agentic" / "config.yaml").write_text("kit_schema_version: 99\n", encoding="utf-8")
    payload = _json(["workspace", "upgrade", "--root", str(tmp_path)], 1)
    assert payload["next_command_kind"] == KIND_HUMAN and payload["code"] in payload["next_command_reason"]
    assert route_problems(payload) == []


def test_remove_of_a_foreign_agentic_directory_names_the_reason(tmp_path: Path):
    (tmp_path / ".agentic").mkdir()
    payload = _json(["workspace", "remove", "--root", str(tmp_path)], 2)
    assert payload["result_status"] == "BLOCKED" and payload["next_command_kind"] == KIND_HUMAN
    assert "foreign" in payload["next_command_reason"] and route_problems(payload) == []


def test_adopt_passes_without_route(tmp_path: Path):
    payload = _json(["workspace", "adopt", "--root", str(tmp_path)], 0)
    assert payload["result_status"] == "PASS" and "next_command_kind" not in payload


def test_dpa_intake_evidence_block_names_the_evidence_root(tmp_path: Path):
    (tmp_path / "README.md").write_text("# Demo\n", encoding="utf-8")
    payload = _json(["workspace", "dpa-intake", "--root", str(tmp_path), "--validation-ref", "test-ref",
                     "--output", "docs/reports/intake.json"], 2)
    assert payload["result_status"] == "BLOCKED_FOR_DPA_INTAKE"
    assert "docs/architecture/evidence/dpa/assessment/" in payload["next_command_reason"]
    _routed(payload)


def test_docs_sweep_block_names_what_to_add(tmp_path: Path):
    payload = _json(["docs", "lifecycle", "sweep", "--root", str(tmp_path), "--execute"], 2)
    assert payload["result_status"] == "BLOCK" and payload["reason"] == "missing_only"
    assert "--only" in payload["next_command_reason"] and payload["next_command_kind"] == KIND_HUMAN
    _routed(payload)


def test_final_closeout_check_evidence_block_carries_the_route(tmp_path: Path):
    result = runner.invoke(app, ["dpa", "final-closeout-check", "--root", str(tmp_path),
                                 "--validation-ref", "r", "--output", "docs/x.json"])
    assert result.exit_code == 2, result.output
    assert "EVIDENCE_WRITE=BLOCK" in result.output and "NEXT_COMMAND_KIND=human" in result.output
    payload = _json(["dpa", "final-closeout-check", "--root", str(tmp_path), "--validation-ref", "r",
                     "--output", "docs/x.json"], 2)
    assert payload["next_command_kind"] == KIND_HUMAN and "assessment" in payload["next_command_reason"]
    _routed(payload)
