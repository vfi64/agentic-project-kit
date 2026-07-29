from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import subprocess
from typing import Any

from agentic_project_kit.dpa_readiness import DEFAULT_READINESS_PATH
from agentic_project_kit.workspace import load_workspace

PROBE_003_SOURCE_PATHS = (
    "src/agentic_project_kit/transfer_repo_actions.py",
    "src/agentic_project_kit/gatekeeper_core.py",
    "src/agentic_project_kit/local_feature_gate.py",
    "src/agentic_project_kit/workspace_lock.py",
    "src/agentic_project_kit/handoff_freshness.py",
)
PROBE_003_TEST_GLOBS = (
    "tests/test_transfer_repo_actions.py",
    "tests/test_gatekeeper_core.py",
    "tests/test_local_feature_gate_contract.py",
    "tests/test_handoff_freshness.py",
)
PROBE_003_CONTROL_SURFACES = (
    "docs/architecture/dpa/probes/DP1_PROBE_MANUALS_20260727.md",
    "docs/architecture/dpa/probes/DP1_PROBE_EXECUTION_PACKAGE_DRAFT_20260727.md",
)
EVIDENCE_OUTPUT_ROOT_PARTS = ("evidence", "dpa", "probes")

REQUIRED_GROUPS = (
    ("P3-G01", "branch/worktree/ref identity capture", "fixture-not-executed"),
    ("P3-G02", "branch switch stale-plan rejection", "mutable-fixture"),
    ("P3-G03", "rebase/reset stale-plan rejection", "mutable-fixture"),
    ("P3-G04", "pull-request head/base identity comparison", "pr-fixture"),
    ("P3-G05", "required-check evidence bound to the exact PR head", "pr-fixture"),
    (
        "P3-G06",
        "merge eligibility blocked by stale source, target, contract, renderer, ownership, "
        "partition, gate-set or base-context dependency",
        "integration-fixture",
    ),
    (
        "P3-G07",
        "integration-time revalidation before acceptance-bearing workflow completion",
        "integration-fixture",
    ),
    ("P3-G08", "clean textual Git merge rejected as projection-freshness evidence", "fixture-not-executed"),
    (
        "P3-G09",
        "deterministic regeneration from current validation ref after stale-plan detection",
        "mutable-fixture",
    ),
    (
        "P3-G10",
        "competing projection refresh conflict across shared targets or registered partitions",
        "integration-fixture",
    ),
    (
        "P3-G11",
        "post-integration refresh bound to the accepted integration ref",
        "integration-fixture",
    ),
    (
        "P3-G12",
        "acceptance-bearing evidence publication blocked while workflow identity is stale",
        "integration-fixture",
    ),
)


@dataclass(frozen=True)
class Probe003Finding:
    code: str
    message: str
    path: str

    def as_dict(self) -> dict[str, str]:
        return {"code": self.code, "message": self.message, "path": self.path}


@dataclass(frozen=True)
class Probe003ReadinessResult:
    root: str
    validation_ref: str
    readiness_record: str
    data: dict[str, Any]
    findings: tuple[Probe003Finding, ...]

    @property
    def structural_ok(self) -> bool:
        return not self.findings

    @property
    def blockers(self) -> tuple[str, ...]:
        return tuple(str(item["id"]) for item in self.data.get("blockers", ()))

    @property
    def full_evidence_satisfied(self) -> bool:
        return self.structural_ok and not self.blockers

    @property
    def result_status(self) -> str:
        if not self.structural_ok:
            return "STRUCTURAL_BLOCK"
        if self.full_evidence_satisfied:
            return "SATISFIED_FOR_CURRENT_KIT_REF"
        return "PARTIAL_BLOCKED_FOR_DP2"

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "kind": "dpa_probe_003_workflow_serialization_readiness",
            "result_status": self.result_status,
            "validation_ref": self.validation_ref,
            "readiness_record": self.readiness_record,
            "structural_ok": self.structural_ok,
            "full_evidence_satisfied": self.full_evidence_satisfied,
            "finding_count": len(self.findings),
            "blocker_count": len(self.blockers),
            "findings": [finding.as_dict() for finding in self.findings],
            **self.data,
        }


