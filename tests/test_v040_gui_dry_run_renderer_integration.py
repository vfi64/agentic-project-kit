from __future__ import annotations

import subprocess
from pathlib import Path


def test_gui_dry_run_preserves_renderer_contract_without_ns() -> None:
    assert not Path("ns").exists()
    result = subprocess.run(
        ["./.venv/bin/python", "-m", "agentic_project_kit.gui_dry_run"],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode in {0, 1}
    output = result.stdout + result.stderr
    assert "GUI DRY RUN" in output
    assert "presenter_preview_begin" in output
    assert "presenter_preview_end" in output
