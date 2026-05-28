from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

FIXED_SLOT_YAML = Path(".agentic/commands/inbox/next-turn.yaml")
FIXED_SLOT_SCRIPT = Path(".agentic/commands/inbox/next-turn.py")

@dataclass(frozen=True)
class FixedSlotStatus:
    state: str
    yaml_exists: bool
    script_exists: bool
    overwrite_allowed: bool
    reason: str
    yaml_path: str
    script_path: str

def fixed_slot_status(root: Path | str = ".") -> FixedSlotStatus:
    root_path = Path(root)
    yaml_path = root_path / FIXED_SLOT_YAML
    script_path = root_path / FIXED_SLOT_SCRIPT
    yaml_exists = yaml_path.exists()
    script_exists = script_path.exists()
    if yaml_exists and script_exists:
        return FixedSlotStatus("ready", True, True, False, "fixed-slot work order exists", str(FIXED_SLOT_YAML), str(FIXED_SLOT_SCRIPT))
    if yaml_exists or script_exists:
        return FixedSlotStatus("partial", yaml_exists, script_exists, False, "fixed-slot work order is incomplete; use --force only after inspection", str(FIXED_SLOT_YAML), str(FIXED_SLOT_SCRIPT))
    return FixedSlotStatus("empty", False, False, True, "no fixed-slot work order exists", str(FIXED_SLOT_YAML), str(FIXED_SLOT_SCRIPT))

def render_status(status: FixedSlotStatus) -> str:
    return "\n".join([
        "NEXT_TURN_FIXED_SLOT_STATUS",
        f"state={status.state}",
        f"yaml_exists={str(status.yaml_exists).lower()}",
        f"script_exists={str(status.script_exists).lower()}",
        f"overwrite_allowed={str(status.overwrite_allowed).lower()}",
        f"yaml_path={status.yaml_path}",
        f"script_path={status.script_path}",
        f"reason={status.reason}",
        "### RESULT: PASS ###",
    ])

def default_yaml(command_id: str = "next-turn") -> str:
    return "\n".join([
        "schema_version: 1",
        f"command_id: {command_id}",
        "kind: fixed-slot-work-order",
        "slot: next-turn",
        "entrypoint: .agentic/commands/inbox/next-turn.py",
        "safety_class: bounded",
        "status: pending",
        "evidence:",
        "  local_terminal_log: /tmp/agentic-project-kit/next-turn-latest.log",
        "  remote_terminal_log: docs/reports/terminal/next-turn-latest.log",
        "  command_report: docs/reports/command_runs/next-turn-latest.json",
        "",
    ])

def default_script() -> str:
    return "\n".join([
        "#!/usr/bin/env python3",
        "from __future__ import annotations",
        "",
        "def main() -> int:",
        "    print(\"NEXT_TURN_FIXED_SLOT_PLACEHOLDER\")",
        "    print(\"status=pending_runner\")",
        "    print(\"### RESULT: PASS ###\")",
        "    return 0",
        "",
        "if __name__ == \"__main__\":",
        "    raise SystemExit(main())",
        "",
    ])

def write_fixed_slot(root: Path | str = ".", *, force: bool = False, command_id: str = "next-turn") -> FixedSlotStatus:
    root_path = Path(root)
    status = fixed_slot_status(root_path)
    if status.state != "empty" and not force:
        raise RuntimeError(f"fixed slot is not empty: {status.state}")
    yaml_path = root_path / FIXED_SLOT_YAML
    script_path = root_path / FIXED_SLOT_SCRIPT
    yaml_path.parent.mkdir(parents=True, exist_ok=True)
    yaml_path.write_text(default_yaml(command_id), encoding="utf-8")
    script_path.write_text(default_script(), encoding="utf-8")
    script_path.chmod(0o755)
    return fixed_slot_status(root_path)

def main() -> int:
    parser = argparse.ArgumentParser(prog="next-turn-slot")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status")
    write_parser = sub.add_parser("write")
    write_parser.add_argument("--force", action="store_true")
    write_parser.add_argument("--command-id", default="next-turn")
    args = parser.parse_args()
    if args.command == "status":
        print(render_status(fixed_slot_status()))
        return 0
    if args.command == "write":
        print(render_status(write_fixed_slot(force=args.force, command_id=args.command_id)))
        return 0
    raise AssertionError(args.command)

if __name__ == "__main__":
    raise SystemExit(main())