def evaluate_probe_003_workflow_readiness(
    root: Path | str = ".",
    *,
    readiness_path: Path | str = DEFAULT_READINESS_PATH,
    validation_ref: str | None = None,
) -> Probe003ReadinessResult:
    base = Path(root).resolve()
    record_path = _resolve_under_root(base, readiness_path)
    findings: list[Probe003Finding] = []

    source_surfaces = _path_records(base, PROBE_003_SOURCE_PATHS)
    test_surfaces = _glob_records(base, PROBE_003_TEST_GLOBS)
    control_surfaces = _path_records(base, PROBE_003_CONTROL_SURFACES)
    for item in (*source_surfaces, *test_surfaces, *control_surfaces):
        if not item["present"]:
            findings.append(
                Probe003Finding(
                    code="required-surface-missing",
                    message=f"Required PROBE-003 surface is missing: {item['path']}",
                    path=item["path"],
                )
            )

    readiness_data = _load_readiness_data(record_path, base, findings)
    readiness_status = _probe_family_status(readiness_data, record_path, base, findings)
    dp2_entry_status = _probe_003_dp2_entry_status(readiness_data, record_path, base, findings)
    blockers = _blockers_for(readiness_status, dp2_entry_status)
    validation = validation_ref or _git_head(base)
    data = {
        "source_surfaces": source_surfaces,
        "test_surfaces": test_surfaces,
        "control_surfaces": control_surfaces,
        "required_groups": _group_records(blockers),
        "readiness_probe_family_status": readiness_status,
        "readiness_dp2_entry_status": dp2_entry_status,
        "blockers": blockers,
        "claims": {
            "probe_execution_claimed": False,
            "dp2_authorized": False,
            "production_mutation_performed": False,
            "workflow_queue_conformance_claimed": False,
            "generated_outputs_manually_patched": False,
        },
    }
    return Probe003ReadinessResult(
        root=base.as_posix(),
        validation_ref=validation,
        readiness_record=_display_path(record_path, base),
        data=data,
        findings=tuple(findings),
    )


def render_probe_003_workflow_readiness(result: Probe003ReadinessResult) -> str:
    payload = result.as_dict()
    lines = [
        "DPA_PROBE_003_WORKFLOW_READINESS",
        f"STATUS={payload['result_status']}",
        f"VALIDATION_REF={payload['validation_ref']}",
        f"FULL_EVIDENCE_SATISFIED={str(payload['full_evidence_satisfied']).lower()}",
        f"FINDINGS={payload['finding_count']}",
        f"BLOCKERS={payload['blocker_count']}",
    ]
    for blocker in payload["blockers"]:
        lines.append(f"BLOCKER={blocker['id']}|{blocker['message']}")
    if payload["finding_count"]:
        for finding in payload["findings"]:
            lines.append(f"FINDING={finding['code']}|path={finding['path']}|{finding['message']}")
    return "\n".join(lines) + "\n"


def write_probe_003_readiness_json(
    result: Probe003ReadinessResult,
    root: Path | str,
    output: Path | str,
    *,
    execute: bool,
) -> dict[str, Any]:
    base = Path(root).resolve()
    output_path = _resolve_under_root(base, output)
    relative = output_path.relative_to(base)
    evidence_root = _evidence_output_root(base)
    if evidence_root not in (output_path, *output_path.parents):
        return {
            "result_status": "BLOCK",
            "reason": "output_outside_dpa_probe_evidence_root",
            "output_path": relative.as_posix(),
            "written": False,
        }
    changed = True
    rendered = json.dumps(result.as_dict(), indent=2, sort_keys=True) + "\n"
    if output_path.exists():
        changed = output_path.read_text(encoding="utf-8") != rendered
    if execute:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered, encoding="utf-8")
    return {
        "result_status": "PASS",
        "output_path": relative.as_posix(),
        "changed": changed,
        "written": bool(execute),
    }


def _resolve_under_root(root: Path, path: Path | str) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return root / candidate


