from pathlib import Path

import yaml


REGISTRY = Path("docs/DOCUMENTATION_REGISTRY.yaml")
OLD_ROADMAP = "docs/strategy/V0.4.0_GUI_MVP_ROADMAP.md"
PROJECT_DIRECTION = Path("docs/planning/PROJECT_DIRECTION.yaml")


def _registry() -> dict[str, dict[str, object]]:
    data = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))
    return {
        item["path"]: item
        for item in data.get("documents", [])
        if isinstance(item, dict) and "path" in item
    }


def test_v040_gui_mvp_roadmap_is_no_longer_active_authority() -> None:
    registry = _registry()
    assert OLD_ROADMAP in registry
    assert registry[OLD_ROADMAP]["status"] == "superseded"
    assert registry[OLD_ROADMAP]["superseded_by"] == "docs/planning/PROJECT_DIRECTION.yaml"


def test_project_direction_exists_as_active_direction_authority() -> None:
    assert PROJECT_DIRECTION.exists()
    text = PROJECT_DIRECTION.read_text(encoding="utf-8")
    assert "v0.5.0" in text or "gui" in text.lower()
