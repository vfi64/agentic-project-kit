from __future__ import annotations

from pathlib import Path


def test_legacy_ns_slice_runner_route_is_removed() -> None:
    assert not Path("ns").exists()


def test_entrypoint_slice_runner_uses_neutral_python_module() -> None:
    text = Path("src/agentic_project_kit/entrypoint_slice_runner.py").read_text(
        encoding="utf-8",
    )
    assert "Stopping slice runner at retryable state" in text
    assert "Stopping slice runner at first failing step" in text
    assert "### RESULT: FAIL ###" in text
    assert "### RESULT: PENDING ###" in text
