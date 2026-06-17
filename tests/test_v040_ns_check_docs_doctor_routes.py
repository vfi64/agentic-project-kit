from __future__ import annotations

import subprocess
from pathlib import Path


def test_legacy_ns_check_docs_doctor_routes_are_removed() -> None:
    assert not Path("ns").exists()


def test_check_docs_and_doctor_are_available_as_agentic_kit_commands() -> None:
    for args in (
        ["./.venv/bin/agentic-kit", "check-docs", "--help"],
        ["./.venv/bin/agentic-kit", "doctor", "--help"],
    ):
        result = subprocess.run(args, text=True, capture_output=True, check=False)
        assert result.returncode == 0
