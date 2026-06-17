from __future__ import annotations

from pathlib import Path


def test_legacy_ns_summary_route_is_removed() -> None:
    assert not Path("ns").exists()


def test_summary_and_ack_audit_uses_renderer_core() -> None:
    renderer = Path("src/agentic_project_kit/run_summary_renderer.py").read_text(
        encoding="utf-8",
    )
    assert "validate_rendered_summary_text" in renderer
    assert "terminal_log_remote" in renderer
