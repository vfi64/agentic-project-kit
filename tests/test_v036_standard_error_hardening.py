from __future__ import annotations

from pathlib import Path


def test_legacy_ns_dev_forwarding_path_is_removed() -> None:
    assert not Path("ns").exists()


def test_standard_error_hardening_uses_python_and_agentic_kit_surfaces() -> None:
    reference = Path("docs/reference/AGENTIC_KIT_COMMANDS.md").read_text(encoding="utf-8")
    assert "agentic-kit" in reference
    assert "transfer" in reference
