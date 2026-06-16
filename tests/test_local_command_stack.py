from __future__ import annotations

from pathlib import Path

from agentic_project_kit.local_command_stack import begin_local_command_stack
from agentic_project_kit.local_command_stack import current_or_begin_local_command_stack
from agentic_project_kit.local_command_stack import current_or_begin_local_command_stack_id
from agentic_project_kit.local_command_stack import end_local_command_stack
from agentic_project_kit.local_command_stack import read_local_command_stack


def test_command_stack_begin_reuse_and_end(tmp_path: Path) -> None:
    first = begin_local_command_stack(tmp_path)
    assert first["active"] is True
    assert str(first["command_stack_id"]).startswith("local-")

    reused = current_or_begin_local_command_stack(tmp_path)
    assert reused["command_stack_id"] == first["command_stack_id"]
    assert reused["reason"] == "active_reused"

    ended = end_local_command_stack(tmp_path)
    assert ended["active"] is False

    second = current_or_begin_local_command_stack(tmp_path)
    assert second["active"] is True
    assert second["command_stack_id"] != first["command_stack_id"]


def test_current_or_begin_command_stack_id_is_repo_local(tmp_path: Path) -> None:
    stack_id = current_or_begin_local_command_stack_id(tmp_path)
    state = read_local_command_stack(tmp_path)

    assert stack_id == state["command_stack_id"]
    assert (tmp_path / "tmp" / "local-command-stack-state.json").exists()
