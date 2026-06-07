from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_agentic_kit_command_reference_is_current() -> None:
    subprocess.run(
        [sys.executable, "scripts/generate_agentic_kit_command_reference.py"],
        check=True,
    )
    assert Path("docs/reference/agentic-kit-commands.json").exists()
    assert Path("docs/reference/AGENTIC_KIT_COMMANDS.md").exists()

    data = json.loads(Path("docs/reference/agentic-kit-commands.json").read_text(encoding="utf-8"))
    names = {(item["group"], item["name"]) for item in data["commands"]}
    assert ("transfer", "pr-complete") in names
    assert ("transfer", "pr-wait-ci") in names
    assert ("transfer", "pr-merge-safe") in names
    assert ("transfer", "post-merge-complete") in names

    markdown = Path("docs/reference/AGENTIC_KIT_COMMANDS.md").read_text(encoding="utf-8")
    assert "agentic-kit transfer pr-complete" in markdown
    assert "agentic-kit transfer post-merge-complete" in markdown
