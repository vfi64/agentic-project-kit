from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_next_step_uses_python_workflow_runner_not_legacy_shell_cycle() -> None:
    text = Path("tools/next-step.py").read_text(encoding="utf-8")
    assert "local_workflow_cycle.sh" not in text
    assert "workflow_runner.py" in text


def test_capture_workflow_output_python_helper_captures_stdin(tmp_path: Path) -> None:
    output = tmp_path / "captured.txt"
    proc = subprocess.run(
        [sys.executable, "tools/capture_workflow_output.py", str(output)],
        input=b"hello\nworkflow\n",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert proc.returncode == 0
    assert proc.stdout == b"hello\nworkflow\n"
    assert output.read_bytes() == b"hello\nworkflow\n"


def test_active_workflow_route_does_not_require_local_workflow_cycle_shell() -> None:
    active_route_files = [
        Path("tools/next-step.py"),
        Path("tools/workflow_runner.py"),
        Path("tools/NEXT_TRANSFER_TASK.py"),
    ]
    active_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in active_route_files
        if path.exists()
    )
    assert "tools/local_workflow_cycle.sh" not in active_text
    assert "./tools/local_workflow_cycle.sh" not in active_text
    assert "local_workflow_cycle.sh" not in active_text
    assert "tools/workflow_runner.py" in Path("tools/next-step.py").read_text(
        encoding="utf-8",
        errors="ignore",
    )


def test_legacy_workflow_shell_helpers_are_removed_in_closeout_slice() -> None:
    assert not Path("tools/local_workflow_cycle.sh").exists()
    assert not Path("tools/capture_workflow_output.sh").exists()
