from __future__ import annotations

from pathlib import Path


def test_v037_zero_direct_ns_shell_adapter_state_is_now_no_ns() -> None:
    assert not Path("ns").exists()
    assert not Path("ns-menu").exists()


def test_gui_preparation_uses_python_dry_run_surface() -> None:
    assert Path("src/agentic_project_kit/gui_dry_run.py").exists()
