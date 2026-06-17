from __future__ import annotations

from pathlib import Path


def test_legacy_ns_evidence_guard_shortcut_is_removed() -> None:
    assert not Path("ns").exists()


def test_evidence_guard_remains_available_in_python_or_transfer_surface() -> None:
    candidates = [
        Path("src/agentic_project_kit/evidence_inspector.py"),
        Path("src/agentic_project_kit/cli_commands/evidence.py"),
        Path("src/agentic_project_kit/cli_commands/transfer.py"),
    ]
    existing = [path for path in candidates if path.exists()]
    assert existing
    text = "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in existing)
    assert "evidence" in text.lower()
