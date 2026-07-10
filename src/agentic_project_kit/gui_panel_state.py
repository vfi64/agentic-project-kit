from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from agentic_project_kit.workspace import LEGACY_DEFAULTS, load_workspace

PANEL_STATE_FILE = "gui-panel-state.json"
PANEL_STATE_RELATIVE_PATH = Path(LEGACY_DEFAULTS.tmp_root) / PANEL_STATE_FILE


def panel_state_path(root: Path = Path(".")) -> Path:
    return load_workspace(root).gui_panel_state_path()


def _coerce_state(data: Any) -> dict[str, bool]:
    if isinstance(data, dict) and isinstance(data.get("expanded_groups"), dict):
        data = data["expanded_groups"]
    if not isinstance(data, dict):
        return {}
    return {str(key): bool(value) for key, value in data.items() if isinstance(key, str)}


def read_panel_state(root: Path = Path(".")) -> dict[str, bool]:
    path = panel_state_path(root)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        return {}
    return _coerce_state(data)


def write_panel_state(root: Path = Path("."), state: dict[str, bool] | None = None) -> Path:
    path = panel_state_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    workspace = load_workspace(root)
    payload = {
        "schema_version": 1,
        "kind": "gui_panel_state",
        "state_path": workspace.path_text(path),
        "updated_at_utc": datetime.now(timezone.utc).isoformat(),
        "expanded_groups": dict(sorted((state or {}).items())),
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path
