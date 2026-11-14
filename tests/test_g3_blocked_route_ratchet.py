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
from agentic_project_kit.cli_commands.transfer_shared import _emit_transfer

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

# Orchestrators whose command callback prints only through routing emitters (checked by AST
# below): a routing emitter's first statement is ``payload = with_route(payload)`` (work/release/kit
# ``_emit``, transfer ``_emit_transfer``); a delegate such as ``_echo_repo_result`` qualifies when it
# prints only through routing emitters itself.
EMITTER_GUARDED = frozenset({
    "agentic-kit work start", "agentic-kit work finish", "agentic-kit work recover", "agentic-kit work rescue",
    "agentic-kit release ready", "agentic-kit release prepare", "agentic-kit release run",
    "agentic-kit release abandon", "agentic-kit kit update", "agentic-kit kit return-install",
    "agentic-kit kit return-revert",
    "agentic-kit transfer admin-refresh-pr", "agentic-kit transfer chat-switch-complete",
    "agentic-kit transfer evidence-pr-complete", "agentic-kit transfer post-merge-complete",
    "agentic-kit transfer post-merge-settle", "agentic-kit transfer pr-closeout-complete",
    "agentic-kit transfer pr-complete", "agentic-kit transfer pr-create-complete", "agentic-kit transfer remote-next",
    "agentic-kit transfer remote-work-start", "agentic-kit transfer sync-main",
})

# Not yet conformant. May only shrink: lower DEBT_CEILING whenever an entry leaves.
DEBT_CEILING = 15
DEBT = frozenset({
    "agentic-kit artifact-gc", "agentic-kit chat session-start", "agentic-kit docs lifecycle sweep",
    "agentic-kit dpa final-closeout-check", "agentic-kit github-create", "agentic-kit init",
    "agentic-kit post-release-doi-closeout", "agentic-kit release-prep", "agentic-kit release-publish",
    "agentic-kit workflow go", "agentic-kit workspace adopt", "agentic-kit workspace dpa-intake",
    "agentic-kit workspace init", "agentic-kit workspace remove", "agentic-kit workspace upgrade",
})
ROUTING_FIRST_STATEMENT = "payload = with_route(payload)"


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


def _is_printer(func: str) -> bool:
    return func in {"typer.echo", "print", "console.print"} or any(word in func for word in ("emit", "echo", "print"))


def _printers(function) -> set[str]:
    """Printing calls of ``function``; text projections handed to an emitter (``text=``) run after
    routing and are skipped. Local aliases from ``_public_transfer_attr("X", X)`` resolve to X."""
    tree = ast.parse(textwrap.dedent(inspect.getsource(function)))
    aliases, deferred, skipped = {}, set(), set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call) and len(node.targets) == 1:
            call = node.value
            if ast.unparse(call.func) == "_public_transfer_attr" and len(call.args) == 2:
                aliases[ast.unparse(node.targets[0])] = ast.unparse(call.args[1])
        if isinstance(node, ast.Call):
            for keyword in node.keywords:
                if keyword.arg == "text":
                    if isinstance(keyword.value, ast.Lambda):
                        skipped.update(id(inner) for inner in ast.walk(keyword.value))
                    elif isinstance(keyword.value, ast.Name):
                        deferred.add(keyword.value.id)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name in deferred:
            skipped.update(id(inner) for inner in ast.walk(node))
    printers = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and id(node) not in skipped:
            func = ast.unparse(node.func)
            if _is_printer(func):
                printers.add(aliases.get(func, func))
    return printers


def _routes(function, depth: int = 0) -> bool:
    """A routing emitter, or a delegate that prints only through routing emitters."""
    body = ast.parse(textwrap.dedent(inspect.getsource(function))).body[0].body
    first = body[1] if isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) else body[0]
    if ast.unparse(first) == ROUTING_FIRST_STATEMENT:
        return True
    return depth < 3 and _all_route(function, depth + 1)


def _all_route(function, depth: int = 0) -> bool:
    module = inspect.getmodule(function)
    printers = _printers(function)
    if not printers:
        return False
    for name in printers:
        target = getattr(module, name, None)
        if not inspect.isfunction(target) or not _routes(target, depth):
            return False
    return True


@pytest.mark.parametrize("name", sorted(EMITTER_GUARDED))
def test_guarded_orchestrators_print_only_through_a_routing_emitter(name):
    callback = _callback(_orchestrators()[name])
    module = inspect.getmodule(callback)
    for printer in sorted(_printers(callback)):
        target = getattr(module, printer, None)
        assert inspect.isfunction(target), f"{name} prints through {printer}, not a routing emitter"
        assert _routes(target), f"{name} prints through {printer}, which does not route first"
    assert _printers(callback), f"{name} prints nothing through an emitter"


def test_the_ratchet_rejects_a_direct_print():
    def callback(payload, json_output):
        _emit_transfer(payload, json_output=json_output, text=lambda routed: typer.echo("fine, after routing"))
        typer.echo("bypasses the route")

    assert _printers(callback) == {"_emit_transfer", "typer.echo"}


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
