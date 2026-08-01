from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from agentic_project_kit.dpa_dp5_stage_adoption import DEFAULT_DP5_STAGE_RECORD_PATH
from agentic_project_kit.dpa_post_dp2_scope_assessment import (
    evaluate_post_dp2_scope_assessment,
)
from agentic_project_kit.workspace import load_workspace

DEFAULT_DP5_BLOCK_NEW_BASELINE_PATH = Path(
    "docs/architecture/evidence/dpa/assessment/post-dp2-scope-51178821-pre-dp5-block-new-20260801/results.json"
)
EVIDENCE_OUTPUT_ROOT_PARTS = ("evidence", "dpa", "assessment")
PASS_STATUS = "PASS"
BLOCK_STATUS = "BLOCK"


@dataclass(frozen=True)
class Dp5BlockNewFinding:
    code: str
    message: str
    path: str

    def as_dict(self) -> dict[str, str]:
        return {"code": self.code, "message": self.message, "path": self.path}


@dataclass(frozen=True)
class Dp5BlockNewGateResult:
    root: str
    baseline_path: str
    baseline_present: bool
    baseline_validation_ref: str
    baseline_kit_wide_status: str
    current_validation_ref: str
    current_kit_wide_status: str
    active_stage: str
    baseline_noncompliance: tuple[str, ...]
    current_noncompliance: tuple[str, ...]
    new_noncompliance: tuple[str, ...]
    findings: tuple[Dp5BlockNewFinding, ...]

    @property
    def ok(self) -> bool:
        return not self.findings and not self.new_noncompliance

    @property
    def result_status(self) -> str:
        return PASS_STATUS if self.ok else BLOCK_STATUS

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "kind": "dpa_dp5_block_new_gate",
            "result_status": self.result_status,
            "baseline_path": self.baseline_path,
            "baseline_present": self.baseline_present,
            "baseline_validation_ref": self.baseline_validation_ref,
            "baseline_kit_wide_status": self.baseline_kit_wide_status,
            "current_validation_ref": self.current_validation_ref,
            "current_kit_wide_status": self.current_kit_wide_status,
            "active_stage": self.active_stage,
            "baseline_noncompliance_count": len(self.baseline_noncompliance),
            "baseline_noncompliance": list(self.baseline_noncompliance),
            "current_noncompliance_count": len(self.current_noncompliance),
            "current_noncompliance": list(self.current_noncompliance),
            "new_noncompliance_count": len(self.new_noncompliance),
            "new_noncompliance": list(self.new_noncompliance),
            "finding_count": len(self.findings),
            "findings": [finding.as_dict() for finding in self.findings],
            "claims": {
                "blocks_new_noncompliance": self.ok,
                "strict_stage_active": False,
                "kit_wide_dpa_conformance_claimed": False,
                "production_mutation_performed": False,
                "generated_outputs_manually_patched": False,
                "stable_dpa_claimed": False,
            },
        }


def evaluate_dp5_block_new_gate(
    root: Path | str = ".",
    *,
    baseline_path: Path | str = DEFAULT_DP5_BLOCK_NEW_BASELINE_PATH,
    dp5_stage_record_path: Path | str = DEFAULT_DP5_STAGE_RECORD_PATH,
    validation_ref: str | None = None,
) -> Dp5BlockNewGateResult:
    base = Path(root).resolve()
    resolved_baseline = _resolve_under_root(base, baseline_path)
    display_baseline = _display_path(resolved_baseline, base)
    current = evaluate_post_dp2_scope_assessment(
        base,
        dp5_stage_record_path=dp5_stage_record_path,
        validation_ref=validation_ref,
    )
    current_payload = current.as_dict()
    findings = [
        Dp5BlockNewFinding(
            code=f"post-dp2-{finding.code}",
            message=finding.message,
            path=finding.path,
        )
        for finding in current.findings
    ]
    baseline_payload = _load_baseline(resolved_baseline, display_baseline, findings)
    baseline_noncompliance = _noncompliance_from_payload(baseline_payload)
    current_noncompliance = tuple(
        dict.fromkeys(
            [
                *current_payload["dp3"]["blockers"],
                *current_payload["dp4"]["blockers"],
                *current_payload["dp5"]["blockers"],
            ]
        )
    )
    if not current.dp5_stage_record.stage_accepted("block-new"):
        findings.append(
            Dp5BlockNewFinding(
                code="block-new-stage-not-active",
                message="DP5 block-new gate requires an accepted block-new stage record.",
                path=current.dp5_stage_record.record_path,
            )
        )
    if baseline_payload and baseline_payload.get("kit_wide_dpa_status") != "DP5_WARN_ACTIVE_STRICT_NOT_COMPLETE":
        findings.append(
            Dp5BlockNewFinding(
                code="baseline-status-invalid",
                message="block-new baseline must be the accepted DP5 warn-stage assessment.",
                path=display_baseline,
            )
        )
    baseline_set = set(baseline_noncompliance)
    new_noncompliance = tuple(item for item in current_noncompliance if item not in baseline_set)

    return Dp5BlockNewGateResult(
        root=base.as_posix(),
        baseline_path=display_baseline,
        baseline_present=resolved_baseline.exists(),
        baseline_validation_ref=str(baseline_payload.get("validation_ref", "")) if baseline_payload else "",
        baseline_kit_wide_status=str(baseline_payload.get("kit_wide_dpa_status", "")) if baseline_payload else "",
        current_validation_ref=str(current_payload["validation_ref"]),
        current_kit_wide_status=str(current_payload["kit_wide_dpa_status"]),
        active_stage=current.dp5_stage_record.active_stage,
        baseline_noncompliance=baseline_noncompliance,
        current_noncompliance=current_noncompliance,
        new_noncompliance=new_noncompliance,
        findings=tuple(findings),
    )


