from __future__ import annotations

from pathlib import Path

import yaml

PROJECT_DIRECTION = "docs/planning/project_direction.yaml"


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
    legacy_paths = [
        "docs/planning/NS_COMMAND_MIGRATION_CLASSIFICATION.md",
        "docs/planning/NS_RELEASE_SHORTCUTS.md",
        "docs/planning/NS_UP_PR_COMPLETION.md",
        "docs/planning/NO_COPY_NS_WORKFLOW_CONTROL.md",
    ]

    for path in legacy_paths:
        if Path(path).exists():
            assert registry[path]["status"] == "superseded", path


def test_workflow_docs_remain_operational_not_project_direction() -> None:
    registry = _registry()
    workflow_docs = sorted(Path("docs/workflow").rglob("*.md"))

    assert workflow_docs, "expected workflow runbooks"

    for path in workflow_docs:
        rel = path.as_posix()
        assert rel in registry, rel
        assert registry[rel]["class"] == "operational/automation", rel
        assert registry[rel]["status"] == "active", rel


def test_old_handoff_overlay_is_delete_candidate_not_active_handoff() -> None:
    path = "docs/handoff/CURRENT_HANDOFF_OVERLAY_AFTER_PR660.md"
    if Path(path).exists():
        entry = _registry()[path]
        assert entry["status"] == "delete_candidate"
        assert entry["class"] == "historical archive"
