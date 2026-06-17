from __future__ import annotations

from pathlib import Path


def test_legacy_ns_summary_smoke_route_is_removed() -> None:
    assert not Path("ns").exists()


def test_summary_renderer_usage_is_anchored_in_python_core() -> None:
    renderer = Path("src/agentic_project_kit/run_summary_renderer.py").read_text(
        encoding="utf-8",
    )
    tests = Path("tests/test_run_summary_renderer.py").read_text(encoding="utf-8")
    assert "validate_rendered_summary_text" in renderer
    assert "remote_evidence" in tests
    assert "CHAT_REPLY" in tests
