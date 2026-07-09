from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

DOC = Path("docs/archive/V0.3.36_SHELL_ADAPTER_INVENTORY_BASELINE.md")


def git_ls_files(pattern: str) -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", pattern],
        text=True,
        capture_output=True,
        check=True,
    )
    return sorted(line.strip() for line in result.stdout.splitlines() if line.strip())


def baseline_payload() -> dict:
    text = DOC.read_text(encoding="utf-8")
    match = re.search(r"```json\n(.*?)\n```", text, re.S)
    assert match, "baseline must include machine-readable JSON block"
    return json.loads(match.group(1))


def test_shell_adapter_inventory_is_empty_after_ns_removal() -> None:
    payload = baseline_payload()
    shell_files = git_ls_files("tools/ns_*.sh")

    assert not Path("ns").exists()
    assert not Path("ns-menu").exists()
    assert shell_files == []

    assert payload["tracked_shell_adapters"] == []
    assert payload["direct_ns_shell_references"] == []
    assert payload["python_routes"] == []
    assert payload["tracked_shell_adapter_count"] == 0
    assert payload["direct_ns_shell_reference_count"] == 0
    assert payload["python_route_count"] == 0


def test_shell_adapter_inventory_documents_superseded_scope() -> None:
    text = DOC.read_text(encoding="utf-8")
    assert "Status: superseded" in text
    assert "legacy ns entrypoint removed" in text