def render_dp5_block_new_gate(result: Dp5BlockNewGateResult) -> str:
    payload = result.as_dict()
    lines = [
        "DPA_DP5_BLOCK_NEW_GATE",
        f"STATUS={payload['result_status']}",
        f"BASELINE={payload['baseline_path']}",
        f"BASELINE_VALIDATION_REF={payload['baseline_validation_ref']}",
        f"BASELINE_KIT_WIDE_DPA_STATUS={payload['baseline_kit_wide_status']}",
        f"CURRENT_VALIDATION_REF={payload['current_validation_ref']}",
        f"CURRENT_KIT_WIDE_DPA_STATUS={payload['current_kit_wide_status']}",
        f"ACTIVE_STAGE={payload['active_stage']}",
        f"BASELINE_NONCOMPLIANCE={payload['baseline_noncompliance_count']}",
        f"CURRENT_NONCOMPLIANCE={payload['current_noncompliance_count']}",
        f"NEW_NONCOMPLIANCE={payload['new_noncompliance_count']}",
        f"FINDINGS={payload['finding_count']}",
    ]
    for item in payload["new_noncompliance"]:
        lines.append(f"NEW_NONCOMPLIANCE_ITEM={item}")
    for finding in result.findings:
        lines.append(f"FINDING={finding.code}|path={finding.path}|{finding.message}")
    return "\n".join(lines) + "\n"


def write_dp5_block_new_gate_json(
    result: Dp5BlockNewGateResult,
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
            "reason": "output_outside_dpa_assessment_evidence_root",
            "output_path": relative.as_posix(),
            "written": False,
        }
    rendered = json.dumps(result.as_dict(), indent=2, sort_keys=True) + "\n"
    changed = True
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


def _load_baseline(
    baseline: Path,
    display_path: str,
    findings: list[Dp5BlockNewFinding],
) -> dict[str, Any]:
    if not baseline.exists():
        findings.append(
            Dp5BlockNewFinding(
                code="baseline-missing",
                message="block-new gate requires an exact warn-stage baseline assessment.",
                path=display_path,
            )
        )
        return {}
    try:
        data = json.loads(baseline.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        findings.append(
            Dp5BlockNewFinding(
                code="baseline-invalid-json",
                message=f"baseline JSON is invalid: {exc}",
                path=display_path,
            )
        )
        return {}
    if not isinstance(data, dict):
        findings.append(
            Dp5BlockNewFinding(
                code="baseline-invalid",
                message="baseline root must be a JSON object",
                path=display_path,
            )
        )
        return {}
    return data


def _noncompliance_from_payload(payload: dict[str, Any]) -> tuple[str, ...]:
    if not payload:
        return ()
    dp3 = _mapping(payload.get("dp3"))
    dp4 = _mapping(payload.get("dp4"))
    dp5 = _mapping(payload.get("dp5"))
    return tuple(
        dict.fromkeys(
            [
                *_string_list(dp3.get("blockers")),
                *_string_list(dp4.get("blockers")),
                *_string_list(dp5.get("blockers")),
            ]
        )
    )


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str) and item]


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


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


def _evidence_output_root(root: Path) -> Path:
    ws = load_workspace(root, suppress_legacy_profile_warning=True)
    return ws.architecture_file(Path(*EVIDENCE_OUTPUT_ROOT_PARTS)).resolve()
