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


def test_legacy_ns_release_metadata_tool_is_removed() -> None:
    assert not Path("tools/ns_release_metadata_prep.py").exists()


def test_no_active_legacy_ns_release_metadata_prep_references() -> None:
    checked_roots = [Path("src"), Path("tools"), Path("docs/planning")]
    offenders: list[str] = []
    for root in checked_roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if path.is_file() and path.suffix in {".py", ".md", ".txt", ".yaml", ".json"}:
                text = path.read_text(encoding="utf-8")
                if "tools/ns_release_metadata_prep.py" in text or "ns_release_metadata_prep.py" in text:
                    offenders.append(path.as_posix())
    assert offenders == []