def _display_path(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _path_records(root: Path, paths: tuple[str, ...]) -> list[dict[str, Any]]:
    return [{"path": item, "present": (root / item).exists()} for item in paths]


def _glob_records(root: Path, patterns: tuple[str, ...]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for pattern in patterns:
        matches = sorted(path.relative_to(root).as_posix() for path in root.glob(pattern))
        records.append({"path": pattern, "present": bool(matches), "matches": matches})
    return records


def _evidence_output_root(root: Path) -> Path:
    ws = load_workspace(root, suppress_legacy_profile_warning=True)
    return ws.architecture_file(Path(*EVIDENCE_OUTPUT_ROOT_PARTS)).resolve()


def _load_readiness_data(
    path: Path,
    root: Path,
    findings: list[Probe003Finding],
) -> dict[str, Any]:
    if not path.exists():
        findings.append(
            Probe003Finding(
                code="readiness-record-missing",
                message="DPA readiness record is missing",
                path=_display_path(path, root),
            )
        )
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        findings.append(
            Probe003Finding(
                code="readiness-record-json-invalid",
                message=f"DPA readiness record is not valid JSON: {exc}",
                path=_display_path(path, root),
            )
        )
        return {}
    if not isinstance(data, dict):
        findings.append(
            Probe003Finding(
                code="readiness-record-not-object",
                message="DPA readiness record must contain a JSON object",
                path=_display_path(path, root),
            )
        )
        return {}
    return data


def _probe_family_status(
    readiness_data: dict[str, Any],
    record_path: Path,
    root: Path,
    findings: list[Probe003Finding],
) -> str:
    raw = readiness_data.get("probe_family_status")
    if not isinstance(raw, dict):
        findings.append(
            Probe003Finding(
                code="probe-family-status-missing",
                message="readiness record must contain probe_family_status mapping",
                path=_display_path(record_path, root),
            )
        )
        return "MISSING"
    status = raw.get("PROBE-003")
    if not isinstance(status, str):
        findings.append(
            Probe003Finding(
                code="probe-003-status-missing",
                message="readiness record must contain probe_family_status.PROBE-003",
                path=_display_path(record_path, root),
            )
        )
        return "MISSING"
    return status


def _probe_003_dp2_entry_status(
    readiness_data: dict[str, Any],
    record_path: Path,
    root: Path,
    findings: list[Probe003Finding],
) -> str:
    raw = readiness_data.get("dp2_entry_status")
    if not isinstance(raw, dict):
        findings.append(
            Probe003Finding(
                code="dp2-entry-status-missing",
                message="readiness record must contain dp2_entry_status mapping",
                path=_display_path(record_path, root),
            )
        )
        return "MISSING"
    status = raw.get("probe_003_full_evidence")
    if not isinstance(status, str):
        findings.append(
            Probe003Finding(
                code="probe-003-dp2-entry-status-missing",
                message="readiness record must contain dp2_entry_status.probe_003_full_evidence",
                path=_display_path(record_path, root),
            )
        )
        return "MISSING"
    return status


def _blockers_for(readiness_status: str, dp2_entry_status: str) -> list[dict[str, str]]:
    blockers: list[dict[str, str]] = []
    if readiness_status != "SATISFIED_FOR_CURRENT_KIT_REF":
        blockers.append(
            {
                "id": "probe-003-family-not-satisfied",
                "message": f"Readiness record reports PROBE-003 as {readiness_status}.",
            }
        )
    if dp2_entry_status != "SATISFIED_FOR_CURRENT_KIT_REF":
        blockers.append(
            {
                "id": "probe-003-dp2-entry-blocked",
                "message": f"DP2 entry record reports probe_003_full_evidence as {dp2_entry_status}.",
            }
        )
    if not blockers:
        return blockers
    blockers.append(
        {
            "id": "probe-003-executable-fixture-run",
            "message": "PROBE-003 has not been executed as a full exact-ref workflow serialization fixture run.",
        }
    )
    blockers.append(
        {
            "id": "probe-003-mutable-workflow-authorization",
            "message": "Branch, PR, push or integration fixtures require Maintainer authorization and rollback instructions.",
        }
    )
    return blockers


def _group_records(blockers: list[dict[str, str]]) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    if not blockers:
        return [
            {"id": group_id, "label": label, "status": "SATISFIED_FOR_CURRENT_KIT_REF"}
            for group_id, label, _category in REQUIRED_GROUPS
        ]
    for group_id, label, category in REQUIRED_GROUPS:
        if category in {"mutable-fixture", "pr-fixture", "integration-fixture"}:
            status = "BLOCKED_REQUIRES_AUTHORIZED_DISPOSABLE_WORKFLOW_FIXTURE"
        else:
            status = "PREFLIGHT_SURFACE_PRESENT_NOT_EXECUTED"
        records.append({"id": group_id, "label": label, "status": status})
    return records


def _git_head(root: Path) -> str:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except (OSError, subprocess.CalledProcessError):
        return "UNKNOWN"
    return completed.stdout.strip() or "UNKNOWN"
