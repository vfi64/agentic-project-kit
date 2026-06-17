from __future__ import annotations

from pathlib import Path


def test_legacy_ns_typed_next_shortcut_is_removed() -> None:
    assert not Path("ns").exists()


def test_typed_next_queue_execution_is_available_through_python_tools() -> None:
    assert Path("tools/next-step.py").exists()
    assert Path("tools/workflow_runner.py").exists()
    next_step = Path("tools/next-step.py").read_text(encoding="utf-8")
    assert "workflow_runner.py" in next_step
    assert "local_workflow_cycle.sh" not in next_step
