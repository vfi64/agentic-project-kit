"""G3 emitter of the orchestrators outside the work, release, kit and transfer families.

``emit_routed`` routes a BLOCKED or FAIL payload before printing (``blocked_route.with_route``). A
payload that blocks under another status name (``BLOCK``, a domain status such as
``BLOCKED_FOR_DPA_INTAKE``) is routed the same way when the caller says it blocks, so every result
that ends the command with a non-zero exit names its way on. Exit codes stay with the caller.
"""
from __future__ import annotations

import json
import shlex
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import NoReturn

import typer

from agentic_project_kit.blocked_route import first_line, kit_route, with_blocked_route, with_route

BLOCK_STATUS = "BLOCK"


def emit_routed(
    payload: Mapping[str, object],
    *,
    json_output: bool,
    text: str | Callable[[dict[str, object]], str | None] | None = None,
    blocked: bool = False,
    err: bool = False,
) -> dict[str, object]:
    """Route, then print: JSON, or the text projection followed by the route lines."""
    payload = with_route(payload)  # G3 emitter guard; the ratchet test checks this line
    if blocked or payload.get("result_status") == BLOCK_STATUS:
        payload = with_blocked_route(payload)
    if json_output:
        typer.echo(json.dumps(payload, indent=2, sort_keys=True), err=err)
        return payload
    if isinstance(text, str):
        # A rendered projection is printed as given; the source-flow audit follows this path.
        typer.echo(text, nl=False, err=err)
    elif text is not None:
        rendered = text(payload)
        if rendered is not None:
            typer.echo(rendered, nl=False, err=err)
    echo_route_lines(payload, err=err)
    return payload


class RoutedRefusal(Exception):
    """A run that ends the command early: its payload (with the reason a person has to act or a
    Kit route) and the exit code. ``emit_refusal`` prints it."""

    def __init__(self, payload: Mapping[str, object], exit_code: int) -> None:
        super().__init__(str(payload.get("error") or ""))
        self.payload = dict(payload)
        self.exit_code = exit_code


def emit_refusal(refusal: RoutedRefusal, *, json_output: bool, text: str = "") -> NoReturn:
    """G3 for a refusal: the JSON on stdout, or ``text`` and ``Error: …`` plus the route lines on
    stderr; then the refusal's exit code."""
    emit_routed(
        refusal.payload,
        json_output=json_output,
        text=f"{text}Error: {refusal.payload.get('error')}\n",
        err=not json_output,
    )
    raise typer.Exit(code=refusal.exit_code)


def echo_route_lines(payload: Mapping[str, object], *, err: bool = False) -> None:
    """Text projection of a route, in the KEY=value form of the orchestrators' text output."""
    kind = payload.get("next_command_kind")
    if not kind:
        return
    typer.echo(f"NEXT_COMMAND_KIND={kind}", err=err)
    if payload.get("next_command"):
        typer.echo(f"NEXT_COMMAND={payload['next_command']}", err=err)
        typer.echo(f"NEXT_COMMAND_AUTONOMOUS={'yes' if payload.get('next_command_autonomous') else 'no'}", err=err)
    else:
        typer.echo(f"NEXT_COMMAND_REASON={first_line(payload.get('next_command_reason'))}", err=err)


def kit_command(*words: str, root: Path | None = None) -> str:
    """A Kit command line; ``--root`` only when the caller named a root other than the default."""
    parts = ["agentic-kit", *words]
    if root is not None and root != Path("."):
        parts += ["--root", str(root)]
    return " ".join(shlex.quote(part) for part in parts)


def read_only_route(*words: str, root: Path | None = None) -> dict[str, object]:
    """Kit route to a planning (read-only) command, which a session may run on its own."""
    return kit_route(kit_command(*words, root=root), autonomous=True)


def human_reason(reason: str) -> dict[str, object]:
    """The reason a person has to act; ``with_route`` turns it into the human marker."""
    return {"next_command_reason": reason}
