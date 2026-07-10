from __future__ import annotations

from dataclasses import dataclass
from typing import Any


SAFETY_SORT_ORDER = {"READ_ONLY": 0, "BOUNDED": 1, "DESTRUCTIVE": 2}


@dataclass(frozen=True)
class CommandSelection:
    status: str
    payload: dict[str, Any]


def normalize_raw_command(command_line: str) -> str:
    """Normalize a pasted shell command for deterministic manifest lookup."""
    text = command_line.strip()
    while text and text[0] in "$#>":
        text = text[1:].lstrip()
    return " ".join(text.split())


def _matches_prefix(command_line: str, prefix: str) -> bool:
    return command_line == prefix or command_line.startswith(prefix + " ")


def _command_summary(command: dict[str, Any]) -> dict[str, Any]:
    return {
        "qualified_name": str(command.get("qualified_name") or ""),
        "safety": str(command.get("safety") or ""),
        "when_to_use": str(command.get("when_to_use") or ""),
        "dry_run_available": bool(command.get("dry_run_available")),
    }


def select_for_raw(manifest: dict[str, Any], command_line: str) -> CommandSelection:
    normalized = normalize_raw_command(command_line)
    matches: list[tuple[str, dict[str, Any]]] = []
    for command in manifest.get("commands") or []:
        if not isinstance(command, dict):
            continue
        for raw_prefix in command.get("replaces_raw") or []:
            prefix = normalize_raw_command(str(raw_prefix))
            if prefix and _matches_prefix(normalized, prefix):
                matches.append((prefix, command))

    if not matches:
        return CommandSelection(
            status="no_match",
            payload={
                "mode": "raw",
                "status": "no_match",
                "raw": command_line,
                "normalized_raw": normalized,
                "message": "no mapping; if this mutates the repo, check the manifest before running raw",
            },
        )

    longest = max(len(prefix) for prefix, _command in matches)
    selected = [
        command for prefix, command in matches if len(prefix) == longest
    ]
    selected.sort(key=lambda command: str(command.get("qualified_name") or ""))
    matched_prefix = sorted({prefix for prefix, _command in matches if len(prefix) == longest})[0]
    return CommandSelection(
        status="match",
        payload={
            "mode": "raw",
            "status": "match",
            "raw": command_line,
            "normalized_raw": normalized,
            "matched_prefix": matched_prefix,
            "commands": [_command_summary(command) for command in selected],
        },
    )


def _all_task_tags(manifest: dict[str, Any]) -> list[str]:
    tags: set[str] = set()
    for command in manifest.get("commands") or []:
        if not isinstance(command, dict):
            continue
        tags.update(str(tag) for tag in command.get("task_tags") or [] if str(tag).strip())
    return sorted(tags)


def select_for_task(manifest: dict[str, Any], task_tag: str) -> CommandSelection:
    commands = [
        command
        for command in manifest.get("commands") or []
        if isinstance(command, dict) and task_tag in set(command.get("task_tags") or [])
    ]
    if not commands:
        return CommandSelection(
            status="unknown_tag",
            payload={
                "mode": "task",
                "status": "unknown_tag",
                "task_tag": task_tag,
                "available_tags": _all_task_tags(manifest),
            },
        )

    commands.sort(
        key=lambda command: (
            SAFETY_SORT_ORDER.get(str(command.get("safety") or ""), 99),
            str(command.get("qualified_name") or ""),
        )
    )
    return CommandSelection(
        status="match",
        payload={
            "mode": "task",
            "status": "match",
            "task_tag": task_tag,
            "commands": [_command_summary(command) for command in commands],
        },
    )


def render_command_selection(selection: CommandSelection) -> str:
    payload = selection.payload
    if payload["mode"] == "raw":
        lines = [
            "COMMAND_FOR",
            f"STATUS={payload['status']}",
            f"RAW={payload['raw']}",
            f"NORMALIZED_RAW={payload['normalized_raw']}",
        ]
        if payload["status"] == "no_match":
            lines.append(str(payload["message"]))
            return "\n".join(lines) + "\n"
        lines.append(f"MATCHED_PREFIX={payload['matched_prefix']}")
        for command in payload["commands"]:
            dry_run = "yes" if command["dry_run_available"] else "no"
            lines.append(
                "WRAPPER="
                f"{command['qualified_name']} | safety={command['safety']} | "
                f"dry_run_available={dry_run} | when_to_use={command['when_to_use']}"
            )
        return "\n".join(lines) + "\n"

    lines = [
        "COMMAND_FOR",
        f"STATUS={payload['status']}",
        f"TASK_TAG={payload['task_tag']}",
    ]
    if payload["status"] == "unknown_tag":
        lines.append("AVAILABLE_TAGS=" + ", ".join(payload["available_tags"]))
        return "\n".join(lines) + "\n"
    for command in payload["commands"]:
        lines.append(
            f"COMMAND={command['qualified_name']} | safety={command['safety']} | "
            f"when_to_use={command['when_to_use']}"
        )
    return "\n".join(lines) + "\n"
