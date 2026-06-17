from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_legacy_ns_check_docs_doctor_routes_are_removed() -> None:
    assert not Path("ns").exists()


def test_check_docs_and_doctor_are_available_as_agentic_kit_commands() -> None:
    for args in (
        [sys.executable, "-m", "agentic_project_kit.cli", "check-docs", "--help"],
        [sys.executable, "-m", "agentic_project_kit.cli", "doctor", "--help"],
    ):
        result = subprocess.run(args, text=True, capture_output=True, check=False)
        assert result.returncode == 0
