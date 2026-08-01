from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from agentic_project_kit.workspace import KitConfig, load_workspace

_DEFAULT_CONFIG = KitConfig()
DEFAULT_READINESS_PATH = (
    Path(_DEFAULT_CONFIG.architecture_root)
    / "evidence"
    / "dpa"
    / "assessment"
    / "dp1-assessment-readiness-20260728.json"
)
EXPECTED_KIND = "dpa_dp1_assessment_readiness"
EXPECTED_SCHEMA_VERSION = 1
BLOCKED_STATUS = "DP2_BLOCKED"
AUTHORIZED_STATUS = "DP2_AUTHORIZED"
REQUIRED_PROBE_FAMILIES = ("PROBE-001", "PROBE-002", "RENDERER", "PROBE-003", "PROBE-004")
REQUIRED_FALSE_CLAIMS = (
    "full_probe_pass_claimed",
    "runtime_behavior_changed",
    "production_mutation_performed",
    "kit_conformance_claimed",
    "generated_outputs_manually_patched",
)
PROGRESS_MODEL = "dpa-readiness-v1"
IMPLEMENTATION_SCOPE = "DP2_SELECTED_SELF_HOSTING_CURRENT_HANDOFF_SCOPE"
KIT_WIDE_DPA_STATUS = "NOT_ASSESSED_BY_DP2_READINESS"
PROGRESS_WEIGHTS = (
    ("architecture_staging", "Architecture package staged in Kit", 25),
    ("dp1_evidence_staged", "DP1 evidence inputs staged", 10),
    ("dp1_readiness_recorded", "DP1 Assessment readiness recorded", 5),
    ("probe_001_full_evidence", "PROBE-001 full evidence", 8),
    ("probe_002_full_evidence", "PROBE-002 full evidence", 8),
    ("renderer_full_evidence", "Renderer Probe full evidence", 8),
    ("probe_003_full_evidence", "PROBE-003 full evidence", 8),
    ("probe_004_full_evidence", "PROBE-004 full evidence", 8),
    ("maintainer_assessment", "Maintainer Assessment recorded", 7),
    ("first_dp2_target_scope", "First DP2 target and writer scope selected", 4),
    ("rollback_cleanup_proven", "Rollback and cleanup proven", 4),
    ("maintainer_authorization", "Maintainer DP2 authorization recorded", 5),
)


@dataclass(frozen=True)
class DpaReadinessFinding:
    code: str
    message: str
    path: str = DEFAULT_READINESS_PATH.as_posix()

    def as_dict(self) -> dict[str, str]:
        return {"code": self.code, "message": self.message, "path": self.path}


@dataclass(frozen=True)
class DpaProgressItem:
    id: str
    label: str
    weight: int
    earned: int
    status: str

    def as_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "label": self.label,
            "weight": self.weight,
            "earned": self.earned,
            "status": self.status,
        }


@dataclass(frozen=True)
class DpaReadinessResult:
    path: str
    data: dict[str, Any]
    findings: tuple[DpaReadinessFinding, ...]
    blockers: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return not self.findings

    @property
    def dp2_ready(self) -> bool:
        return self.ok and self.data.get("status") == AUTHORIZED_STATUS and not self.blockers

    @property
    def status(self) -> str:
        if not self.ok:
            return "FAIL"
        if self.dp2_ready:
            return AUTHORIZED_STATUS
        return BLOCKED_STATUS

    @property
    def progress_items(self) -> tuple[DpaProgressItem, ...]:
        if not self.ok:
            return ()
        return tuple(_progress_items(self.data))

    @property
    def implementation_percent(self) -> int:
        return sum(item.earned for item in self.progress_items)

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "kind": "dpa_readiness_check",
            "status": self.status,
            "implementation_percent": self.implementation_percent,
            "implementation_scope": IMPLEMENTATION_SCOPE,
            "dp2_implementation_percent": self.implementation_percent,
            "kit_wide_dpa_status": KIT_WIDE_DPA_STATUS,
            "kit_wide_dpa_conformance_claimed": False,
            "progress_model": PROGRESS_MODEL,
            "path": self.path,
            "finding_count": len(self.findings),
            "blocker_count": len(self.blockers),
            "findings": [finding.as_dict() for finding in self.findings],
            "blockers": list(self.blockers),
            "progress": [item.as_dict() for item in self.progress_items],
            "claims": self.data.get("claims", {}),
        }


