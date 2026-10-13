"""Validated, deterministic public adjudications; consumer verification is separate."""

from collections import Counter
from importlib.resources import files
import hashlib
import json
from pathlib import Path
from agentic_project_kit.workspace import KitConfig

CATALOG = Path(".agentic/greenfield_findings.json")
PUBLIC_REPORTS = Path(KitConfig().docs_root) / "reports"
EXPORT = PUBLIC_REPORTS / "greenfield" / "external-findings-status.json"
PACKAGED = Path("src/agentic_project_kit/reference/external-findings-status.json")
RETEST_REPORT = PUBLIC_REPORTS / "greenfield" / "EXTERNAL_FINDINGS_RETESTS.md"
STATES = {"OPEN", "PARTIAL", "CLOSED", "NOT_APPLICABLE"}
FAMILIES = {f"KIT-GF-{n:03}" for n in (*range(1, 19), *range(21, 67))} | {
    "KIT-GF-RULE-REGISTRY-BOOTSTRAP"
}


def encoded(data: dict) -> bytes:
    return (json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode()


def validate(data: dict, root: Path | None = None) -> None:
    if data.get("schema_version") != 1 or not isinstance(data.get("findings"), list):
        raise ValueError("unsupported finding schema")
    ids = [f["id"] for f in data["findings"]]
    if len(ids) != len(set(ids)) or not FAMILIES <= set(ids):
        raise ValueError("duplicate or missing finding families")
    for f in data["findings"]:
        if f["kit_state"] not in STATES or not isinstance(f["fixed_in"], str):
            raise ValueError("invalid Kit adjudication")
        if not isinstance(f["prs"], list) or any(not isinstance(p, int) or p < 1 for p in f["prs"]):
            raise ValueError("invalid PR references")
        report = Path(f["report"])
        if (
            report.is_absolute()
            or ".." in report.parts
            or not report.is_relative_to(PUBLIC_REPORTS)
        ):
            raise ValueError("report must be a repository evidence path")
        if root and (
            not (root / report).resolve().is_relative_to(root.resolve())
            or not (root / report).is_file()
        ):
            raise ValueError(f"missing report: {report}")
        r = f["external_retest"]
        if not isinstance(r.get("expected_result_fields"), dict) or not isinstance(
            r.get("bindings"), dict
        ):
            raise ValueError("missing exact result fields or runner bindings")
        if (
            r["workspace_kind"] not in {"external_manifest", "kit_release"}
            or not r["preconditions"]
            or not r["commands"]
            or not r["expected"]
        ):
            raise ValueError("incomplete external retest contract")
        for command in r["commands"]:
            if not isinstance(command, str) or not command.startswith("agentic-kit "):
                raise ValueError("retests must name Kit routes")
        if f["id"] in {"KIT-GF-055", "KIT-GF-056", "KIT-GF-058", "KIT-GF-059"}:
            if (
                f.get("kit_release_evidence", {}).get("path")
                != (PUBLIC_REPORTS / "release" / "release-run-1.0.25.json").as_posix()
            ):
                raise ValueError("publishing finding requires release-run evidence")


def build(root: Path) -> dict:
    source = json.loads((root / CATALOG).read_text())
    validate(source, root)
    records = sorted(source["findings"], key=lambda f: f["id"])
    return {
        "schema_version": 1,
        "kind": "external_findings_status",
        "authority": "Kit adjudication; VERIFIED_FIXED belongs to the consuming workspace",
        "source_sha256": hashlib.sha256(encoded(source)).hexdigest(),
        "counts": {s: sum(f["kit_state"] == s for f in records) for s in sorted(STATES)},
        "findings": records,
    }


def read_status(finding_id: str = "") -> dict:
    result = json.loads(
        files("agentic_project_kit").joinpath("reference/external-findings-status.json").read_text()
    )
    validate(result)
    if finding_id:
        selected = [f for f in result["findings"] if f["id"] == finding_id]
        if not selected:
            raise ValueError("unknown finding id")
        result = {
            **result,
            "findings": selected,
            "counts": dict(Counter(f["kit_state"] for f in selected)),
        }
    return result


def export(root: Path, *, execute: bool = False, expected_signature: str = "") -> dict:
    root = root.resolve()
    data = build(root)
    desired = {
        EXPORT: encoded(data),
        PACKAGED: encoded(data),
        RETEST_REPORT: render_retests(data).encode(),
    }
    paths = tuple(desired)
    for p in paths:
        if not (root / p).resolve().is_relative_to(root):
            raise ValueError("export target escapes root")
    previous = [
        hashlib.sha256((root / p).read_bytes()).hexdigest() if (root / p).exists() else None
        for p in paths
    ]
    signature = hashlib.sha256(
        encoded(
            {
                "root": str(root),
                "previous": previous,
                "desired": {str(p): hashlib.sha256(b).hexdigest() for p, b in desired.items()},
            }
        )
    ).hexdigest()
    changed = [
        p.as_posix()
        for p in paths
        if not (root / p).exists() or (root / p).read_bytes() != desired[p]
    ]
    result = {
        "result_status": "PLANNED" if changed else "PASS",
        "approval_signature": signature,
        "changed_paths": changed,
    }
    if execute:
        if expected_signature != signature:
            raise ValueError("signature mismatch; replan against current evidence")
        from agentic_project_kit.workspace_lock import acquire_workspace_lock

        with acquire_workspace_lock(root, "greenfield-export"):
            # Revalidate inputs after acquiring the workspace lock.
            current = export(root)
            if current["approval_signature"] != signature:
                raise ValueError("export inputs changed while acquiring lock")
            for p in paths:
                if p.as_posix() in changed:
                    target = root / p
                    target.parent.mkdir(parents=True, exist_ok=True)
                    pending = target.with_suffix(".json.pending")
                    pending.write_bytes(desired[p])
                    pending.replace(target)
        result["result_status"] = "PASS"
    return result


def render_retests(data: dict) -> str:
    lines = [
        "---",
        "artifact_type: evidence",
        "status: active",
        "review_policy: historical_evidence",
        "---",
        "",
        "# External finding retest contracts",
        "",
        "Generated from .agentic/greenfield_findings.json by the signed greenfield export route.",
        "These are executable templates, not successful test evidence. Substitute bindings as single argv tokens.",
        "Consumer VERIFIED_FIXED requires its own retained results. Publishing evidence can be absent pending a release.",
        "",
    ]
    for f in data["findings"]:
        r = f["external_retest"]
        lines += [
            f"## {f['id']}",
            "",
            f"Kit state: {f['kit_state']}; fixed_in: {f['fixed_in'] or 'not established'}.",
            f"Evidence: {f['report']}",
            "",
            "Preconditions: " + " ".join(r["preconditions"]),
            "",
            "```text",
            *r["commands"],
            "```",
            "",
            "Expected: " + " ".join(r["expected"]),
            "",
            "Expected result fields: `"
            + json.dumps(r["expected_result_fields"], sort_keys=True)
            + "`.",
            "",
        ]
    return "\n".join(lines) + "\n"
