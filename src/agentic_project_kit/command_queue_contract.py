"""Machine-readable command queue state contract for GUI readiness.

The contract is intentionally read-only. It classifies the repo-backed
agent command inbox without executing, deleting, staging, or committing files.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import subprocess

QUEUE_NO_COMMAND = "NO_COMMAND"
QUEUE_EXACTLY_ONE_COMMAND = "EXACTLY_ONE_COMMAND"
QUEUE_MULTIPLE_COMMANDS = "MULTIPLE_COMMANDS"
QUEUE_ALREADY_EXECUTED_COMMAND = "ALREADY_EXECUTED_COMMAND"
QUEUE_DIRTY_INBOX = "DIRTY_INBOX"
QUEUE_MISSING_METADATA = "MISSING_COMMAND_METADATA"
QUEUE_INCOMPLETE_COMMAND = "INCOMPLETE_COMMAND"

COMMAND_DIR = Path(".agentic/commands")
INBOX_DIR = COMMAND_DIR / "inbox"
EXECUTED_JSONL = COMMAND_DIR / "executed.jsonl"

@dataclass(frozen=True)
class QueueCommandCandidate:
    command_id: str | None
    stem: str
    yaml_path: str
    script_path: str
    has_yaml: bool
    has_script: bool

@dataclass(frozen=True)
class QueueState:
    schema_version: int
    queue_state: str
    valid_for_agent_next: bool
    command_count: int
    candidates: tuple[QueueCommandCandidate, ...]
    dirty_paths: tuple[str, ...]
    reason: str
    next_allowed_actions: tuple[str, ...]

def _root(root: Path) -> Path:
    return root.resolve()

def _parse_simple_yaml(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    if not path.exists():
        return data
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        value = value.strip()
        if (value.startswith(chr(34)) and value.endswith(chr(34))) or (value.startswith(chr(39)) and value.endswith(chr(39))):
            value = value[1:-1]
        data[key.strip()] = value
    return data

def _executed_ids(root: Path) -> set[str]:
    path = _root(root) / EXECUTED_JSONL
    if not path.exists():
        return set()
    ids: set[str] = set()
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        try:
            item = json.loads(raw)
        except json.JSONDecodeError:
            continue
        command_id = item.get("command_id")
        if isinstance(command_id, str):
            ids.add(command_id)
    return ids

def _dirty_inbox_paths(root: Path) -> tuple[str, ...]:
    proc = subprocess.run(["git", "status", "--porcelain", ".agentic/commands/inbox"], cwd=_root(root), text=True, capture_output=True, check=False)
    if proc.returncode != 0:
        return ()
    paths: list[str] = []
    for raw in proc.stdout.splitlines():
        if raw.strip():
            paths.append(raw[3:])
    return tuple(paths)

def _candidates(root: Path) -> tuple[QueueCommandCandidate, ...]:
    inbox = _root(root) / INBOX_DIR
    if not inbox.exists():
        return ()
    stems = {path.stem for path in inbox.glob("*.yaml")} | {path.stem for path in inbox.glob("*.sh")}
    result: list[QueueCommandCandidate] = []
    for stem in sorted(stems):
        yaml_path = inbox / f"{stem}.yaml"
        script_path = inbox / f"{stem}.sh"
        data = _parse_simple_yaml(yaml_path)
        command_id = data.get("command_id") or None
        result.append(QueueCommandCandidate(command_id, stem, yaml_path.relative_to(_root(root)).as_posix(), script_path.relative_to(_root(root)).as_posix(), yaml_path.exists(), script_path.exists()))
    return tuple(result)

def inspect_queue_state(root: Path = Path(".")) -> QueueState:
    root = _root(root)
    dirty = _dirty_inbox_paths(root)
    candidates = _candidates(root)
    complete = tuple(item for item in candidates if item.has_yaml and item.has_script)
    incomplete = tuple(item for item in candidates if not (item.has_yaml and item.has_script))
    executed = _executed_ids(root)
    already = tuple(item for item in complete if item.command_id in executed)
    missing_meta = tuple(item for item in complete if not item.command_id)
    if dirty:
        state = QUEUE_DIRTY_INBOX
        reason = "command inbox has uncommitted changes"
    elif incomplete:
        state = QUEUE_INCOMPLETE_COMMAND
        reason = "command inbox contains unmatched yaml or shell file"
    elif not complete:
        state = QUEUE_NO_COMMAND
        reason = "no complete pending command pair"
    elif len(complete) > 1:
        state = QUEUE_MULTIPLE_COMMANDS
        reason = "multiple complete pending command pairs"
    elif missing_meta:
        state = QUEUE_MISSING_METADATA
        reason = "pending command is missing command_id metadata"
    elif already:
        state = QUEUE_ALREADY_EXECUTED_COMMAND
        reason = "pending command_id is already recorded as executed"
    else:
        state = QUEUE_EXACTLY_ONE_COMMAND
        reason = "exactly one complete pending command pair is ready"
    valid = state == QUEUE_EXACTLY_ONE_COMMAND
    next_actions = ("agent-next",) if valid else ("cockpit.actions",)
    return QueueState(1, state, valid, len(complete), candidates, dirty, reason, next_actions)

def queue_state_as_json_data(state: QueueState) -> dict[str, object]:
    return {
        "schema_version": state.schema_version,
        "queue_state": state.queue_state,
        "valid_for_agent_next": state.valid_for_agent_next,
        "command_count": state.command_count,
        "dirty_paths": list(state.dirty_paths),
        "reason": state.reason,
        "next_allowed_actions": list(state.next_allowed_actions),
        "candidates": [
            {
                "command_id": item.command_id,
                "stem": item.stem,
                "yaml_path": item.yaml_path,
                "script_path": item.script_path,
                "has_yaml": item.has_yaml,
                "has_script": item.has_script,
            }
            for item in state.candidates
        ],
    }
