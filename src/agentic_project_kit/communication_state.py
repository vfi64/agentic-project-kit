from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


DEFAULT_STATE_PATH = Path(".agentic/communication_state.json")
VALID_ORIGINS = {"local", "remote", "mixed"}


@dataclass(frozen=True)
class CommunicationStateCheck:
    ok: bool
    findings: tuple[str, ...]


def format_summary_id(value: int) -> str:
    if value < 0:
        raise ValueError("summary id must be non-negative")
    return f"COMM-{value:05d}"


def current_branch() -> str:
    result = subprocess.run(["git", "branch", "--show-current"], text=True, capture_output=True, check=False)
    return result.stdout.strip() or "unknown"


def load_state(path: Path = DEFAULT_STATE_PATH) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_state(state: dict[str, Any], path: Path = DEFAULT_STATE_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def check_state(path: Path = DEFAULT_STATE_PATH) -> CommunicationStateCheck:
    findings: list[str] = []
    if not path.exists():
        return CommunicationStateCheck(False, ("missing_state_file",))
    try:
        state = load_state(path)
    except json.JSONDecodeError:
        return CommunicationStateCheck(False, ("invalid_json",))
    if state.get("schema_version") != 1:
        findings.append("invalid_schema_version")
    summary_id = state.get("last_summary_id")
    if not isinstance(summary_id, int) or summary_id < 0:
        findings.append("invalid_last_summary_id")
    origin = state.get("last_origin")
    if origin is not None and origin not in VALID_ORIGINS:
        findings.append("invalid_last_origin")
    return CommunicationStateCheck(not findings, tuple(findings) if findings else ("none",))


def next_summary_header(
    path: Path = DEFAULT_STATE_PATH,
    origin: str = "local",
    branch: str | None = None,
    slice_name: str = "unknown",
    write: bool = True,
) -> str:
    if origin not in VALID_ORIGINS:
        raise ValueError(f"invalid origin: {origin}")
    state = load_state(path)
    next_id = int(state.get("last_summary_id", 0)) + 1
    now = datetime.now().astimezone()
    branch_name = branch or current_branch()
    header = f"SUMMARY {format_summary_id(next_id)} | {now:%Y-%m-%d %H:%M:%S %z}"
    if write:
        state["last_summary_id"] = next_id
        state["updated_at"] = now.isoformat(timespec="seconds")
        state["last_origin"] = origin
        state["last_branch"] = branch_name
        state["last_slice"] = slice_name
        write_state(state, path)
    return header


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="communication-state")
    sub = parser.add_subparsers(dest="command", required=True)
    check_parser = sub.add_parser("check")
    check_parser.add_argument("--state-path", default=str(DEFAULT_STATE_PATH))
    next_parser = sub.add_parser("next-summary")
    next_parser.add_argument("--state-path", default=str(DEFAULT_STATE_PATH))
    next_parser.add_argument("--origin", choices=sorted(VALID_ORIGINS), default="local")
    next_parser.add_argument("--branch", default=None)
    next_parser.add_argument("--slice", default="unknown")
    next_parser.add_argument("--no-write", action="store_true")
    args = parser.parse_args(argv)
    path = Path(args.state_path)
    if args.command == "check":
        result = check_state(path)
        print("COMMUNICATION STATE CHECK")
        print(f"state_path={path}")
        print(f"state={'PASS' if result.ok else 'FAIL'}")
        print("findings:")
        for finding in result.findings:
            print(f"  - {finding}")
        print(f"### RESULT: {'PASS' if result.ok else 'FAIL'} ###")
        return 0 if result.ok else 1
    print(next_summary_header(path, args.origin, args.branch, args.slice, not args.no_write))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
