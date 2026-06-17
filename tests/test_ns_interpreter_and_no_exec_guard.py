from __future__ import annotations

from pathlib import Path


def test_legacy_ns_entrypoint_is_removed() -> None:
    assert not Path("ns").exists()


def test_agentic_kit_entrypoint_replaces_ns_interpreter_discovery() -> None:
    command_reference = Path("docs/reference/AGENTIC_KIT_COMMANDS.md").read_text(
        encoding="utf-8",
    )
    assert "agentic-kit" in command_reference
    assert "agentic-kit transfer" in command_reference


def test_no_shell_script_entrypoint_exec_dispatches_remain() -> None:
    assert not Path("ns").exists()
    assert not Path("ns-menu").exists()
    assert not list(Path(".").glob("*.sh"))
