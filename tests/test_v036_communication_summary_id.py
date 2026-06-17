from __future__ import annotations

from pathlib import Path


def test_legacy_ns_summary_shortcut_is_removed() -> None:
    assert not Path("ns").exists()


def test_summary_renderer_core_remains_canonical() -> None:
    text = Path("src/agentic_project_kit/run_summary_renderer.py").read_text(
        encoding="utf-8",
    )
    assert "validate_rendered_summary_text" in text
    assert "terminal_log_remote" in text
