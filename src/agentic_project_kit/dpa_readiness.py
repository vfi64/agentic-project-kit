from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

DEFAULT_READINESS_PATH = Path(
    "docs/architecture/evidence/dpa/assessment/dp1-assessment-readiness-20260728.json"
)
EXPECTED_KIND = "dpa_dp1_assessment_readiness"
EXPECTED_SCHEMA_VERSION = 1
BLOCKED_STATUS = "DP2_BLOCKED"
AUTHORIZED_STATUS = "DP2_AUTHORIZED"
REQUIRED_PROBE_FAMILIES = ("PROBE-001", "PROBE-002", "RENDERER", "PROBE-003", "PROBE-004")
REQUIRED_FALSE_CLAIMS = (
    "full_probe_pass_claimed",
    "dp2_authorized",
    "runtime_behavior_changed",
    "production_mutation_performed",
    "kit_conformance_claimed",
    "generated_outputs_manually_patched",
)


@dataclass(frozen=True)
class DpaReadinessFinding:
    code: str
    message: str
    path: str = DEFAULT_READINESS_PATH.as_posix()

    def as_dict(self) -> dict[str, str]:
        return {"code": self.code, "message": self.message, "path": self.path}


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

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "kind": "dpa_readiness_check",
            "status": self.status,
            "path": self.path,
            "finding_count": len(self.findings),
            "blocker_count": len(self.blockers),
            "findings": [finding.as_dict() for finding in self.findings],
            "blockers": list(self.blockers),
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
