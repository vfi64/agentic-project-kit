"""Bounded command pages from task routes and the existing tested quickstart."""
from __future__ import annotations

from html import escape
import json
from pathlib import Path
import re
from string import Template

from .site_task_routes import task_navigation
from .site_public_contract import projection_provenance


def detail_filename(command: str) -> str:
    if not re.fullmatch(r"agentic-kit(?: [a-z0-9][a-z0-9-]*)+", command):
        raise ValueError("invalid command identity for detail page")
    return "detail-" + command.removeprefix("agentic-kit ").replace(" ", "-") + ".html"


def collect_command_details(manifest: dict, quickstart: dict) -> dict:
    navigation = task_navigation(manifest)
    entries = {c["qualified_name"]: c for c in manifest["commands"]}
    quick = {c["qualified_name"] for f in quickstart["flows"] for c in f["commands"]}
    selected = quick | {r["command"] for r in navigation["routes"]}
    if not selected <= entries.keys():
        raise ValueError("quickstart detail command is absent from manifest")
    rows = []
    for name in sorted(selected):
        entry = entries[name]
        rows.append({
            "command": name, "file": detail_filename(name),
            "selection_sources": [*( ["tested_quickstart"] if name in quick else []),
                                  *( ["task_routes"] if any(r["command"] == name for r in navigation["routes"]) else [])],
            "description": entry.get("when_to_use") or entry.get("help") or "Inspect the command contract and local help.",
            "help": entry.get("help", ""), "params": entry["params"],
            "contract": {k: entry[k] for k in ("safety", "surface", "remote_effects", "dry_run_available")},
            "routes": [r for r in navigation["routes"] if r["command"] == name],
            "help_example": [*name.split(), "--help"],
        })
    if len({r["file"] for r in rows}) != len(rows):
        raise ValueError("command detail filenames collide")
    return {"schema_version": 1, "kind": "command_detail_projection",
            "manifest_sha": manifest["meta"]["manifest_sha"], "execution_authorized": False,
            "commands": rows}


def render_command_detail(root: Path, row: dict, *, product_name: str, version: str, manifest_sha: str, build_commit: str = "") -> str:
    contracts = "".join(f'<dt>{escape(k.replace("_", " "))}</dt><dd>{escape(json.dumps(v))}</dd>'
                        for k, v in row["contract"].items())
    routes = []
    for route in row["routes"]:
        conditions = ", ".join(f'{k.replace("_", " ")} = {json.dumps(v)}' for k, v in route["when"].items())
        inputs = ", ".join(f'{k}: {v}' for k, v in route["inputs"].items()) or "none"
        routes.append(f'<article class="panel"><h3>{escape(route["task"].replace("_", " ").capitalize())}</h3>'
                      f'<p>Phase: {escape(route["phase"])}. Required state: {escape(conditions)}.</p>'
                      f'<p>Required task inputs: {escape(inputs)}.</p><p>{escape(route["review_note"])}</p></article>')
    params = []
    for param in row["params"]:
        flags = ", ".join(param.get("opts", [])) or param["name"]
        params.append(f'<div class="parameter"><dt><code>{escape(flags)}</code></dt>'
                      f'<dd>{escape(str(param.get("help") or "No description supplied by the manifest."))}'
                      f'<br>Required: {str(bool(param.get("required"))).lower()} · Default: '
                      f'<code>{escape(str(param.get("default")))}</code></dd></div>')
    return Template((root / "site/templates/command-detail.html").read_text()).substitute(
        product_name=escape(product_name), command=escape(row["command"]), description=escape(row["description"]),
        package_version=escape(version), manifest_sha=escape(manifest_sha), contracts=contracts,
        routes="".join(routes) or "<p>This quickstart command has no reviewed D1 task route.</p>",
        parameters="".join(params) or "<p>No parameters are declared.</p>",
        help_example=escape(" ".join(row["help_example"])),
        provenance=escape(projection_provenance(build_commit)),
    ).rstrip() + "\n"
