"""G3 ratchet: every orchestrator in the command manifest either routes its BLOCKED results
through a conformant result builder (Kit command or human marker with reason) or stands on the
debt list. The debt list may only shrink: a new orchestrator must be conformant, and an
orchestrator that becomes conformant must leave the list (owner decision 2026-11-13)."""
from __future__ import annotations

import ast
import hashlib
import inspect
import json
import textwrap
from pathlib import Path

import pytest
import typer.main

from agentic_project_kit.blocked_route import KIND_HUMAN, KIND_KIT, route_problems, with_route
from agentic_project_kit.cli import app
from agentic_project_kit.cli_commands.human_workflows import _failed_local_step, _noop_step, _payload

MANIFEST = Path(__file__).resolve().parents[1] / "src/agentic_project_kit/reference/agentic-kit-commands.json"

# The 37 orchestrators of the manifest when the ratchet was introduced. Debt entries must come
# from this set, so a later orchestrator cannot be parked on the debt list.
BASELINE_SHA256 = "3df1094ba081d8b3ca3addaeb7a20da40210ba36857f463ccbca3d354d019666"
BASELINE = frozenset({
    "agentic-kit artifact-gc", "agentic-kit chat session-start", "agentic-kit docs lifecycle sweep",
    "agentic-kit dpa final-closeout-check", "agentic-kit github-create", "agentic-kit init",
    "agentic-kit kit return-install", "agentic-kit kit return-revert", "agentic-kit kit update",
    "agentic-kit post-release-doi-closeout", "agentic-kit release abandon", "agentic-kit release prepare",
    "agentic-kit release ready", "agentic-kit release run", "agentic-kit release-prep",
    "agentic-kit release-publish", "agentic-kit transfer admin-refresh-pr",
    "agentic-kit transfer chat-switch-complete", "agentic-kit transfer evidence-pr-complete",
    "agentic-kit transfer post-merge-complete", "agentic-kit transfer post-merge-settle",
    "agentic-kit transfer pr-closeout-complete", "agentic-kit transfer pr-complete",
    "agentic-kit transfer pr-create-complete", "agentic-kit transfer remote-next",
    "agentic-kit transfer remote-work-start", "agentic-kit transfer sync-main", "agentic-kit work finish",
    "agentic-kit work recover", "agentic-kit work rescue", "agentic-kit work start", "agentic-kit workflow go",
    "agentic-kit workspace adopt", "agentic-kit workspace dpa-intake", "agentic-kit workspace init",
    "agentic-kit workspace remove", "agentic-kit workspace upgrade",
})

# Orchestrators whose command callback prints only through its module's _emit, and that _emit
# routes every payload through blocked_route.with_route before printing (checked by AST below).
EMITTER_GUARDED = frozenset({
    "agentic-kit work start", "agentic-kit work finish", "agentic-kit work recover", "agentic-kit work rescue",
    "agentic-kit release ready", "agentic-kit release prepare", "agentic-kit release run",
    "agentic-kit release abandon", "agentic-kit kit update", "agentic-kit kit return-install",
    "agentic-kit kit return-revert",
})

# Not yet conformant. May only shrink: lower DEBT_CEILING whenever an entry leaves.
DEBT_CEILING = 26
DEBT = frozenset({
    "agentic-kit artifact-gc", "agentic-kit chat session-start", "agentic-kit docs lifecycle sweep",
    "agentic-kit dpa final-closeout-check", "agentic-kit github-create", "agentic-kit init",
    "agentic-kit post-release-doi-closeout", "agentic-kit release-prep", "agentic-kit release-publish",
    "agentic-kit transfer admin-refresh-pr", "agentic-kit transfer chat-switch-complete",
    "agentic-kit transfer evidence-pr-complete", "agentic-kit transfer post-merge-complete",
    "agentic-kit transfer post-merge-settle", "agentic-kit transfer pr-closeout-complete",
    "agentic-kit transfer pr-complete", "agentic-kit transfer pr-create-complete", "agentic-kit transfer remote-next",
    "agentic-kit transfer remote-work-start", "agentic-kit transfer sync-main", "agentic-kit workflow go",
    "agentic-kit workspace adopt", "agentic-kit workspace dpa-intake", "agentic-kit workspace init",
    "agentic-kit workspace remove", "agentic-kit workspace upgrade",
})


def _orchestrators() -> dict[str, list[str]]:
    commands = json.loads(MANIFEST.read_text(encoding="utf-8"))["commands"]
    return {c["qualified_name"]: list(c["path"]) for c in commands if c.get("surface") == "orchestrator"}


def _callback(path: list[str]):
    command = typer.main.get_command(app)
    for part in path:
        command = command.commands[part]
    return command.callback


def test_baseline_is_pinned():
    assert hashlib.sha256("\n".join(sorted(BASELINE)).encode()).hexdigest() == BASELINE_SHA256


def test_every_orchestrator_is_conformant_or_on_the_debt_list():
    orchestrators = set(_orchestrators())
    assert not EMITTER_GUARDED & DEBT
    assert orchestrators - DEBT - EMITTER_GUARDED == set(), "unclassified orchestrator: make it conformant"
    assert DEBT - orchestrators == set(), "stale debt entry: remove it"
    assert EMITTER_GUARDED <= orchestrators


