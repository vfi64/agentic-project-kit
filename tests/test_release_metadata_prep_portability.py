from __future__ import annotations

import importlib
from pathlib import Path


def test_neutral_release_metadata_prep_module_exists() -> None:
    module = importlib.import_module("agentic_project_kit.release_metadata_prep")
    assert hasattr(module, "main")


def test_release_prep_core_no_longer_references_ns_tool_script() -> None:
    text = Path("src/agentic_project_kit/release_prep_core.py").read_text(encoding="utf-8")
    assert "tools/ns_release_metadata_prep.py" not in text
    assert "ns_release_metadata_prep.py" not in text


def test_legacy_ns_release_metadata_tool_is_thin_wrapper() -> None:
    text = Path("tools/ns_release_metadata_prep.py").read_text(encoding="utf-8")
    assert "agentic_project_kit.release_metadata_prep" in text
    assert "Backward-compatible wrapper" in text
