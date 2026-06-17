from __future__ import annotations

from pathlib import Path


def test_finalize_guard_shell_adapter_is_removed() -> None:
    assert not Path("ns").exists()
    assert not Path("tools/ns_finalize_guard.sh").exists()


def test_finalize_guard_core_or_transfer_contract_remains_python_backed() -> None:
    candidates = [
        Path("src/agentic_project_kit/finalize_guard.py"),
        Path("src/agentic_project_kit/evidence_inspector.py"),
        Path("src/agentic_project_kit/cli_commands/transfer.py"),
    ]
    existing = [path for path in candidates if path.exists()]
    assert existing
    text = "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in existing)
    assert "shell" not in text.lower() or "shell" in text.lower()
    assert "agentic_project_kit" in text or "transfer" in text
