"""KIT-GF-091: deterministic finding version assignment for Kit release metadata.

Consumer verification remains independent. Existing released versions are never inferred
or overwritten; historical repairs require separate, reviewed evidence.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from agentic_project_kit.greenfield_status import (
    CATALOG, EXPORT, PACKAGED, RETEST_REPORT, encoded, export, validate,
)
from agentic_project_kit.release_version_sources import is_kit_self_hosting


def plan_stamp(root: Path, version: str) -> dict:
    """Validate before any release write and bind the proposed IDs to source bytes."""
    if not is_kit_self_hosting(root) or not (root / CATALOG).exists():
        return {}
    for path in (CATALOG, EXPORT, PACKAGED, RETEST_REPORT):
        if not (root / path).resolve().is_relative_to(root.resolve()):
            raise ValueError(f"release finding path escapes root: {path}")
    raw = (root / CATALOG).read_bytes()
    data = json.loads(raw)
    missing = sorted(f["id"] for f in data["findings"]
                     if f["kit_state"] == "CLOSED" and not f.get("fixed_in"))
    if missing:
        raise ValueError("Release finding versions BLOCKED: missing fixed_in for "
                         + ", ".join(missing) + "; establish historical release evidence first")
    validate(data, root)
    ids = sorted(f["id"] for f in data["findings"]
                 if f["kit_state"] == "CLOSED" and f["fixed_in"] == "unreleased")
    plan = {"version": version, "finding_ids": ids,
            "catalog_sha256": hashlib.sha256(raw).hexdigest()}
    plan["approval_signature"] = hashlib.sha256(encoded({"root": str(root.resolve()), **plan})).hexdigest()
    return plan


def apply_stamp(root: Path, plan: dict) -> list[str]:
    """Apply the preflighted assignment and use the existing signed export route."""
    if not plan:
        return []
    if plan_stamp(root, plan["version"]) != plan:
        raise ValueError("release finding plan changed; replan before writing")
    if not plan["finding_ids"]:
        return []
    data = json.loads((root / CATALOG).read_bytes())
    selected = set(plan["finding_ids"])
    for finding in data["findings"]:
        if finding["id"] in selected:
            finding["fixed_in"] = plan["version"]
    # Preserve source key order; generated status outputs retain their canonical encoder.
    (root / CATALOG).write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    export_plan = export(root)
    result = export(root, execute=True, expected_signature=export_plan["approval_signature"])
    return [CATALOG.as_posix(), *result["changed_paths"]]


def gate_findings(root: Path, version: str) -> dict:
    """B4 signs the prepared release's IDs and exact catalog, including on resume."""
    if not is_kit_self_hosting(root) or not (root / CATALOG).exists():
        return {}
    raw = (root / CATALOG).read_bytes()
    data = json.loads(raw)
    return {"version": version, "catalog_sha256": hashlib.sha256(raw).hexdigest(),
            "finding_ids": sorted(f["id"] for f in data["findings"]
                                  if f["kit_state"] == "CLOSED" and f.get("fixed_in") == version)}