def evaluate_dpa_readiness(
    root: Path | str = ".",
    *,
    readiness_path: Path | str = DEFAULT_READINESS_PATH,
) -> DpaReadinessResult:
    base = Path(root)
    configured_path = Path(readiness_path)
    path = configured_path if configured_path.is_absolute() else base / configured_path
    display_path = _display_path(path, base)
    findings: list[DpaReadinessFinding] = []

    if not path.exists():
        return DpaReadinessResult(
            path=display_path,
            data={},
            findings=(
                DpaReadinessFinding(
                    code="readiness-record-missing",
                    message="DPA readiness record is missing",
                    path=display_path,
                ),
            ),
            blockers=(),
        )

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return DpaReadinessResult(
            path=display_path,
            data={},
            findings=(
                DpaReadinessFinding(
                    code="readiness-json-invalid",
                    message=f"DPA readiness record is not valid JSON: {exc}",
                    path=display_path,
                ),
            ),
            blockers=(),
        )

    if not isinstance(data, dict):
        findings.append(
            DpaReadinessFinding(
                code="readiness-record-not-object",
                message="DPA readiness record must contain a JSON object",
                path=display_path,
            )
        )
        return DpaReadinessResult(path=display_path, data={}, findings=tuple(findings), blockers=())

    _validate_top_level(data, findings, display_path)
    _validate_claims(data, findings, display_path)
    _validate_probe_family_status(data, findings, display_path)
    _validate_evidence_inputs(data, findings, display_path, base)
    _validate_command_manifest_ack(data, findings, display_path, base)
    blockers = _collect_blockers(data)
    _validate_status_consistency(data, blockers, findings, display_path)

    return DpaReadinessResult(
        path=display_path,
        data=data,
        findings=tuple(findings),
        blockers=tuple(blockers),
    )


def render_dpa_readiness_result(result: DpaReadinessResult) -> str:
    lines = [
        f"DPA readiness: {result.status}",
        f"implementation scope: {IMPLEMENTATION_SCOPE}",
        f"DP2 implementation: {result.implementation_percent}%",
        f"kit-wide DPA: {KIT_WIDE_DPA_STATUS}",
        f"record: {result.path}",
        f"findings: {len(result.findings)}",
        f"blockers: {len(result.blockers)}",
    ]
    if result.findings:
        lines.append("")
        lines.append("Findings:")
        lines.extend(f"- {finding.code}: {finding.message}" for finding in result.findings)
    if result.blockers:
        lines.append("")
        lines.append("DP2 blockers:")
        lines.extend(f"- {blocker}" for blocker in result.blockers)
    if result.progress_items:
        lines.append("")
        lines.append(f"Progress model: {PROGRESS_MODEL}")
        lines.extend(
            f"- {item.id}: {item.earned}/{item.weight} ({item.status})"
            for item in result.progress_items
        )
    if not result.findings and not result.blockers:
        lines.append("")
        lines.append("DP2 authorization evidence is structurally complete.")
    return "\n".join(lines) + "\n"


def _display_path(path: Path, base: Path) -> str:
    try:
        return path.relative_to(base).as_posix()
    except ValueError:
        return path.as_posix()


def _validate_top_level(data: dict[str, Any], findings: list[DpaReadinessFinding], path: str) -> None:
    if data.get("schema_version") != EXPECTED_SCHEMA_VERSION:
        findings.append(
            DpaReadinessFinding(
                code="invalid-schema-version",
                message=f"schema_version must be {EXPECTED_SCHEMA_VERSION}",
                path=path,
            )
        )
    if data.get("kind") != EXPECTED_KIND:
        findings.append(
            DpaReadinessFinding(
                code="invalid-kind",
                message=f"kind must be {EXPECTED_KIND!r}",
                path=path,
            )
        )
    if data.get("status") not in {BLOCKED_STATUS, AUTHORIZED_STATUS}:
        findings.append(
            DpaReadinessFinding(
                code="invalid-status",
                message=f"status must be {BLOCKED_STATUS!r} or {AUTHORIZED_STATUS!r}",
                path=path,
            )
        )


