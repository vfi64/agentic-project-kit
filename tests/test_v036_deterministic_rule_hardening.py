from __future__ import annotations

import subprocess
from pathlib import Path


def test_legacy_ns_direct_shell_adapter_routes_are_removed() -> None:
    assert not Path("ns").exists()
    assert subprocess.check_output(["git", "ls-files", "*.sh"], text=True).strip() == ""


def test_rule_registry_remains_deterministic_without_ns() -> None:
    inventory = Path(".agentic/rule_mechanism_inventory.yaml").read_text(encoding="utf-8")
    assert "./ns" not in inventory
    assert "agentic-kit-cli" in inventory or "agentic-kit" in inventory
