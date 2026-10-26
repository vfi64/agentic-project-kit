"""Website projection of the same authenticated routes used by command-for."""

from __future__ import annotations

from html import escape
import json

from .command_manifest import manifest_identity
from .task_selection import validate_routes


def task_navigation(manifest: dict) -> dict:
    if manifest.get("schema_version") == 2 and "task_routes" not in manifest:
        return {"schema_version": 1, "availability": "legacy_manifest", "routes": []}
    if (
        manifest.get("schema_version") != 3
        or manifest.get("meta", {}).get("schema_version") != 2
        or manifest.get("meta", {}).get("manifest_sha") != manifest_identity(manifest)
    ):
        raise ValueError("task navigation manifest schema or identity mismatch")
    errors = validate_routes(manifest.get("task_routes"), manifest)
    if errors:
        raise ValueError("; ".join(errors))
    commands = {c["qualified_name"]: c for c in manifest["commands"]}
    return {
        "schema_version": 1,
        "manifest_sha": manifest["meta"]["manifest_sha"],
        "execution_authorized": False,
        "unassigned_commands": sorted(
            set(commands) - {r["command"] for r in manifest["task_routes"]["routes"]}
        ),
        "facts_schema": manifest["task_routes"]["facts_schema"],
        "routes": [
            {
                **r,
                "contract": {
                    k: commands[r["command"]][k]
                    for k in ("safety", "surface", "remote_effects", "dry_run_available")
                },
            }
            for r in manifest["task_routes"]["routes"]
        ],
    }


def render_task_navigation(projection: dict) -> str:
    rows = []
    for row in projection["routes"]:
        conditions = ", ".join(f"{k}={json.dumps(v)}" for k, v in row["when"].items())
        params = ", ".join(f"{k}: {v}" for k, v in row["inputs"].items()) or "none"
        rows.append(
            "<article><h3>"
            + escape(row["task"].replace("_", " "))
            + "</h3><p><code>"
            + escape(row["command"])
            + "</code> · "
            + escape(row["phase"])
            + " · "
            + escape(row["contract"]["safety"])
            + "</p><p>Requires: "
            + escape(conditions)
            + ". Inputs: "
            + escape(params)
            + ".</p><p>"
            + escape(row["review_note"])
            + "</p></article>"
        )
    return (
        '<section class="task-routes" aria-label="Task routes"><h2>Start from your task</h2>'
        "<p>Generated from the same manifest as command-for intent selection. "
        "These are conditional routes, not an observation of your repository or execution permission. "
        "Unknown facts stop selection; existing command gates remain in force.</p>"
        + "".join(rows)
        + f"<p>{len(projection.get('unassigned_commands', []))} commands are unassigned in this bounded task matrix; "
        '<a href="index.html">complete catalog</a> and <a href="diagnostics.html">diagnostics</a> remain accessible.</p></section>'
    )
