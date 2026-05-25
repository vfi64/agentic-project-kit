from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

VALID_STATES = {"empty", "prepared", "running", "completed", "failed", "blocked", "recovery_needed"}

EVIDENCE_LOOKUP_ORDER = (
    "docs/reports/command_runs/next-turn-latest.json",
    "docs/reports/command_runs/next-turn-latest.md",
    "docs/reports/terminal/next-turn-latest.log",
    ".agentic/commands/executed.jsonl",
)

@dataclass(frozen=True)
class NextTurnStatus:
    state: str
    yaml_exists: bool
    script_exists: bool
    overwrite_allowed: bool
    reason: str

def _extract_state(yaml_text: str) -> str | None:
    match = re.search(r"(?m)^state:\s*([A-Za-z0-9_-]+)\s*$", yaml_text)
    return match.group(1) if match else None

def detect_next_turn_status(root: Path | str = ".") -> NextTurnStatus:
    root_path = Path(root)
    yaml_path = root_path / ".agentic/commands/next-turn.yaml"
    script_path = root_path / ".agentic/commands/next-turn.py"
    yaml_exists = yaml_path.exists()
    script_exists = script_path.exists()
    if not yaml_exists and not script_exists:
        return NextTurnStatus("empty", False, False, True, "no fixed-slot files exist")
    if yaml_exists != script_exists:
        return NextTurnStatus("blocked", yaml_exists, script_exists, False, "partial fixed-slot state")
    try:
        declared = _extract_state(yaml_path.read_text(encoding="utf-8"))
    except UnicodeDecodeError:
        return NextTurnStatus("blocked", True, True, False, "next-turn yaml is not valid utf-8")
    if declared is None:
        return NextTurnStatus("blocked", True, True, False, "next-turn yaml has no state field")
    if declared not in VALID_STATES:
        return NextTurnStatus("blocked", True, True, False, f"unknown state: {declared}")
    overwrite_allowed = declared in {"completed", "failed"}
    reason = "completed or failed slot may be replaced" if overwrite_allowed else f"{declared} slot must not be overwritten"
    return NextTurnStatus(declared, True, True, overwrite_allowed, reason)

def _bool(value: bool) -> str:
    return "true" if value else "false"

def render_status(status: NextTurnStatus) -> str:
    lines = [
        "NEXT_TURN_STATUS",
        f"state={status.state}",
        f"yaml_exists={_bool(status.yaml_exists)}",
        f"script_exists={_bool(status.script_exists)}",
        f"overwrite_allowed={_bool(status.overwrite_allowed)}",
        f"reason={status.reason}",
        "evidence_lookup_order:",
    ]
    lines.extend(f"- {path}" for path in EVIDENCE_LOOKUP_ORDER)
    lines.append("### RESULT: PASS ###")
    return "\n".join(lines)

def _read_preview(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="replace")
    if path.suffix == ".json":
        try:
            return json.dumps(json.loads(text), indent=2, sort_keys=True)
        except json.JSONDecodeError:
            return text[:4000]
    if path.name == "executed.jsonl":
        lines = [line for line in text.splitlines() if line.strip()]
        return lines[-1] if lines else ""
    return text[:4000]

def find_last_result(root: Path | str = ".") -> tuple[Path | None, list[str], str]:
    root_path = Path(root)
    checked: list[str] = []
    for relative in EVIDENCE_LOOKUP_ORDER:
        checked.append(relative)
        candidate = root_path / relative
        if candidate.exists():
            return candidate, checked, _read_preview(candidate)
    return None, checked, ""

def render_last_result(root: Path | str = ".") -> str:
    found, checked, preview = find_last_result(root)
    lines: list[str] = ["NEXT_TURN_LAST_RESULT"]
    if found is None:
        lines.append("status=NO_RESULT_FOUND")
        lines.append("checked_paths:")
        lines.extend(f"- {path}" for path in checked)
        lines.append("recovery=run ./ns next-turn --status before requesting pasted terminal output")
        lines.append("### RESULT: PASS ###")
        return "\n".join(lines)
    try:
        relative = found.relative_to(Path(root))
    except ValueError:
        relative = found
    lines.append("status=FOUND")
    lines.append(f"path={relative}")
    lines.append("checked_paths:")
    lines.extend(f"- {path}" for path in checked)
    lines.append("preview:")
    lines.append(preview)
    lines.append("### RESULT: PASS ###")
    return "\n".join(lines)

def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="next-turn-status")
    subparsers = parser.add_subparsers(dest="command", required=True)
    next_turn = subparsers.add_parser("next-turn")
    next_turn.add_argument("--status", action="store_true")
    subparsers.add_parser("last-result")
    args = parser.parse_args(list(argv) if argv is not None else None)
    if args.command == "next-turn":
        print(render_status(detect_next_turn_status()))
        return 0
    if args.command == "last-result":
        print(render_last_result())
        return 0
    raise AssertionError(args.command)

if __name__ == "__main__":
    raise SystemExit(main())
