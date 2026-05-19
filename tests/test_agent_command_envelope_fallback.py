from pathlib import Path

from agentic_project_kit.agent_command_runner import normalize_safety_class
from agentic_project_kit.command_inbox_check import check_command_inbox


def test_local_verification_is_normalized_to_local_only() -> None:
    assert normalize_safety_class("local-verification") == "local-only"


def test_inbox_check_accepts_local_verification_alias(tmp_path: Path) -> None:
    inbox = tmp_path / ".agentic" / "commands" / "inbox"
    inbox.mkdir(parents=True)
    (inbox / "cmd.sh").write_text("#!/usr/bin/env sh\nprintf 'ok\n'\n", encoding="utf-8")
    (inbox / "cmd.yaml").write_text(
        "command_id: cmd\ntitle: Local verification\nsafety_class: local-verification\n",
        encoding="utf-8",
    )
    assert check_command_inbox(inbox).ok
