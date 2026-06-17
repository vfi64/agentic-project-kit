from __future__ import annotations

from pathlib import Path


def test_legacy_ns_typed_work_order_shortcut_is_removed() -> None:
    assert not Path("ns").exists()


def test_typed_work_order_contract_uses_agentic_kit_transfer_surface() -> None:
    reference = Path("docs/reference/AGENTIC_KIT_COMMANDS.md").read_text(encoding="utf-8")
    assert "agentic-kit transfer" in reference
    assert "work-order" in reference or "work-order-patch" in reference
