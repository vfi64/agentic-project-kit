from __future__ import annotations

import subprocess
from pathlib import Path


def test_no_tracked_tool_shell_scripts_remain() -> None:
    files = subprocess.check_output(["git", "ls-files"], text=True).splitlines()
    tool_shell_files = [path for path in files if path.startswith("tools/") and path.endswith(".sh")]
    assert tool_shell_files == []


def test_supported_portable_replacements_exist() -> None:
    assert Path("tools/capture_workflow_output.py").exists()
    assert Path("tools/screen_control_gate.py").exists()
    assert Path("tools/workflow_runner.py").exists()


def test_legacy_ns_is_the_only_remaining_tracked_shell_entrypoint_for_now() -> None:
    files = subprocess.check_output(["git", "ls-files"], text=True).splitlines()
    shell_named = [path for path in files if path.endswith(".sh")]
    assert shell_named == []
    assert Path("ns").exists()
