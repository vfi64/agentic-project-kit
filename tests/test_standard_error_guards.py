from __future__ import annotations

from pathlib import Path


def test_legacy_ns_standard_recovery_shortcuts_are_removed() -> None:
    assert not Path("ns").exists()


def test_standard_recovery_surfaces_are_available_through_agentic_kit() -> None:
    reference = Path("docs/reference/AGENTIC_KIT_COMMANDS.md").read_text(encoding="utf-8")
    for term in [
        "agentic-kit transfer repo-status",
        "agentic-kit transfer post-merge-check",
        "agentic-kit transfer protected-diff-plan",
    ]:
        assert term in reference
