"""G3: every BLOCKED or FAIL orchestrator result names its way on.

A result either names the Kit command that resolves it (``next_command_kind = "kit"``, with
``next_command`` and ``next_command_autonomous``), or it carries the human marker
(``next_command_kind = "human"``): no automatic route, ``next_command`` stays empty and the
mandatory ``next_command_reason`` says why a person has to act. Cockpit and LLM sessions then
read the route instead of interpreting free text (owner decision 2026-11-13: ratchet plus human
marker).
"""
from __future__ import annotations

import json
from collections.abc import Mapping

KIND_KIT = "kit"
KIND_HUMAN = "human"
ROUTE_KINDS = frozenset({KIND_KIT, KIND_HUMAN})
ROUTE_STATUSES = frozenset({"BLOCKED", "FAIL"})
ROUTE_FIELDS = ("next_command", "next_command_autonomous", "next_command_kind", "next_command_reason")


def kit_route(command: str, *, autonomous: bool = False) -> dict[str, object]:
    """Route fields for a result that a Kit command resolves."""
    if not command.strip():
        raise ValueError("a kit route needs the resolving command")
    return {
        "next_command": command,
        "next_command_autonomous": bool(autonomous),
        "next_command_kind": KIND_KIT,
        "next_command_reason": "",
    }


def human_route(reason: str) -> dict[str, object]:
    """Route fields for a result without an automatic route; the reason is mandatory."""
    reason = reason.strip()
    if not reason:
        raise ValueError("the human marker needs a reason")
    return {
        "next_command": "",
        "next_command_autonomous": False,
        "next_command_kind": KIND_HUMAN,
        "next_command_reason": reason,
    }


def route_fields(command: str, *, autonomous: bool, reason: str) -> dict[str, object]:
    """A named command wins; otherwise the human marker with ``reason``."""
    if command.strip():
        return kit_route(command, autonomous=autonomous)
    return human_route(reason)


def first_line(text: object) -> str:
    for line in str(text or "").splitlines():
        if line.strip():
            return line.strip()
    return ""


def route_problems(result: Mapping[str, object]) -> list[str]:
    """Contract violations of one result; results outside BLOCKED/FAIL need no route."""
    if result.get("result_status") not in ROUTE_STATUSES:
        return []
    problems = [f"missing {name}" for name in ROUTE_FIELDS if name not in result]
    if problems:
        return problems
    kind = result["next_command_kind"]
    command = result["next_command"]
    autonomous = result["next_command_autonomous"]
    reason = result["next_command_reason"]
    if not isinstance(autonomous, bool):
        problems.append("next_command_autonomous must be a bool")
    if kind == KIND_KIT:
        if not isinstance(command, str) or not command.strip():
            problems.append("kit route without next_command")
    elif kind == KIND_HUMAN:
        if command != "":
            problems.append("human marker must leave next_command empty")
        if autonomous is not False:
            problems.append("human marker cannot be autonomous")
        if not isinstance(reason, str) or not reason.strip():
            problems.append("human marker without next_command_reason")
    else:
        problems.append(f"next_command_kind must be one of {sorted(ROUTE_KINDS)}, got {kind!r}")
    return problems


def with_route(payload: Mapping[str, object]) -> dict[str, object]:
    """Emitter-level G3: a BLOCKED/FAIL payload without a valid route gets one before printing.

    A named ``next_command`` becomes a kit route; otherwise the human marker, whose reason is the
    payload's own words: ``next_command_reason``, ``blocker``, ``blockers`` or ``next_action``.
    """
    data = dict(payload)
    if data.get("result_status") not in ROUTE_STATUSES or not route_problems(data):
        return data
    blockers = data.get("blockers")
    blocker_text = ", ".join(str(item) for item in blockers) if isinstance(blockers, list) and blockers else ""
    reason = (
        first_line(data.get("next_command_reason"))
        or first_line(data.get("blocker"))
        or (f"blockers {blocker_text}" if blocker_text else "")
        or first_line(data.get("next_action"))
        or f"{data.get('kind') or data.get('action') or 'result'} ended {data['result_status']} without a Kit route."
    )
    data.update(route_fields(
        str(data.get("next_command") or ""),
        autonomous=data.get("next_command_autonomous") is True,
        reason=reason,
    ))
    return data


def nested_route(result: object) -> dict[str, object]:
    """The Kit route a nested Kit result already names (K6: a CI state seen in pr-complete).

    ``result`` is that command's parsed JSON or its stdout. Only a complete kit route is inherited,
    with the nested ``ci_state`` if there is one; a human marker or an incomplete route is not.
    """
    if isinstance(result, str):
        try:
            result = json.loads(result)
        except ValueError:
            return {}
    if not isinstance(result, Mapping) or result.get("next_command_kind") != KIND_KIT:
        return {}
    if route_problems({**result, "result_status": "BLOCKED"}):
        return {}
    inherited = {name: result[name] for name in ROUTE_FIELDS}
    if result.get("ci_state"):
        inherited["ci_state"] = result["ci_state"]
    return inherited
