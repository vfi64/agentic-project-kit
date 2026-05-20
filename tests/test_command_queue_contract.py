from __future__ import annotations

import json
import subprocess
from pathlib import Path

from agentic_project_kit.command_queue_contract import (
    QUEUE_ALREADY_EXECUTED_COMMAND,
    QUEUE_DIRTY_INBOX,
    QUEUE_EXACTLY_ONE_COMMAND,
    QUEUE_INCOMPLETE_COMMAND,
    QUEUE_MISSING_METADATA,
    QUEUE_MULTIPLE_COMMANDS,
    QUEUE_NO_COMMAND,
    inspect_queue_state,
    queue_state_as_json_data,
)

def _init_repo(root: Path) -> None:
    subprocess.run(["git", "init"], cwd=root, check=True, stdout=subprocess.DEVNULL)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=root, check=True)
    (root / ".gitignore").write_text("", encoding="utf-8")
    subprocess.run(["git", "add", ".gitignore"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=root, check=True, stdout=subprocess.DEVNULL)

def _write_pair(root: Path, stem: str, command_id: str | None = None, script: bool = True) -> None:
    inbox = root / ".agentic" / "commands" / "inbox"
    inbox.mkdir(parents=True, exist_ok=True)
    lines = ["title: Test", "safety_class: read-only"]
    if command_id is not None:
        lines.insert(0, f"command_id: {command_id}")
    (inbox / f"{stem}.yaml").write_text("\n".join(lines) + "\n", encoding="utf-8")
    if script:
        (inbox / f"{stem}.sh").write_text("printf test\n", encoding="utf-8")

def test_queue_state_no_command(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    state = inspect_queue_state(tmp_path)
    assert state.queue_state == QUEUE_NO_COMMAND
    assert state.valid_for_agent_next is False
    assert state.command_count == 0

def test_queue_state_exactly_one_command(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    _write_pair(tmp_path, "one", "cmd-one")
    subprocess.run(["git", "add", ".agentic/commands/inbox"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-m", "queue"], cwd=tmp_path, check=True, stdout=subprocess.DEVNULL)
    state = inspect_queue_state(tmp_path)
    assert state.queue_state == QUEUE_EXACTLY_ONE_COMMAND
    assert state.valid_for_agent_next is True
    assert state.next_allowed_actions == ("agent-next",)
    data = queue_state_as_json_data(state)
    assert data["schema_version"] == 1
    assert data["queue_state"] == QUEUE_EXACTLY_ONE_COMMAND
    assert data["candidates"][0]["command_id"] == "cmd-one"

def test_queue_state_multiple_commands(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    _write_pair(tmp_path, "one", "cmd-one")
    _write_pair(tmp_path, "two", "cmd-two")
    subprocess.run(["git", "add", ".agentic/commands/inbox"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-m", "queue"], cwd=tmp_path, check=True, stdout=subprocess.DEVNULL)
    state = inspect_queue_state(tmp_path)
    assert state.queue_state == QUEUE_MULTIPLE_COMMANDS
    assert state.command_count == 2

def test_queue_state_already_executed_command(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    _write_pair(tmp_path, "one", "cmd-one")
    executed = tmp_path / ".agentic" / "commands" / "executed.jsonl"
    executed.parent.mkdir(parents=True, exist_ok=True)
    executed.write_text(json.dumps({"command_id": "cmd-one"}) + "\n", encoding="utf-8")
    subprocess.run(["git", "add", ".agentic/commands"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-m", "queue"], cwd=tmp_path, check=True, stdout=subprocess.DEVNULL)
    state = inspect_queue_state(tmp_path)
    assert state.queue_state == QUEUE_ALREADY_EXECUTED_COMMAND
    assert state.valid_for_agent_next is False

def test_queue_state_dirty_inbox(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    _write_pair(tmp_path, "one", "cmd-one")
    state = inspect_queue_state(tmp_path)
    assert state.queue_state == QUEUE_DIRTY_INBOX
    assert state.dirty_paths

def test_queue_state_missing_metadata(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    _write_pair(tmp_path, "one", None)
    subprocess.run(["git", "add", ".agentic/commands/inbox"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-m", "queue"], cwd=tmp_path, check=True, stdout=subprocess.DEVNULL)
    state = inspect_queue_state(tmp_path)
    assert state.queue_state == QUEUE_MISSING_METADATA

def test_queue_state_incomplete_command(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    _write_pair(tmp_path, "one", "cmd-one", script=False)
    subprocess.run(["git", "add", ".agentic/commands/inbox"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-m", "queue"], cwd=tmp_path, check=True, stdout=subprocess.DEVNULL)
    state = inspect_queue_state(tmp_path)
    assert state.queue_state == QUEUE_INCOMPLETE_COMMAND
