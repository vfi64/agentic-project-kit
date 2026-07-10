from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any

import yaml


@dataclass(frozen=True)
class InstructionLintResult:
    result_status: str
    blockers: list[str]
    checked_path: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "instruction_lint_result",
            "result_status": self.result_status,
            "blockers": self.blockers,
            "checked_path": self.checked_path,
        }


_RAW_GITHUB_RE = re.compile(r"(^|[;&|]\s*)(gh|curl)\s+(pr|api|repos|https://api\.github\.com)\b")
_ANGLE_PLACEHOLDER_RE = re.compile(r"<[^>\n]+>")
_UNSAFE_SHELL_RE = re.compile(
    r"(^|[;&|]\s*)("
    r"rm\s+-rf\s+(?:/|\.|docs|src|tests|\.agentic)|"
    r"sudo\b|"
    r"chmod\s+-R\s+777\b|"
    r"git\s+push\s+--force\b|"
    r"git\s+reset\s+--hard\s+origin/main\b"
    r")"
)


def _iter_commands(value: Any) -> list[str]:
    commands: list[str] = []

    if isinstance(value, dict):
        for key, item in value.items():
            if key in {"run", "command", "cmd", "shell"} and isinstance(item, str):
                commands.append(item)
            else:
                commands.extend(_iter_commands(item))
    elif isinstance(value, list):
        for item in value:
            commands.extend(_iter_commands(item))

    return commands


def _load_payload(path: Path) -> Any:
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        return {}
    loaded = yaml.safe_load(text)
    return loaded if loaded is not None else {}


def lint_transfer_instruction(path: str | Path) -> InstructionLintResult:
    payload_path = Path(path)
    blockers: list[str] = []

    try:
        payload = _load_payload(payload_path)
    except Exception:
        return InstructionLintResult(
            result_status="BLOCKED",
            blockers=["invalid_transfer_payload"],
            checked_path=str(payload_path),
        )

    commands = _iter_commands(payload)

    for command in commands:
        stripped = command.strip()

        if _RAW_GITHUB_RE.search(stripped):
            blockers.append("raw_github_command")

        if "agentic-kit transfer pr-complete" in stripped and (
            "--pr " in stripped or "--post-merge-complete" in stripped
        ):
            blockers.append("stale_or_invalid_pr_complete_composition")

        if _ANGLE_PLACEHOLDER_RE.search(stripped):
            blockers.append("angle_bracket_placeholder")

        if _UNSAFE_SHELL_RE.search(stripped):
            blockers.append("unsafe_shell_command")

    unique_blockers = list(dict.fromkeys(blockers))
    return InstructionLintResult(
        result_status="BLOCKED" if unique_blockers else "PASS",
        blockers=unique_blockers,
        checked_path=str(payload_path),
    )