def _validate_claims(data: dict[str, Any], findings: list[DpaReadinessFinding], path: str) -> None:
    claims = data.get("claims")
    if not isinstance(claims, dict):
        findings.append(
            DpaReadinessFinding(code="claims-missing", message="claims must be a mapping", path=path)
        )
        return
    for claim in REQUIRED_FALSE_CLAIMS:
        if claims.get(claim) is not False:
            findings.append(
                DpaReadinessFinding(
                    code="unsafe-claim",
                    message=f"claim {claim!r} must be false in the current DPA readiness record",
                    path=path,
                )
            )
    dp2_authorized = claims.get("dp2_authorized")
    if data.get("status") == AUTHORIZED_STATUS:
        if dp2_authorized is not True:
            findings.append(
                DpaReadinessFinding(
                    code="authorization-claim-missing",
                    message="claim 'dp2_authorized' must be true when status is DP2_AUTHORIZED",
                    path=path,
                )
            )
    elif dp2_authorized is not False:
        findings.append(
            DpaReadinessFinding(
                code="premature-authorization-claim",
                message="claim 'dp2_authorized' must be false unless status is DP2_AUTHORIZED",
                path=path,
            )
        )
    maintainer_authorized = claims.get("maintainer_authorization_recorded")
    if maintainer_authorized is not None:
        if data.get("status") == AUTHORIZED_STATUS and maintainer_authorized is not True:
            findings.append(
                DpaReadinessFinding(
                    code="maintainer-authorization-claim-missing",
                    message="claim 'maintainer_authorization_recorded' must be true when status is DP2_AUTHORIZED",
                    path=path,
                )
            )
        if data.get("status") != AUTHORIZED_STATUS and maintainer_authorized is not False:
            findings.append(
                DpaReadinessFinding(
                    code="premature-maintainer-authorization-claim",
                    message="claim 'maintainer_authorization_recorded' must be false unless status is DP2_AUTHORIZED",
                    path=path,
                )
            )


def _validate_probe_family_status(
    data: dict[str, Any], findings: list[DpaReadinessFinding], path: str
) -> None:
    probe_status = data.get("probe_family_status")
    if not isinstance(probe_status, dict):
        findings.append(
            DpaReadinessFinding(
                code="probe-family-status-missing",
                message="probe_family_status must be a mapping",
                path=path,
            )
        )
        return
    missing = sorted(set(REQUIRED_PROBE_FAMILIES) - set(probe_status))
    for family in missing:
        findings.append(
            DpaReadinessFinding(
                code="probe-family-missing",
                message=f"required Probe family is missing: {family}",
                path=path,
            )
        )


def _validate_evidence_inputs(
    data: dict[str, Any], findings: list[DpaReadinessFinding], path: str, base: Path
) -> None:
    inputs = data.get("evidence_inputs")
    if not isinstance(inputs, list):
        findings.append(
            DpaReadinessFinding(
                code="evidence-inputs-missing",
                message="evidence_inputs must be a list",
                path=path,
            )
        )
        return
    for index, item in enumerate(inputs):
        if not isinstance(item, dict):
            findings.append(
                DpaReadinessFinding(
                    code="evidence-input-invalid",
                    message=f"evidence_inputs[{index}] must be a mapping",
                    path=path,
                )
            )
            continue
        raw_path = item.get("path")
        if not isinstance(raw_path, str) or not raw_path:
            findings.append(
                DpaReadinessFinding(
                    code="evidence-input-path-missing",
                    message=f"evidence_inputs[{index}].path must be a non-empty string",
                    path=path,
                )
            )
            continue
        evidence_path = Path(raw_path)
        if evidence_path.is_absolute():
            findings.append(
                DpaReadinessFinding(
                    code="evidence-input-absolute-path",
                    message=f"evidence input uses an absolute path: {raw_path}",
                    path=path,
                )
            )
            continue
        if not (base / evidence_path).exists():
            findings.append(
                DpaReadinessFinding(
                    code="evidence-input-missing",
                    message=f"evidence input path does not exist: {raw_path}",
                    path=path,
                )
            )


