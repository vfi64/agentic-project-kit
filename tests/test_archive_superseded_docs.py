from __future__ import annotations

from pathlib import Path

import yaml

ARCHIVED = {
    "docs/archive/planning/RULE_REGISTRY_IMPLEMENTATION_PLAN.yaml": "docs/planning/RULE_REGISTRY_IMPLEMENTATION_PLAN.yaml",
    "docs/archive/planning/roadmap/V0.4.0_PORTABLE_LLM_COMMUNICATION_BOOTSTRAP_ROADMAP.md": "docs/roadmap/V0.4.0_PORTABLE_LLM_COMMUNICATION_BOOTSTRAP_ROADMAP.md",
}


def _registry() -> dict[str, dict[str, object]]:
    data = yaml.safe_load(Path("docs/DOCUMENTATION_REGISTRY.yaml").read_text(encoding="utf-8"))
    return {
        item["path"]: item
        for item in data.get("documents", [])
        if isinstance(item, dict) and "path" in item
    }


def test_safe_direct_archive_sources_moved() -> None:
    for archived, original in ARCHIVED.items():
        assert Path(archived).exists(), archived
        assert not Path(original).exists(), original


def test_safe_direct_archive_registry_paths_updated() -> None:
    registry = _registry()

    for archived, original in ARCHIVED.items():
        assert archived in registry, archived
        assert original not in registry, original
        assert registry[archived].get("status") == "superseded", archived
        assert registry[archived].get("archived_from") == original, archived


def test_active_workflow_docs_not_archived_by_safe_direct_slice() -> None:
    registry = _registry()
    workflow_docs = sorted(Path("docs/workflow").rglob("*.md"))
    assert workflow_docs

    for path in workflow_docs:
        rel = path.as_posix()
        assert rel in registry, rel
        assert registry[rel].get("status") == "active", rel
        assert registry[rel].get("class") == "operational/automation", rel
