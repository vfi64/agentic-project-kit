from __future__ import annotations

from pathlib import Path

import yaml

AUTHORITY = "docs/planning/PROJECT_DIRECTION.yaml"
DIRECTION_DIRS = [Path("docs/plans"), Path("docs/roadmap"), Path("docs/strategy")]


def _direction_docs() -> list[Path]:
    docs: list[Path] = []
    for base in DIRECTION_DIRS:
        if base.exists():
            docs.extend(sorted(base.rglob("*.md")))
    return docs


def test_direction_duplicate_docs_are_marked_superseded() -> None:
    docs = _direction_docs()
    assert docs == []

    for path in docs:
        head = "\n".join(path.read_text(encoding="utf-8").splitlines()[:12])
        assert "Status: superseded" in head, path.as_posix()
        assert f"Authority: {AUTHORITY}" in head, path.as_posix()


def test_direction_duplicate_docs_registered_as_superseded_or_historical() -> None:
    registry = yaml.safe_load(Path("docs/DOCUMENTATION_REGISTRY.yaml").read_text(encoding="utf-8"))
    registered = {
        item["path"]: item
        for item in registry.get("documents", [])
        if isinstance(item, dict) and "path" in item
    }

    assert AUTHORITY in registered
    assert registered[AUTHORITY].get("status") == "active"

    for path in _direction_docs():
        rel = path.as_posix()
        assert rel in registered, rel
        entry = registered[rel]
        assert entry.get("status") == "superseded", rel
        assert entry.get("superseded_by") == AUTHORITY, rel
