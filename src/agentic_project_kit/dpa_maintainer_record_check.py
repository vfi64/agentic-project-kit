from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import subprocess
from typing import Any

from agentic_project_kit.dpa_readiness import DEFAULT_READINESS_PATH
from agentic_project_kit.workspace import KitConfig, load_workspace

_DEFAULT_CONFIG = KitConfig()
DEFAULT_MAINTAINER_RECORD_PATH = (
    Path(_DEFAULT_CONFIG.architecture_root)
    / "evidence"
    / "dpa"
    / "assessment"
    / "DP2_MAINTAINER_ASSESSMENT_RECORD_20260728.json"
)
EXPECTED_KIND = "dpa_dp2_maintainer_assessment_record"
EXPECTED_SCHEMA_VERSION = 1
STATUS_TEMPLATE = "TEMPLATE_NOT_ASSESSED"
STATUS_BLOCKED = "DP2_BLOCKED"
STATUS_AUTHORIZED = "DP2_AUTHORIZED"
ALLOWED_STATUSES = {STATUS_TEMPLATE, STATUS_BLOCKED, STATUS_AUTHORIZED}
REQUIRED_PROBE_DISPOSITIONS = ("PROBE-002", "RENDERER", "PROBE-003", "PROBE-004")
ALLOWED_PROBE_STATUSES = {
    "BLOCKED",
    "SATISFIED_FOR_CURRENT_KIT_REF",
    "EXPLICITLY_NOT_APPLICABLE",
}
SELF_HOSTING_WRITERS = ("WRT-CH-001", "WRT-CH-002", "WRT-CH-003", "WRT-CH-004")
REQUIRED_FALSE_CLAIMS = (
    "runtime_behavior_changed",
    "production_mutation_performed",
    "kit_conformance_claimed",
    "generated_outputs_manually_patched",
)
ASSESSMENT_OUTPUT_ROOT_PARTS = ("evidence", "dpa", "assessment")


@dataclass(frozen=True)
class MaintainerRecordFinding:
    code: str
    message: str
    path: str

    def as_dict(self) -> dict[str, str]:
        return {"code": self.code, "message": self.message, "path": self.path}


@dataclass(frozen=True)
class MaintainerRecordCheckResult:
    root: str
    validation_ref: str
    record_path: str
    data: dict[str, Any]
    findings: tuple[MaintainerRecordFinding, ...]
    action_items: tuple[dict[str, str], ...]

    @property
    def structural_ok(self) -> bool:
        return not self.findings

    @property
    def record_status(self) -> str:
        status = self.data.get("status")
        return str(status) if isinstance(status, str) else "MISSING"

    @property
    def result_status(self) -> str:
        if not self.structural_ok:
            return "STRUCTURAL_BLOCK"
        if self.record_status == STATUS_AUTHORIZED:
            return "VALID_AUTHORIZATION_RECORD"
        if self.record_status == STATUS_TEMPLATE:
            return "TEMPLATE_READY_DP2_BLOCKED"
        return "VALID_BLOCKED_RECORD"

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "kind": "dpa_dp2_maintainer_record_check",
            "result_status": self.result_status,
            "validation_ref": self.validation_ref,
            "record_path": self.record_path,
            "record_status": self.record_status,
            "structural_ok": self.structural_ok,
            "finding_count": len(self.findings),
            "findings": [finding.as_dict() for finding in self.findings],
            "action_item_count": len(self.action_items),
            "action_items": list(self.action_items),
            "record_summary": _record_summary(self.data),
            "claims": self.data.get("claims", {}),
        }


