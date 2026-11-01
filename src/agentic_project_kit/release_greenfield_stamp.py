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


def _external_projection_release_prerequisites(root: Path, data: dict, selected: list[str]) -> dict:
    if "KIT-GF-094" not in selected:
        return {}
    finding = next(item for item in data["findings"] if item["id"] == "KIT-GF-094")
    path = root / Path(finding["report"]).with_suffix(".json")
    if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
        raise ValueError("KIT-GF-094 release prerequisites path unsafe")
    try:
        raw = path.read_bytes()
        report = json.loads(raw)
        states = report["release_prerequisites"]
        missing = [key for key in ("local_return", "consumer_rehearsal", "owner_acceptance")
                   if states.get(key) != "PASS"]
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        raise ValueError("KIT-GF-094 release prerequisites missing or invalid") from exc
    if missing:
        raise ValueError("KIT-GF-094 release BLOCKED: " + ", ".join(missing))
    # Existing signed release approval binds the reviewed evidence bytes as
    # well as the catalog. A changed acceptance report invalidates the plan.
    return {"release_prerequisites_sha256": hashlib.sha256(raw).hexdigest()}


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
            "catalog_sha256": hashlib.sha256(raw).hexdigest(),
            **_external_projection_release_prerequisites(root, data, ids)}
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
    ids = sorted(f["id"] for f in data["findings"]
                 if f["kit_state"] == "CLOSED" and f.get("fixed_in") == version)
    return {"version": version, "catalog_sha256": hashlib.sha256(raw).hexdigest(),
            "finding_ids": ids, **_external_projection_release_prerequisites(root, data, ids)}
