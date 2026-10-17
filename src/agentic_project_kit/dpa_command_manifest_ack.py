"""Synchronize the manifest identity without changing DPA authorization evidence."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from agentic_project_kit.command_manifest import load_manifest
from agentic_project_kit.dpa_readiness import DEFAULT_READINESS_PATH
from agentic_project_kit.instruction_lint import command_manifest_ack_line


def refresh_dpa_readiness_command_manifest_ack(
    project_root: Path | str = ".",
    *,
    dry_run: bool = False,
    manifest: dict[str, Any] | None = None,
) -> dict[str, object]:
    root = Path(project_root).resolve()
    path = root / DEFAULT_READINESS_PATH
    relative = DEFAULT_READINESS_PATH.as_posix()
    if not path.exists():
        return {
            "ok": True, "status": "SKIPPED", "reason": "readiness-record-missing",
            "path": relative, "changed": False, "changed_paths": [], "dry_run": dry_run,
        }
    data = json.loads(path.read_text(encoding="utf-8"))
    expected_ack = command_manifest_ack_line(load_manifest(root) if manifest is None else manifest)
    old_ack = data.get("command_manifest_ack")
    if old_ack == expected_ack:
        return {
            "ok": True, "status": "CURRENT", "path": relative, "changed": False,
            "changed_paths": [], "command_manifest_ack": expected_ack, "dry_run": dry_run,
        }
    data["command_manifest_ack"] = expected_ack
    if not dry_run:
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return {
        "ok": True, "status": "UPDATED", "path": relative, "changed": True,
        "changed_paths": [relative], "old_command_manifest_ack": old_ack,
        "command_manifest_ack": expected_ack, "dry_run": dry_run,
    }
