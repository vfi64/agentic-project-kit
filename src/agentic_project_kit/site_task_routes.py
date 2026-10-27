"""Website projection of the same authenticated routes used by command-for."""

from __future__ import annotations

from html import escape
import json

from .task_selection import manifest_route_errors


def task_navigation(manifest: dict) -> dict:
    if (
        isinstance(manifest, dict)
        and manifest.get("schema_version") == 2
        and "task_routes" not in manifest
    ):
        return {"schema_version": 1, "availability": "legacy_manifest", "routes": []}
    errors = manifest_route_errors(manifest)
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
    from .site_command_details import detail_filename

    phases = {"diagnostic": ("Inspect and understand", []),
              "planning": ("Review a plan", []), "guarded": ("Governed workflow steps", [])}
    for row in projection["routes"]:
        conditions = ", ".join(f"{k}={json.dumps(v)}" for k, v in row["when"].items())
        params = ", ".join(f"{k}: {v}" for k, v in row["inputs"].items()) or "none"
        search = escape(" ".join((row["task"].replace("_", " "), row["command"], row["review_note"])), quote=True)
        phases[row["phase"]][1].append(
            f'<article class="task-card" data-task-text="{search}"><h4>'
            + escape(row["task"].replace("_", " ").capitalize())
            + "</h4><p><code>"
            + escape(row["command"])
            + "</code> · "
            + escape(row["phase"])
            + " · "
            + escape(row["contract"]["safety"])
            + '</p><details><summary>Conditions and required inputs</summary><p>Requires: '
            + escape(conditions)
            + ". Inputs: "
            + escape(params)
            + ".</p></details><p>"
            + escape(row["review_note"])
            + f'</p><a href="{detail_filename(row["command"])}">Command details</a></article>'
        )
    groups = "".join(f'<section data-task-phase="{phase}" aria-labelledby="phase-{phase}"><h3 id="phase-{phase}">{label}</h3>'
                     f'<div class="task-grid">{"".join(rows)}</div></section>'
                     for phase, (label, rows) in phases.items() if rows)
    return (
        '<section class="task-routes" aria-label="Task routes"><h2>Start from your task</h2>'
        "<p>Generated from the same manifest as command-for intent selection. "
        "These are conditional routes, not an observation of your repository or execution permission. "
        "Unknown facts stop selection; existing command gates remain in force. Intent-mode availability describes this source tree, not an assertion about previously published wheels.</p>"
        + '<label for="task-search">Find a task</label> <input id="task-search" type="search" aria-controls="task-cards" placeholder="Check, finish work, handoff…" disabled>'
        + '<p id="task-filter-status" role="status" aria-live="polite"></p><div id="task-cards">' + groups + '</div>'
        + f"<p>{len(projection.get('unassigned_commands', []))} commands are unassigned in this bounded task matrix; "
        '<a href="index.html">complete catalog</a> and <a href="diagnostics.html">diagnostics</a> remain accessible.</p>'
        '<details><summary>Unassigned commands</summary><ul>'
        + ''.join(f'<li><code>{escape(name)}</code></li>' for name in projection.get('unassigned_commands', []))
        + '</ul></details></section>'
    )
