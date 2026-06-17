from __future__ import annotations

from pathlib import Path


def test_legacy_ns_dev_gate_route_is_removed() -> None:
    assert not Path("ns").exists()


def test_local_feature_gate_python_core_remains_available() -> None:
    candidates = [
        Path("src/agentic_project_kit/dev_local_feature_gate.py"),
        Path("src/agentic_project_kit/local_feature_gate.py"),
        Path("src/agentic_project_kit/cli_commands/dev.py"),
    ]
    existing = [path for path in candidates if path.exists()]
    assert existing
    text = "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in existing)
    assert "feature" in text.lower()
    assert "gate" in text.lower()
