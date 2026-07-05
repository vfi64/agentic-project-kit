from __future__ import annotations

from pathlib import Path

import yaml

PROJECT_DIRECTION = "docs/planning/PROJECT_DIRECTION.yaml"


def _registry() -> dict[str, dict[str, object]]:
    data = yaml.safe_load(Path("docs/DOCUMENTATION_REGISTRY.yaml").read_text(encoding="utf-8"))
    return {
        item["path"]: item
        for item in data.get("documents", [])
        if isinstance(item, dict) and "path" in item
    }


def test_project_direction_is_only_active_direction_source() -> None:
    registry = _registry()

    assert registry[PROJECT_DIRECTION]["status"] == "active"

    for path, item in registry.items():
        if path == PROJECT_DIRECTION:
            continue
        if path.startswith(("docs/plans/", "docs/roadmap/", "docs/strategy/")):
            assert item.get("status") == "superseded", path
            assert item.get("superseded_by") == PROJECT_DIRECTION, path


def test_legacy_ns_planning_docs_are_not_active_direction_sources() -> None:
    registry = _registry()
    legacy_ns_entries = [
        (path, entry)
        for path, entry in registry.items()
        if path.startswith("docs/planning/")
        and (
            "/NS_" in path
            or "NO_COPY_NS_WORKFLOW_CONTROL" in path
        )
    ]

    assert legacy_ns_entries
    for path, entry in legacy_ns_entries:
        assert entry["status"] == "superseded", path


def test_workflow_docs_remain_operational_not_project_direction() -> None:
    registry = _registry()
    workflow_docs = sorted(Path("docs/workflow").rglob("*.md"))

    assert workflow_docs, "expected workflow runbooks"

    for path in workflow_docs:
        rel = path.as_posix()
        assert rel in registry, rel
        assert registry[rel]["class"] == "operational/automation", rel
        assert registry[rel]["status"] == "active", rel


def test_delete_candidates_are_not_active_handoff_authority() -> None:
    registry = _registry()

    for path, entry in registry.items():
        if path.startswith("docs/handoff/") and entry.get("status") == "delete_candidate":
            assert entry["class"] == "historical archive"
            assert path != "docs/handoff/CURRENT_HANDOFF.md"
