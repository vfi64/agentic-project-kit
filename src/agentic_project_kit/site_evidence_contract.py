"""Small website evidence boundary and dependency contract, independent of rendering."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from agentic_project_kit.ci_runtime_policy import (
    BUILD_REQUIRED,
    classify_pages_build,
    validate_pages_input_manifest,
)

CLAIM_SCOPES = frozenset({"technical", "documentation", "historical-observation"})


def evidence_policy_blockers(root: Path, record: dict[str, Any]) -> tuple[str, ...]:
    scope = record.get("scope", "technical")
    problems = []
    if not isinstance(scope, str) or scope not in CLAIM_SCOPES:
        problems.append("unsupported claim scope")
    if scope == "historical-observation" and (
        not isinstance(record.get("scope_note"), str) or not record["scope_note"].strip()
    ):
        problems.append("historical observation requires scope_note")
    for evidence in evidence_records(record):
        path = evidence.get("path", "")
        if evidence.get("type") == "file-contains" and isinstance(path, str):
            try:
                parts = (root / path).resolve().relative_to(root.resolve()).parts
            except ValueError:
                problems.append("evidence path escapes root")
                continue
            if parts[:1] == ("site",) and scope != "documentation":
                problems.append("presentation text cannot verify a technical or historical claim")
            if parts[:2] == ("docs", "site") and scope != "documentation":
                problems.append("generated presentation cannot verify its own claim")
    return tuple(problems)


def evidence_records(record: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    raw = record.get("evidence")
    return (
        (raw,)
        if isinstance(raw, dict)
        else tuple(e for e in raw if isinstance(e, dict))
        if isinstance(raw, list)
        else ()
    )


def direct_evidence_paths(records: list[dict[str, Any]]) -> tuple[str, ...]:
    paths = set()
    for record in records:
        for evidence in evidence_records(record):
            kind = evidence.get("type")
            if not isinstance(kind, str):
                continue
            if kind in {"pyproject-entrypoint", "pyproject-value"}:
                paths.add("pyproject.toml")
            if kind in {"command-manifest", "command-probe", "generated-artifact"}:
                paths.add("docs/reference/agentic-kit-commands.json")
            if kind == "release-pypi-workflow":
                paths.add("pyproject.toml")
                paths.add("docs/reports/release/")
            if kind == "file-contains" and isinstance(evidence.get("path"), str):
                paths.add(evidence["path"])
            if kind == "pytest-node" and isinstance(evidence.get("node_id"), str):
                paths.add(evidence["node_id"].split("::")[0])
            if kind == "generated-artifact" and isinstance(evidence.get("source"), str):
                paths.add(evidence["source"])
            for key in ("producer", "command"):
                argv = evidence.get(key)
                if isinstance(argv, list):
                    paths.update(
                        item for item in argv if isinstance(item, str) and item.endswith(".py")
                    )
    return tuple(sorted(paths))


def pages_evidence_blockers(root: Path, records: list[dict[str, Any]]) -> tuple[str, ...]:
    try:
        manifest = json.loads((root / "site/pages_input_manifest.json").read_text())
    except (OSError, ValueError):
        return ("Pages evidence input manifest is missing or unreadable",)
    if not isinstance(manifest, dict):
        return ("Pages input manifest must be an object",)
    schema = validate_pages_input_manifest(manifest)
    if schema:
        return tuple("Pages input manifest: " + issue for issue in schema)
    missing = [
        path
        for path in direct_evidence_paths(records)
        if classify_pages_build([path], event_name="push", manifest=manifest).mode != BUILD_REQUIRED
    ]
    return tuple(f"Pages input not covered: {path}" for path in missing)


def selected_command_blockers(*projections: dict[str, Any]) -> tuple[str, ...]:
    missing = set()
    for projection in projections:
        for key in ("flows", "modes"):
            for group in projection.get(key, []):
                for row in group.get("commands", []):
                    if not row.get("manifest_present"):
                        missing.add(str(row.get("qualified_name")))
    return tuple(f"selected website command missing: {name}" for name in sorted(missing))
