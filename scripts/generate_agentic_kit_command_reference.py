from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from typer.main import get_command

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agentic_project_kit.cli import app  # noqa: E402

JSON_PATH = ROOT / "docs/reference/agentic-kit-commands.json"
MD_PATH = ROOT / "docs/reference/AGENTIC_KIT_COMMANDS.md"


@dataclass(frozen=True)
class CommandRecord:
    group: str
    name: str
    path: list[str]
    qualified_name: str
    help: str
    params: list[dict[str, Any]]

    def as_dict(self) -> dict[str, Any]:
        return {
            "group": self.group,
            "name": self.name,
            "path": self.path,
            "qualified_name": self.qualified_name,
            "help": self.help,
            "params": self.params,
        }


def _jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    return repr(value)


def _param_record(param: Any) -> dict[str, Any]:
    record: dict[str, Any] = {
        "name": param.name,
        "param_type": param.__class__.__name__,
        "required": bool(getattr(param, "required", False)),
        "default": _jsonable(getattr(param, "default", None)),
        "metavar": getattr(param, "metavar", None),
    }
    if hasattr(param, "opts"):
        record["opts"] = list(getattr(param, "opts", []))
        record["secondary_opts"] = list(getattr(param, "secondary_opts", []))
        record["help"] = getattr(param, "help", None) or ""
        record["is_flag"] = bool(getattr(param, "is_flag", False))
        record["multiple"] = bool(getattr(param, "multiple", False))
    return record


def _record_for(path: list[str], command: Any) -> CommandRecord:
    group = "root" if len(path) == 1 else " ".join(path[:-1])
    return CommandRecord(
        group=group,
        name=path[-1],
        path=path,
        qualified_name="agentic-kit " + " ".join(path),
        help=command.help or "",
        params=[_param_record(param) for param in command.params],
    )


def _walk(path: list[str], command: Any) -> list[CommandRecord]:
    commands = getattr(command, "commands", None)
    if isinstance(commands, dict):
        records: list[CommandRecord] = []
        for name in sorted(commands):
            records.extend(_walk([*path, name], commands[name]))
        return records
    return [_record_for(path, command)]


def build_reference() -> dict[str, Any]:
    root = get_command(app)
    commands: list[dict[str, Any]] = []
    for name, command in sorted(root.commands.items()):
        nested = getattr(command, "commands", None)
        if isinstance(nested, dict):
            commands.extend(record.as_dict() for record in _walk([name], command))
        else:
            commands.append(_record_for([name], command).as_dict())

    return {
        "schema_version": 2,
        "kind": "agentic_kit_command_reference",
        "source": "generated_from_typer_click_registry",
        "generated_by": "scripts/generate_agentic_kit_command_reference.py",
        "successor_execution_contract": "docs/reports/handoff-packages/latest/execution_contract.json",
        "commands": sorted(commands, key=lambda item: item["qualified_name"]),
    }


def render_markdown(data: dict[str, Any]) -> str:
    lines = [
        "# Agentic-kit command reference",
        "",
        "This file is generated from `docs/reference/agentic-kit-commands.json`.",
        "Do not edit this Markdown file manually.",
        "",
        "> Successor handoff contract note: the machine-readable successor execution contract is written to `docs/reports/handoff-packages/latest/execution_contract.json`. This generated command reference points to the contract instead of duplicating local-command rules.",
        "",
        f"- Schema version: `{data['schema_version']}`",
        f"- Source: `{data['source']}`",
        f"- Command count: `{len(data['commands'])}`",
        "",
        "## Commands",
        "",
    ]
    for command in data["commands"]:
        lines.append(f"### `{command['qualified_name']}`")
        lines.append("")
        if command["help"]:
            lines.append(command["help"].strip())
            lines.append("")
        if command["params"]:
            lines.append("| Parameter | Type | Options | Required | Default | Help |")
            lines.append("|---|---:|---|---:|---|---|")
            for param in command["params"]:
                opts = ", ".join(param.get("opts", []) + param.get("secondary_opts", []))
                default = "" if param.get("default") is None else f"`{param.get('default')}`"
                help_text = (param.get("help") or "").replace("\n", " ")
                lines.append(
                    f"| `{param.get('name')}` | `{param.get('param_type')}` | "
                    f"{opts} | `{param.get('required')}` | {default} | {help_text} |"
                )
            lines.append("")
        else:
            lines.append("_No parameters._")
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def write_reference() -> None:
    data = build_reference()
    JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    JSON_PATH.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    MD_PATH.write_text(render_markdown(data), encoding="utf-8")


if __name__ == "__main__":
    write_reference()