def test_debt_only_shrinks():
    assert DEBT <= BASELINE, "new orchestrators cannot go on the debt list"
    assert len(DEBT) <= DEBT_CEILING, "the debt list grew"


@pytest.mark.parametrize("name", sorted(EMITTER_GUARDED))
def test_guarded_orchestrators_print_only_through_a_routing_emitter(name):
    callback = _callback(_orchestrators()[name])
    tree = ast.parse(textwrap.dedent(inspect.getsource(callback)))
    printers = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = ast.unparse(node.func)
            if func in {"typer.echo", "print", "console.print"} or ("emit" in func or "echo" in func or "print" in func):
                printers.add(func)
    assert printers == {"_emit"}, f"{name} prints through {sorted(printers)}"
    emitter = getattr(inspect.getmodule(callback), "_emit")
    body = ast.parse(textwrap.dedent(inspect.getsource(emitter))).body[0].body
    first = body[1] if isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) else body[0]
    assert ast.unparse(first) == "payload = with_route(payload)", f"{emitter.__module__}._emit does not route first"


def test_payload_builder_routes_kit_commands():
    step = _failed_local_step("b", "x")
    step.update(next_command="agentic-kit work finish --branch b --execute", next_command_autonomous=True)
    payload = _payload("work-finish", [step])
    assert route_problems(payload) == []
    assert payload["next_command_kind"] == KIND_KIT and payload["next_command_reason"] == ""


def test_payload_builder_marks_unrouted_blocks_for_a_human():
    payload = _payload("release-ready", [_noop_step("a", ""), _failed_local_step("release-status", "tag missing\nmore")])
    assert route_problems(payload) == []
    assert payload["next_command_kind"] == KIND_HUMAN and payload["next_command"] == ""
    assert payload["next_command_autonomous"] is False
    assert "release-status" in payload["next_command_reason"] and "tag missing" in payload["next_command_reason"]


def test_an_explicit_human_reason_wins():
    step = _failed_local_step("approval", "x")
    step["next_command_reason"] = "The owner must approve the release."
    assert _payload("release-ready", [step])["next_command_reason"] == "The owner must approve the release."


def test_route_problems_rejects_half_routes():
    blocked = {"result_status": "BLOCKED"}
    assert route_problems(blocked)
    assert route_problems({**blocked, "next_command": "", "next_command_autonomous": False,
                           "next_command_kind": KIND_HUMAN, "next_command_reason": ""})
    assert route_problems({**blocked, "next_command": "x", "next_command_autonomous": True,
                           "next_command_kind": KIND_HUMAN, "next_command_reason": "r"})
    assert route_problems({**blocked, "next_command": "", "next_command_autonomous": False,
                           "next_command_kind": KIND_KIT, "next_command_reason": ""})
    assert route_problems({"result_status": "PASS"}) == []


def test_unrouted_reason_reads_a_nested_kit_result():
    nested = {"result_status": "FAIL", "next_action": "Inspect the PR lookup: gh_pr_list_failed", "blockers": ["x"]}
    step = _failed_local_step("pr-create-complete", "")
    step["stdout"] = json.dumps(nested, indent=2)
    reason = _payload("work-finish", [step])["next_command_reason"]
    assert reason.endswith("pr-create-complete: Inspect the PR lookup: gh_pr_list_failed")
    step["stdout"] = json.dumps({"blockers": ["gh_pr_list_failed"]})
    assert _payload("work-finish", [step])["next_command_reason"].endswith("blockers gh_pr_list_failed")


def test_with_route_marks_unrouted_payloads_in_their_own_words():
    kit_update = with_route({"result_status": "BLOCKED", "blocker": "wheel download failed", "next_action": "x"})
    assert route_problems(kit_update) == [] and kit_update["next_command_reason"] == "wheel download failed"
    release_run = with_route({"result_status": "BLOCKED", "blockers": ["post-release-check-not-run"],
                              "next_action": "Continue release run."})
    assert release_run["next_command_reason"] == "blockers post-release-check-not-run"
    routed = with_route({"result_status": "FAIL", "next_command": "agentic-kit kit update --latest"})
    assert routed["next_command_kind"] == KIND_KIT and routed["next_command_autonomous"] is False
    assert with_route({"result_status": "PASS"}) == {"result_status": "PASS"}


def test_unrouted_reason_reads_state_and_next_from_a_summary():
    step = _failed_local_step("post-merge-check", "")
    step["stdout"] = "*** START SUMMARY ***\nSTATE:  FAIL\nNEXT_COMMAND_REASON:  STATE=NEEDS_SUCCESSOR_PACKAGE_REFRESH\nNEXT=refresh_successor_package\n"
    reason = _payload("work-start", [step])["next_command_reason"]
    assert reason.endswith("post-merge-check: STATE=NEEDS_SUCCESSOR_PACKAGE_REFRESH, NEXT=refresh_successor_package")
