"""G3 for the transfer orchestrators: every BLOCKED/FAIL result they print carries a route.

The structural guarantee (callbacks print only through routing emitters) lives in
test_g3_blocked_route_ratchet.py; these tests pin the behaviour of the shared emitter and of the
paths that printed BLOCKED results without a route before.
"""
from __future__ import annotations

import json
from types import SimpleNamespace

import pytest
import typer
from typer.testing import CliRunner

from agentic_project_kit.blocked_route import KIND_HUMAN, KIND_KIT, route_problems
from agentic_project_kit.cli import app
from agentic_project_kit.cli_commands import transfer_repo_after_pr, transfer_shared
from agentic_project_kit.cli_commands.transfer_shared import (
    _echo_command_error,
    _echo_repo_result,
    _emit_transfer,
    _require_transfer_capability,
)
from agentic_project_kit.transfer_repo_actions import RepoActionResult, result_json


def _blocked_repo_result(**extra) -> RepoActionResult:
    return RepoActionResult(action="admin-refresh-pr", result_status="BLOCKED", returncode=2, command=["x"],
                            stdout="", stderr="", next_action="Inspect the refresh PR.", **extra)


def test_json_mode_routes_an_unrouted_blocked_payload(capsys):
    _emit_transfer({"result_status": "BLOCKED", "blocker": "wheel download failed\nmore"}, json_output=True,
                   indent=2, sort_keys=True)
    printed = json.loads(capsys.readouterr().out)
    assert route_problems(printed) == []
    assert printed["next_command_kind"] == KIND_HUMAN
    assert printed["next_command_reason"] == "wheel download failed"


def test_json_mode_keeps_a_named_command_as_kit_route(capsys):
    _emit_transfer({"result_status": "FAIL", "next_command": "agentic-kit pr wait-ci 7",
                    "next_command_autonomous": True}, json_output=True)
    printed = json.loads(capsys.readouterr().out)
    assert printed["next_command_kind"] == KIND_KIT and printed["next_command_autonomous"] is True


def test_text_mode_prints_the_projection_then_the_route(capsys):
    _emit_transfer({"result_status": "BLOCKED", "next_action": "Fix the head."}, json_output=False,
                   text=lambda routed: f"STATE {routed['result_status']}")
    lines = capsys.readouterr().out.splitlines()
    assert lines[0] == "STATE BLOCKED"
    assert lines[1].startswith("NEXT_COMMAND_KIND:") and lines[1].endswith(KIND_HUMAN)
    assert lines[2].startswith("NEXT_COMMAND_REASON:") and lines[2].endswith("Fix the head.")


def test_text_mode_adds_no_route_to_a_pass(capsys):
    payload = _emit_transfer({"result_status": "PASS"}, json_output=False, text=lambda routed: "done")
    assert capsys.readouterr().out == "done\n"
    assert payload == {"result_status": "PASS"}


def test_text_can_go_to_stderr(capsys):
    _emit_transfer({"result_status": "BLOCKED", "blocker": "category missing"}, json_output=False,
                   text=lambda routed: "BLOCKED: category missing", err=True)
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.splitlines()[0] == "BLOCKED: category missing"


def test_repo_results_print_as_before(capsys):
    result = _blocked_repo_result()
    _echo_repo_result(result, True)
    assert capsys.readouterr().out == result_json(result) + "\n"
    _echo_repo_result(result, False)
    assert capsys.readouterr().out.count("NEXT_COMMAND_KIND") == 1


def test_command_errors_carry_the_human_marker(capsys):
    _echo_command_error("remote-next", RuntimeError("order missing"), returncode=1)
    printed = json.loads(capsys.readouterr().out)
    assert route_problems(printed) == [] and printed["next_command_kind"] == KIND_HUMAN


def _snapshot(*, fail_closed: bool):
    return SimpleNamespace(capabilities={}, next_action="agentic-kit transfer state", primary_state="BLOCKED",
                           reasons=["rules_not_confirmed"], rule_snapshot={"fail_closed": fail_closed},
                           rule_acknowledgement={})


def test_missing_rule_confirmation_names_the_acknowledge_command(monkeypatch, capsys):
    monkeypatch.setattr(transfer_shared, "build_transfer_state", lambda root: _snapshot(fail_closed=False))
    with pytest.raises(typer.Exit):
        _require_transfer_capability("rules_confirmed", json_output=True)
    printed = json.loads(capsys.readouterr().out)
    assert route_problems(printed) == []
    assert printed["next_command"] == "agentic-kit rules acknowledge"
    assert printed["next_command_kind"] == KIND_KIT and printed["next_command_autonomous"] is False


def test_fail_closed_rules_leave_the_decision_to_a_person(monkeypatch, capsys):
    monkeypatch.setattr(transfer_shared, "build_transfer_state", lambda root: _snapshot(fail_closed=True))
    with pytest.raises(typer.Exit):
        _require_transfer_capability("rules_confirmed", json_output=False)
    out = capsys.readouterr().out
    printed = json.loads(out[: out.index("\nFINAL_SIGNAL=f")])
    assert printed["next_command_kind"] == KIND_HUMAN and printed["next_command_reason"] == "agentic-kit transfer state"
    assert out.rstrip().endswith("CHAT_REPLY=f | NEXT=agentic-kit transfer state")


def test_admin_refresh_pr_cli_prints_a_routed_result(monkeypatch):
    monkeypatch.setattr(transfer_repo_after_pr, "_require_transfer_capability", lambda *args, **kwargs: None)
    monkeypatch.setattr(transfer_repo_after_pr, "_public_transfer_attr", lambda name, fallback: fallback)
    monkeypatch.setattr(transfer_repo_after_pr, "admin_refresh_pr", lambda *args, **kwargs: _blocked_repo_result())
    result = CliRunner().invoke(app, ["transfer", "admin-refresh-pr", "--after-pr", "5", "--json"])
    assert result.exit_code == 2
    printed = json.loads(result.stdout)
    assert route_problems(printed) == [] and printed["next_command_reason"] == "Inspect the refresh PR."