def evaluate_dp2_maintainer_record(
    root: Path | str = ".",
    *,
    record_path: Path | str = DEFAULT_MAINTAINER_RECORD_PATH,
    readiness_path: Path | str = DEFAULT_READINESS_PATH,
    validation_ref: str | None = None,
) -> MaintainerRecordCheckResult:
    base = Path(root).resolve()
    record = _resolve_under_root(base, record_path)
    display_path = _display_path(record, base)
    findings: list[MaintainerRecordFinding] = []

    if not record.exists():
        return MaintainerRecordCheckResult(
            root=base.as_posix(),
            validation_ref=validation_ref or _git_head(base),
            record_path=display_path,
            data={},
            findings=(
                MaintainerRecordFinding(
                    code="maintainer-record-missing",
                    message="DPA DP2 Maintainer Assessment record is missing",
                    path=display_path,
                ),
            ),
            action_items=(
                {
                    "id": "create-maintainer-record",
                    "message": "Create a Maintainer-owned record from the DP2 assessment template before DP2 authorization.",
                },
            ),
        )

    try:
        data = json.loads(record.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return MaintainerRecordCheckResult(
            root=base.as_posix(),
            validation_ref=validation_ref or _git_head(base),
            record_path=display_path,
            data={},
            findings=(
                MaintainerRecordFinding(
                    code="maintainer-record-json-invalid",
                    message=f"Maintainer record is not valid JSON: {exc}",
                    path=display_path,
                ),
            ),
            action_items=(),
        )

    if not isinstance(data, dict):
        return MaintainerRecordCheckResult(
            root=base.as_posix(),
            validation_ref=validation_ref or _git_head(base),
            record_path=display_path,
            data={},
            findings=(
                MaintainerRecordFinding(
                    code="maintainer-record-not-object",
                    message="Maintainer record must contain a JSON object",
                    path=display_path,
                ),
            ),
            action_items=(),
        )

    readiness = _resolve_under_root(base, readiness_path)
    _validate_top_level(data, findings, display_path)
    _validate_paths(data, findings, display_path, base, readiness)
    _validate_probe_dispositions(data, findings, display_path)
    _validate_scope(data, findings, display_path, base)
    _validate_rollback(data, findings, display_path)
    _validate_claims(data, findings, display_path)
    _validate_authorization(data, findings, display_path)
    validation = validation_ref or _git_head(base)
    return MaintainerRecordCheckResult(
        root=base.as_posix(),
        validation_ref=validation,
        record_path=display_path,
        data=data,
        findings=tuple(findings),
        action_items=tuple(_action_items(data)),
    )


def render_dp2_maintainer_record_check(result: MaintainerRecordCheckResult) -> str:
    payload = result.as_dict()
    lines = [
        "DPA_DP2_MAINTAINER_RECORD_CHECK",
        f"STATUS={payload['result_status']}",
        f"VALIDATION_REF={payload['validation_ref']}",
        f"RECORD={payload['record_path']}",
        f"RECORD_STATUS={payload['record_status']}",
        f"FINDINGS={payload['finding_count']}",
        f"ACTION_ITEMS={payload['action_item_count']}",
    ]
    for item in payload["action_items"]:
        lines.append(f"ACTION_ITEM={item['id']}|{item['message']}")
    if payload["finding_count"]:
        for finding in payload["findings"]:
            lines.append(f"FINDING={finding['code']}|path={finding['path']}|{finding['message']}")
    return "\n".join(lines) + "\n"


def write_dp2_maintainer_record_check_json(
    result: MaintainerRecordCheckResult,
    root: Path | str,
    output: Path | str,
    *,
    execute: bool,
) -> dict[str, Any]:
    base = Path(root).resolve()
    output_path = _resolve_under_root(base, output)
    relative = output_path.relative_to(base)
    evidence_root = _assessment_output_root(base)
    if evidence_root not in (output_path, *output_path.parents):
        return {
            "result_status": "BLOCK",
            "reason": "output_outside_dpa_assessment_evidence_root",
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


def _assessment_output_root(root: Path) -> Path:
    ws = load_workspace(root, suppress_legacy_profile_warning=True)
    return ws.architecture_file(Path(*ASSESSMENT_OUTPUT_ROOT_PARTS)).resolve()


def _validate_top_level(
    data: dict[str, Any],
    findings: list[MaintainerRecordFinding],
    path: str,
) -> None:
    if data.get("schema_version") != EXPECTED_SCHEMA_VERSION:
        findings.append(
            MaintainerRecordFinding(
                code="invalid-schema-version",
                message=f"schema_version must be {EXPECTED_SCHEMA_VERSION}",
                path=path,
            )
        )
    if data.get("kind") != EXPECTED_KIND:
        findings.append(
            MaintainerRecordFinding(
                code="invalid-kind",
                message=f"kind must be {EXPECTED_KIND!r}",
                path=path,
            )
        )
    status = data.get("status")
    if status not in ALLOWED_STATUSES:
        findings.append(
            MaintainerRecordFinding(
                code="invalid-status",
                message=f"status must be one of {sorted(ALLOWED_STATUSES)}",
                path=path,
            )
        )
    if not isinstance(data.get("template"), bool):
        findings.append(
            MaintainerRecordFinding(
                code="template-flag-missing",
                message="template must be a boolean",
                path=path,
            )
        )
    if data.get("status") == STATUS_TEMPLATE and data.get("template") is not True:
        findings.append(
            MaintainerRecordFinding(
                code="template-status-without-template-flag",
                message="TEMPLATE_NOT_ASSESSED records must set template=true",
                path=path,
            )
        )


def _validate_paths(
    data: dict[str, Any],
    findings: list[MaintainerRecordFinding],
    path: str,
    root: Path,
    readiness_path: Path,
) -> None:
    for field in ("readiness_record", "decision_readiness_evidence"):
        raw = data.get(field)
        if not isinstance(raw, str) or not raw:
            findings.append(
                MaintainerRecordFinding(
                    code=f"{field.replace('_', '-')}-missing",
                    message=f"{field} must be a non-empty repository-relative path",
                    path=path,
                )
            )
            continue
        candidate = Path(raw)
        if candidate.is_absolute():
            findings.append(
                MaintainerRecordFinding(
                    code=f"{field.replace('_', '-')}-absolute",
                    message=f"{field} must be repository-relative: {raw}",
                    path=path,
                )
            )
            continue
        if not (root / candidate).exists():
            findings.append(
                MaintainerRecordFinding(
                    code=f"{field.replace('_', '-')}-not-found",
                    message=f"{field} does not exist: {raw}",
                    path=path,
                )
            )
    readiness_display = _display_path(readiness_path, root)
    if data.get("readiness_record") != readiness_display:
        findings.append(
            MaintainerRecordFinding(
                code="readiness-record-mismatch",
                message=f"readiness_record must match inspected record {readiness_display}",
                path=path,
            )
        )


def _validate_probe_dispositions(
    data: dict[str, Any],
    findings: list[MaintainerRecordFinding],
    path: str,
) -> None:
    dispositions = data.get("probe_dispositions")
    if not isinstance(dispositions, dict):
        findings.append(
            MaintainerRecordFinding(
                code="probe-dispositions-missing",
                message="probe_dispositions must be a mapping",
                path=path,
            )
        )
        return
    for family in REQUIRED_PROBE_DISPOSITIONS:
        record = dispositions.get(family)
        if not isinstance(record, dict):
            findings.append(
                MaintainerRecordFinding(
                    code="probe-disposition-missing",
                    message=f"probe_dispositions.{family} must be a mapping",
                    path=path,
                )
            )
            continue
        status = record.get("status")
        if status not in ALLOWED_PROBE_STATUSES:
            findings.append(
                MaintainerRecordFinding(
                    code="invalid-probe-disposition-status",
                    message=f"{family}.status must be one of {sorted(ALLOWED_PROBE_STATUSES)}",
                    path=path,
                )
            )
        evidence = record.get("evidence")
        if evidence is not None and not _string_list(evidence):
            findings.append(
                MaintainerRecordFinding(
                    code="invalid-probe-disposition-evidence",
                    message=f"{family}.evidence must be a list of strings when present",
                    path=path,
                )
            )
        if status == "EXPLICITLY_NOT_APPLICABLE" and not str(record.get("rationale", "")).strip():
            findings.append(
                MaintainerRecordFinding(
                    code="not-applicable-rationale-missing",
                    message=f"{family} requires rationale when explicitly not applicable",
                    path=path,
                )
            )


def _validate_scope(
    data: dict[str, Any],
    findings: list[MaintainerRecordFinding],
    path: str,
    root: Path,
) -> None:
    scope = data.get("first_dp2_target_scope")
    if not isinstance(scope, dict):
        findings.append(
            MaintainerRecordFinding(
                code="first-dp2-target-scope-missing",
                message="first_dp2_target_scope must be a mapping",
                path=path,
            )
        )
        return
    if scope.get("status") not in {"UNSELECTED", "SELECTED"}:
        findings.append(
            MaintainerRecordFinding(
                code="invalid-target-scope-status",
                message="first_dp2_target_scope.status must be UNSELECTED or SELECTED",
                path=path,
            )
        )
    raw_target = scope.get("target_path")
    if not isinstance(raw_target, str) or not raw_target:
        findings.append(
            MaintainerRecordFinding(
                code="target-path-missing",
                message="first_dp2_target_scope.target_path must be a non-empty path",
                path=path,
            )
        )
    elif Path(raw_target).is_absolute():
        findings.append(
            MaintainerRecordFinding(
                code="target-path-absolute",
                message="first_dp2_target_scope.target_path must be repository-relative",
                path=path,
            )
        )
    elif not (root / raw_target).exists():
        findings.append(
            MaintainerRecordFinding(
                code="target-path-not-found",
                message=f"first_dp2_target_scope.target_path does not exist: {raw_target}",
                path=path,
            )
        )
    for field in ("selected_writers", "deferred_writers", "excluded_writers"):
        if not _string_list(scope.get(field)):
            findings.append(
                MaintainerRecordFinding(
                    code=f"{field.replace('_', '-')}-invalid",
                    message=f"first_dp2_target_scope.{field} must be a list of strings",
                    path=path,
                )
            )
    if data.get("status") == STATUS_AUTHORIZED:
        covered = set(scope.get("selected_writers", ())) | set(scope.get("deferred_writers", ()))
        missing = sorted(set(SELF_HOSTING_WRITERS) - covered)
        for writer in missing:
            findings.append(
                MaintainerRecordFinding(
                    code="self-hosting-writer-undisposed",
                    message=f"{writer} must be selected or deferred before DP2 authorization",
                    path=path,
                )
            )


def _validate_rollback(
    data: dict[str, Any],
    findings: list[MaintainerRecordFinding],
    path: str,
) -> None:
    rollback = data.get("rollback_cleanup")
    if not isinstance(rollback, dict):
        findings.append(
            MaintainerRecordFinding(
                code="rollback-cleanup-missing",
                message="rollback_cleanup must be a mapping",
                path=path,
            )
        )
        return
    if rollback.get("status") not in {"NOT_PROVEN", "PROVEN"}:
        findings.append(
            MaintainerRecordFinding(
                code="invalid-rollback-cleanup-status",
                message="rollback_cleanup.status must be NOT_PROVEN or PROVEN",
                path=path,
            )
        )
    evidence = rollback.get("evidence")
    if not _string_list(evidence):
        findings.append(
            MaintainerRecordFinding(
                code="rollback-cleanup-evidence-invalid",
                message="rollback_cleanup.evidence must be a list of strings",
                path=path,
            )
        )


def _validate_claims(
    data: dict[str, Any],
    findings: list[MaintainerRecordFinding],
    path: str,
) -> None:
    claims = data.get("claims")
    if not isinstance(claims, dict):
        findings.append(
            MaintainerRecordFinding(code="claims-missing", message="claims must be a mapping", path=path)
        )
        return
    for claim in REQUIRED_FALSE_CLAIMS:
        if claims.get(claim) is not False:
            findings.append(
                MaintainerRecordFinding(
                    code="unsafe-runtime-claim",
                    message=f"claim {claim!r} must remain false in a DP2 assessment record",
                    path=path,
                )
            )
    if data.get("status") != STATUS_AUTHORIZED:
        for claim in ("maintainer_authorization_recorded", "dp2_authorized"):
            if claims.get(claim) is not False:
                findings.append(
                    MaintainerRecordFinding(
                        code="premature-authorization-claim",
                        message=f"claim {claim!r} must be false unless status is DP2_AUTHORIZED",
                        path=path,
                    )
                )
    if data.get("status") == STATUS_TEMPLATE and claims.get("maintainer_assessment_recorded") is not False:
        findings.append(
            MaintainerRecordFinding(
                code="premature-assessment-claim",
                message="claim 'maintainer_assessment_recorded' must be false for template records",
                path=path,
            )
        )


def _validate_authorization(
    data: dict[str, Any],
    findings: list[MaintainerRecordFinding],
    path: str,
) -> None:
    if data.get("status") != STATUS_AUTHORIZED:
        return
    if data.get("template") is not False:
        findings.append(
            MaintainerRecordFinding(
                code="authorized-template-record",
                message="DP2_AUTHORIZED records must set template=false",
                path=path,
            )
        )
    if data.get("decision_token") != "DPA_DP2_AUTHORIZED":
        findings.append(
            MaintainerRecordFinding(
                code="authorization-token-missing",
                message="DP2_AUTHORIZED records must set decision_token to DPA_DP2_AUTHORIZED",
                path=path,
            )
        )
    if not str(data.get("maintainer", "")).strip() or data.get("maintainer") == "PENDING_MAINTAINER":
        findings.append(
            MaintainerRecordFinding(
                code="maintainer-missing",
                message="DP2_AUTHORIZED records must name the Maintainer assessor",
                path=path,
            )
        )
    claims = data.get("claims")
    if isinstance(claims, dict):
        for claim in (
            "maintainer_assessment_recorded",
            "maintainer_authorization_recorded",
            "dp2_authorized",
        ):
            if claims.get(claim) is not True:
                findings.append(
                    MaintainerRecordFinding(
                        code="authorization-claim-missing",
                        message=f"DP2_AUTHORIZED records must set claim {claim!r} to true",
                        path=path,
                    )
                )
    dispositions = data.get("probe_dispositions")
    if isinstance(dispositions, dict):
        for family in REQUIRED_PROBE_DISPOSITIONS:
            record = dispositions.get(family)
            status = record.get("status") if isinstance(record, dict) else None
            if status == "BLOCKED":
                findings.append(
                    MaintainerRecordFinding(
                        code="authorized-with-blocked-probe",
                        message=f"{family} remains BLOCKED in a DP2_AUTHORIZED record",
                        path=path,
                    )
                )
            evidence = record.get("evidence") if isinstance(record, dict) else None
            if status == "SATISFIED_FOR_CURRENT_KIT_REF" and not _string_list(evidence):
                findings.append(
                    MaintainerRecordFinding(
                        code="authorized-probe-evidence-missing",
                        message=f"{family} requires evidence paths when satisfied for DP2 authorization",
                        path=path,
                    )
                )
    scope = data.get("first_dp2_target_scope")
    if isinstance(scope, dict) and scope.get("status") != "SELECTED":
        findings.append(
            MaintainerRecordFinding(
                code="authorized-target-scope-not-selected",
                message="DP2_AUTHORIZED records must set first_dp2_target_scope.status to SELECTED",
                path=path,
            )
        )
    rollback = data.get("rollback_cleanup")
    if isinstance(rollback, dict) and rollback.get("status") != "PROVEN":
        findings.append(
            MaintainerRecordFinding(
                code="authorized-rollback-not-proven",
                message="DP2_AUTHORIZED records must set rollback_cleanup.status to PROVEN",
                path=path,
            )
        )


def _record_summary(data: dict[str, Any]) -> dict[str, Any]:
    scope = data.get("first_dp2_target_scope") if isinstance(data, dict) else None
    rollback = data.get("rollback_cleanup") if isinstance(data, dict) else None
    return {
        "template": data.get("template"),
        "maintainer": data.get("maintainer"),
        "decision_token": data.get("decision_token"),
        "target_path": scope.get("target_path") if isinstance(scope, dict) else None,
        "target_scope_status": scope.get("status") if isinstance(scope, dict) else None,
        "rollback_cleanup_status": rollback.get("status") if isinstance(rollback, dict) else None,
    }


def _action_items(data: dict[str, Any]) -> list[dict[str, str]]:
    if data.get("status") == STATUS_AUTHORIZED:
        return []
    items: list[dict[str, str]] = []
    dispositions = data.get("probe_dispositions")
    if not isinstance(dispositions, dict) or any(
        not isinstance(dispositions.get(family), dict)
        or dispositions[family].get("status") == "BLOCKED"
        for family in REQUIRED_PROBE_DISPOSITIONS
    ):
        items.append(
            {
                "id": "complete-probe-dispositions",
                "message": "Record satisfied or explicitly-not-applicable dispositions for PROBE-002, RENDERER, PROBE-003 and PROBE-004.",
            }
        )
    scope = data.get("first_dp2_target_scope")
    scope_ready = False
    if isinstance(scope, dict) and scope.get("status") == "SELECTED":
        covered = set(scope.get("selected_writers", ())) | set(scope.get("deferred_writers", ()))
        scope_ready = set(SELF_HOSTING_WRITERS) <= covered
    if not scope_ready:
        items.append(
            {
                "id": "select-or-defer-writers",
                "message": "Select or defer WRT-CH-001 through WRT-CH-004 for the first DP2 target scope.",
            }
        )
    rollback = data.get("rollback_cleanup")
    if not isinstance(rollback, dict) or rollback.get("status") != "PROVEN":
        items.append(
            {
                "id": "prove-rollback-cleanup",
                "message": "Attach rollback and cleanup evidence for the selected target before authorization.",
            }
        )
    items.append(
        {
            "id": "record-maintainer-authorization",
            "message": "Only a Maintainer-owned non-template record with decision_token DPA_DP2_AUTHORIZED may authorize DP2.",
        }
    )
    return items


def _string_list(value: Any) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


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
