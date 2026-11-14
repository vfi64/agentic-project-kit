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

from agentic_project_kit.blocked_route import KIND_HUMAN, KIND_KIT, route_problems
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

# Orchestrators whose command callback builds every result with human_workflows._payload and
# prints it only through _emit.
PAYLOAD_BUILDER = frozenset({
    "agentic-kit work start", "agentic-kit work finish", "agentic-kit work recover",
    "agentic-kit release ready", "agentic-kit release prepare",
})

# Not yet conformant. May only shrink.
DEBT = frozenset({
    "agentic-kit artifact-gc", "agentic-kit chat session-start", "agentic-kit docs lifecycle sweep",
    "agentic-kit dpa final-closeout-check", "agentic-kit github-create", "agentic-kit init",
    "agentic-kit kit return-install", "agentic-kit kit return-revert", "agentic-kit kit update",
    "agentic-kit post-release-doi-closeout", "agentic-kit release abandon", "agentic-kit release run",
    "agentic-kit release-prep", "agentic-kit release-publish", "agentic-kit transfer admin-refresh-pr",
    "agentic-kit transfer chat-switch-complete", "agentic-kit transfer evidence-pr-complete",
    "agentic-kit transfer post-merge-complete", "agentic-kit transfer post-merge-settle",
    "agentic-kit transfer pr-closeout-complete", "agentic-kit transfer pr-complete",
    "agentic-kit transfer pr-create-complete", "agentic-kit transfer remote-next",
    "agentic-kit transfer remote-work-start", "agentic-kit transfer sync-main", "agentic-kit work rescue",
    "agentic-kit workflow go", "agentic-kit workspace adopt", "agentic-kit workspace dpa-intake",
    "agentic-kit workspace init", "agentic-kit workspace remove", "agentic-kit workspace upgrade",
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
    assert not PAYLOAD_BUILDER & DEBT
    assert orchestrators - DEBT - PAYLOAD_BUILDER == set(), "unclassified orchestrator: make it conformant"
    assert DEBT - orchestrators == set(), "stale debt entry: remove it"
    assert PAYLOAD_BUILDER <= orchestrators


def test_debt_only_shrinks():
    assert DEBT <= BASELINE, "new orchestrators cannot go on the debt list"
    assert len(DEBT) < len(BASELINE)


@pytest.mark.parametrize("name", sorted(PAYLOAD_BUILDER))
def test_payload_builder_orchestrators_emit_only_payload_results(name):
    callback = _callback(_orchestrators()[name])
    tree = ast.parse(textwrap.dedent(inspect.getsource(callback)))
    sources, emitted = [], []
    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if any(isinstance(t, ast.Name) and t.id == "payload" for t in targets):
                sources.append(ast.unparse(node.value.func) if isinstance(node.value, ast.Call) else "<not a call>")
        if isinstance(node, ast.Call):
            func = ast.unparse(node.func)
            assert func not in {"typer.echo", "print"}, f"{name} prints outside _emit"
            if func == "_emit":
                emitted.append(ast.unparse(node.args[0]))
    assert sources and set(sources) == {"_payload"}, f"{name} builds results with {sources}"
    assert emitted and set(emitted) == {"payload"}, f"{name} emits {emitted}"


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