def _validate_command_manifest_ack(
    data: dict[str, Any], findings: list[DpaReadinessFinding], path: str, base: Path
) -> None:
    command_ref = load_workspace(base, suppress_legacy_profile_warning=True).reference_file(
        "agentic-kit-commands.json"
    )
    command_ref_text = _display_path(command_ref, base)
    if not command_ref.exists():
        findings.append(
            DpaReadinessFinding(
                code="command-reference-missing",
                message=f"command reference is missing: {command_ref_text}",
                path=path,
            )
        )
        return
    try:
        command_data = json.loads(command_ref.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        findings.append(
            DpaReadinessFinding(
                code="command-reference-json-invalid",
                message=f"command reference is not valid JSON: {exc}",
                path=path,
            )
        )
        return
    meta = command_data.get("meta")
    manifest_sha = meta.get("manifest_sha") if isinstance(meta, dict) else None
    if not isinstance(manifest_sha, str) or not manifest_sha:
        findings.append(
            DpaReadinessFinding(
                code="command-reference-manifest-sha-missing",
                message="command reference meta.manifest_sha must be a non-empty string",
                path=path,
            )
        )
        return
    expected_ack = f"COMMAND_MANIFEST_ACK {manifest_sha}"
    if data.get("command_manifest_ack") != expected_ack:
        findings.append(
            DpaReadinessFinding(
                code="command-manifest-ack-drift",
                message=f"command_manifest_ack must be {expected_ack!r}",
                path=path,
            )
        )


def _collect_blockers(data: dict[str, Any]) -> list[str]:
    dp2_entry = data.get("dp2_entry_status")
    if not isinstance(dp2_entry, dict):
        return ["dp2_entry_status missing"]
    blockers: list[str] = []
    for requirement, status in dp2_entry.items():
        if status == "BLOCKED":
            blockers.append(requirement)
    return blockers


def _validate_status_consistency(
    data: dict[str, Any],
    blockers: list[str],
    findings: list[DpaReadinessFinding],
    path: str,
) -> None:
    status = data.get("status")
    if status == AUTHORIZED_STATUS and blockers:
        findings.append(
            DpaReadinessFinding(
                code="authorized-with-blockers",
                message="status is DP2_AUTHORIZED while DP2 blockers remain recorded",
                path=path,
            )
        )
    if status == BLOCKED_STATUS and not blockers:
        findings.append(
            DpaReadinessFinding(
                code="blocked-without-blockers",
                message="status is DP2_BLOCKED but no DP2 blockers are recorded",
                path=path,
            )
        )


def _progress_items(data: dict[str, Any]) -> list[DpaProgressItem]:
    dp2_entry = data.get("dp2_entry_status")
    evidence_inputs = data.get("evidence_inputs")
    if not isinstance(dp2_entry, dict):
        dp2_entry = {}
    items: list[DpaProgressItem] = []
    for item_id, label, weight in PROGRESS_WEIGHTS:
        if item_id == "dp1_evidence_staged":
            complete = isinstance(evidence_inputs, list) and bool(evidence_inputs)
            status = "SATISFIED_FOR_STAGING" if complete else "BLOCKED"
        elif item_id == "dp1_readiness_recorded":
            complete = data.get("status") in {BLOCKED_STATUS, AUTHORIZED_STATUS}
            status = str(data.get("status") or "BLOCKED")
        else:
            raw_status = dp2_entry.get(item_id)
            complete = isinstance(raw_status, str) and raw_status != "BLOCKED"
            status = str(raw_status or "BLOCKED")
        items.append(
            DpaProgressItem(
                id=item_id,
                label=label,
                weight=weight,
                earned=weight if complete else 0,
                status=status,
            )
        )
    return items
