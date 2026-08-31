from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
from typing import Any

from agentic_project_kit.dpa_readiness import DEFAULT_READINESS_PATH, evaluate_dpa_readiness
from agentic_project_kit.operational_handoff_projection import (
    ensure_generated_operational_handoff_block,
    render_current_operational_handoff_state,
)
from agentic_project_kit.safe_file_replace import safe_replace
from agentic_project_kit.workspace import LEGACY_DEFAULTS, load_workspace
from agentic_project_kit.workspace_lock import WorkspaceLockBusy, workspace_mutation_lock

DEFAULT_ACCEPTANCE_STATE_PATH = Path(LEGACY_DEFAULTS.agentic_root) / LEGACY_DEFAULTS.dpa_current_handoff_acceptance_state_file
DEFAULT_CURRENT_HANDOFF_FILENAME = "CURRENT_HANDOFF.md"

CONTRACT_ID = "DPA-CURRENT-HANDOFF-OPERATIONAL-STATE-v1"
GATE_SET_ID = "dpa-current-handoff-minimal-gate-set-v1"
RENDERER_ID = "agentic_project_kit.operational_handoff_projection"
RENDERER_SEMANTIC_VERSION = "1"
TARGET_SCOPE = "CURRENT_HANDOFF_OPERATIONAL_STATE_BLOCK"
WRITER_ID = "WRT-CH-001"

OPERATIONAL_REFRESH_MARKER_PATTERN = re.compile(
    r"\n## Operational documentation refresh state after PR #\d+\n\n"
    r"Current administrative handoff refresh state is `[^`]+` \(`[^`]*`\)\. "
    r"Continue next only after this post-PR\d+ refresh is committed and merged; "
    r"the next substantive slice must be created from fresh main\.\n?",
    flags=re.MULTILINE,
)


@dataclass(frozen=True)
class DpaCurrentHandoffFinding:
    code: str
    severity: str
    message: str
    path: str = ""

    def as_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class DpaCurrentHandoffPlan:
    branch: str
    validation_ref: str
    target_path: str
    source_path: str
    acceptance_state_path: str
    target_before_fingerprint: str
    source_fingerprint: str
    projected_payload_fingerprint: str
    projected_complete_target_fingerprint: str
    would_change_target: bool
    prior_acceptance_status: str
    freshness: str

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class DpaCurrentHandoffResult:
    result_status: str
    execute: bool
    initialized_acceptance: bool
    wrote_target: bool
    wrote_acceptance_state: bool
    plan: DpaCurrentHandoffPlan
    findings: tuple[DpaCurrentHandoffFinding, ...] = field(default_factory=tuple)
    acceptance_state: dict[str, Any] | None = None

    @property
    def ok(self) -> bool:
        return not any(item.severity == "BLOCKER" for item in self.findings)

    def as_dict(self) -> dict[str, object]:
        payload = {
            "schema_version": 1,
            "kind": "dpa_current_handoff_lifecycle_result",
            "result_status": self.result_status,
            "execute": self.execute,
            "initialized_acceptance": self.initialized_acceptance,
            "wrote_target": self.wrote_target,
            "wrote_acceptance_state": self.wrote_acceptance_state,
            "plan": self.plan.as_dict(),
            "finding_count": len(self.findings),
            "findings": [item.as_dict() for item in self.findings],
            "claims": {
                "acceptance_state_recorded": self.wrote_acceptance_state,
                "production_mutation_performed": False,
                "kit_conformance_claimed": False,
                "generated_outputs_manually_patched": False,
            },
        }
        if self.acceptance_state is not None:
            payload["acceptance_state"] = self.acceptance_state
        return payload


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read_bytes(path: Path) -> bytes:
    return path.read_bytes() if path.exists() else b""


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _repo_rel(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _resolve(root: Path, path: Path) -> Path:
    return path if path.is_absolute() else root / path


def _git(root: Path, args: list[str]) -> str:
    completed = subprocess.run(["git", *args], cwd=root, text=True, capture_output=True, check=False)
    if completed.returncode != 0:
        return "UNKNOWN"
    return completed.stdout.strip() or "UNKNOWN"


def _git_path_is_clean(root: Path, rel_path: str) -> bool:
    for args in (
        ["diff", "--quiet", "--", rel_path],
        ["diff", "--cached", "--quiet", "--", rel_path],
    ):
        completed = subprocess.run(["git", *args], cwd=root, text=True, capture_output=True, check=False)
        if completed.returncode != 0:
            return False
    return True


def _load_acceptance_state(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"acceptance state is not valid JSON: {exc}") from exc
    if not isinstance(loaded, dict):
        raise ValueError("acceptance state must be a JSON object")
    return loaded


def _write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    safe_replace(path, tmp)


def _write_text_atomic(path: Path, text: str) -> None:
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    safe_replace(path, tmp)


def _render_target_text(root: Path, target_path: Path, source_path: Path) -> str:
    current = _read_text(target_path).replace("\\n", "\n")
    current = OPERATIONAL_REFRESH_MARKER_PATTERN.sub("", current).rstrip() + "\n"
    return ensure_generated_operational_handoff_block(
        current,
        render_current_operational_handoff_state(root, path=source_path),
    )


def _build_acceptance_state(
    *,
    plan: DpaCurrentHandoffPlan,
    target_text: str,
    branch: str,
    validation_ref: str,
    contract_id: str = CONTRACT_ID,
    target_scope: str = TARGET_SCOPE,
    writer_id: str = WRITER_ID,
    renderer_id: str = RENDERER_ID,
    renderer_semantic_version: str = RENDERER_SEMANTIC_VERSION,
) -> dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    return {
        "schema_version": 1,
        "kind": "dpa_acceptance_state",
        "status": "accepted",
        "accepted_at": now,
        "accepted_lifecycle_outcome": "accepted",
        "accepted_gate_result": "pass",
        "accepted_gate_set_id": GATE_SET_ID,
        "branch": branch,
        "validation_ref": validation_ref,
        "contract_id": contract_id,
        "target_scope": target_scope,
        "writer_id": writer_id,
        "renderer": {
            "id": renderer_id,
            "semantic_version": renderer_semantic_version,
        },
        "source": {
            "path": plan.source_path,
            "fingerprint": plan.source_fingerprint,
        },
        "target": {
            "path": plan.target_path,
            "complete_target_fingerprint": _sha256_bytes(target_text.encode("utf-8")),
            "payload_fingerprint": plan.projected_payload_fingerprint,
            "pre_write_fingerprint": plan.target_before_fingerprint,
        },
        "claims": {
            "production_mutation_performed": False,
            "kit_conformance_claimed": False,
            "generated_outputs_manually_patched": False,
        },
    }


def _acceptance_finding(
    code: str,
    message: str,
    *,
    path: Path | None = None,
    root: Path | None = None,
) -> DpaCurrentHandoffFinding:
    rel = _repo_rel(root, path) if path is not None and root is not None else ""
    return DpaCurrentHandoffFinding(code=code, severity="BLOCKER", message=message, path=rel)


def evaluate_current_handoff_lifecycle(
    root: Path | str = ".",
    *,
    target_path: Path | None = None,
    acceptance_state_path: Path | None = None,
    readiness_path: Path = DEFAULT_READINESS_PATH,
    validation_ref: str | None = None,
    execute: bool = False,
    initialize_acceptance: bool = False,
    require_dp2_authorized: bool = True,
    allow_committed_target_drift: bool = False,
) -> DpaCurrentHandoffResult:
    resolved_root = Path(root).resolve()
    workspace = load_workspace(resolved_root)
    target = _resolve(resolved_root, target_path) if target_path is not None else workspace.handoff_file(DEFAULT_CURRENT_HANDOFF_FILENAME)
    source = workspace.operational_handoff_state_path()

    try:
        projected_text = _render_target_text(resolved_root, target, source)
    except (OSError, ValueError) as exc:
        projected_text = _read_text(target)
        preflight_findings = (_acceptance_finding("render-failed", str(exc), path=target, root=resolved_root),)
    else:
        preflight_findings = ()

    return evaluate_current_handoff_text_lifecycle(
        resolved_root,
        target_path=target,
        acceptance_state_path=acceptance_state_path,
        readiness_path=readiness_path,
        validation_ref=validation_ref,
        execute=execute,
        initialize_acceptance=initialize_acceptance,
        require_dp2_authorized=require_dp2_authorized,
        allow_committed_target_drift=allow_committed_target_drift,
        projected_text=projected_text,
        source_path=source,
        writer_id=WRITER_ID,
        renderer_id=RENDERER_ID,
        renderer_semantic_version=RENDERER_SEMANTIC_VERSION,
        contract_id=CONTRACT_ID,
        target_scope=TARGET_SCOPE,
        lock_command="dpa current-handoff-refresh",
        preflight_findings=preflight_findings,
    )


def evaluate_current_handoff_text_lifecycle(
    root: Path | str = ".",
    *,
    projected_text: str,
    writer_id: str,
    renderer_id: str,
    renderer_semantic_version: str = RENDERER_SEMANTIC_VERSION,
    contract_id: str = CONTRACT_ID,
    target_scope: str = TARGET_SCOPE,
    source_path: Path | str | None = None,
    source_fingerprint: str | None = None,
    target_path: Path | None = None,
    acceptance_state_path: Path | None = None,
    readiness_path: Path = DEFAULT_READINESS_PATH,
    validation_ref: str | None = None,
    execute: bool = False,
    initialize_acceptance: bool = False,
    require_dp2_authorized: bool = True,
    allow_committed_target_drift: bool = False,
    lock_command: str = "dpa current-handoff-lifecycle",
    preflight_findings: tuple[DpaCurrentHandoffFinding, ...] = (),
) -> DpaCurrentHandoffResult:
    resolved_root = Path(root).resolve()
    workspace = load_workspace(resolved_root)
    target = _resolve(resolved_root, target_path) if target_path is not None else workspace.handoff_file(DEFAULT_CURRENT_HANDOFF_FILENAME)
    acceptance_path = (
        _resolve(resolved_root, acceptance_state_path)
        if acceptance_state_path is not None
        else workspace.dpa_current_handoff_acceptance_state_path()
    )
    target_rel = _repo_rel(resolved_root, target)
    acceptance_rel = _repo_rel(resolved_root, acceptance_path)
    source_file: Path | None = None
    if source_fingerprint is None:
        if source_path is None:
            raise ValueError("source_path or source_fingerprint is required")
        source_file = _resolve(resolved_root, Path(source_path))
        source_rel = _repo_rel(resolved_root, source_file)
        source_fingerprint = _sha256_bytes(_read_bytes(source_file))
    else:
        source_rel = str(source_path or "<declared-inputs>")

    findings: list[DpaCurrentHandoffFinding] = list(preflight_findings)
    branch = _git(resolved_root, ["branch", "--show-current"])
    current_head = _git(resolved_root, ["rev-parse", "HEAD"])
    effective_ref = validation_ref or current_head

    if validation_ref and current_head != "UNKNOWN" and validation_ref != current_head:
        findings.append(
            _acceptance_finding(
                "stale-validation-ref",
                "validation_ref does not match the current repository HEAD",
                path=target,
                root=resolved_root,
            )
        )

    if require_dp2_authorized:
        readiness = evaluate_dpa_readiness(resolved_root, readiness_path=readiness_path)
        if not readiness.ok or not readiness.dp2_ready:
            findings.append(
                _acceptance_finding(
                    "dp2-not-authorized",
                    "DPA readiness record does not structurally authorize DP2 for this target scope",
                    path=readiness_path,
                    root=resolved_root,
                )
            )

    try:
        previous_acceptance = _load_acceptance_state(acceptance_path)
    except ValueError as exc:
        previous_acceptance = None
        findings.append(_acceptance_finding("acceptance-state-invalid", str(exc), path=acceptance_path, root=resolved_root))

    target_bytes = _read_bytes(target)
    target_before = _sha256_bytes(target_bytes)
    projected_fingerprint = _sha256_bytes(projected_text.encode("utf-8"))
    would_change = target_bytes != projected_text.encode("utf-8")

    prior_status = "missing" if previous_acceptance is None else str(previous_acceptance.get("status") or "unknown")
    freshness = "indeterminate"
    if previous_acceptance is None:
        if not initialize_acceptance:
            findings.append(
                _acceptance_finding(
                    "acceptance-state-missing",
                    "No DPA acceptance-state record exists; pass --initialize-acceptance for the first accepted CURRENT_HANDOFF projection",
                    path=acceptance_path,
                    root=resolved_root,
                )
            )
    else:
        accepted_target = str((previous_acceptance.get("target") or {}).get("complete_target_fingerprint") or "")
        accepted_source = str((previous_acceptance.get("source") or {}).get("fingerprint") or "")
        accepted_source_path = str((previous_acceptance.get("source") or {}).get("path") or "")
        accepted_target_path = str((previous_acceptance.get("target") or {}).get("path") or "")
        if accepted_target_path != target_rel:
            findings.append(
                _acceptance_finding(
                    "acceptance-state-scope-mismatch",
                    f"Acceptance-state target path is {accepted_target_path!r}, expected {target_rel!r}",
                    path=acceptance_path,
                    root=resolved_root,
                )
            )
        elif accepted_target != target_before:
            if allow_committed_target_drift and _git_path_is_clean(resolved_root, target_rel):
                freshness = "stale"
            else:
                findings.append(
                    _acceptance_finding(
                        "target-drift",
                        "Current target bytes differ from the accepted complete-target fingerprint",
                        path=target,
                        root=resolved_root,
                    )
                )
                freshness = "stale"
        elif would_change:
            freshness = "stale"
        elif accepted_source_path == source_rel and accepted_source == source_fingerprint:
            freshness = "fresh"
        else:
            freshness = "fresh"

    plan = DpaCurrentHandoffPlan(
        branch=branch,
        validation_ref=effective_ref,
        target_path=target_rel,
        source_path=source_rel,
        acceptance_state_path=acceptance_rel,
        target_before_fingerprint=target_before,
        source_fingerprint=source_fingerprint,
        projected_payload_fingerprint=projected_fingerprint,
        projected_complete_target_fingerprint=projected_fingerprint,
        would_change_target=would_change,
        prior_acceptance_status=prior_status,
        freshness=freshness,
    )

    if findings:
        return DpaCurrentHandoffResult(
            result_status="BLOCKED",
            execute=execute,
            initialized_acceptance=initialize_acceptance and previous_acceptance is None,
            wrote_target=False,
            wrote_acceptance_state=False,
            plan=plan,
            findings=tuple(findings),
        )

    if not execute:
        status = "FRESH" if freshness == "fresh" else "WOULD_ACCEPT_INITIAL" if previous_acceptance is None else "WOULD_REFRESH"
        return DpaCurrentHandoffResult(
            result_status=status,
            execute=False,
            initialized_acceptance=initialize_acceptance and previous_acceptance is None,
            wrote_target=False,
            wrote_acceptance_state=False,
            plan=plan,
        )

    try:
        with workspace_mutation_lock(resolved_root, lock_command):
            lock_head = _git(resolved_root, ["rev-parse", "HEAD"])
            if current_head != "UNKNOWN" and lock_head != current_head:
                findings.append(
                    _acceptance_finding(
                        "under-lock-head-changed",
                        "Repository HEAD changed between preflight and under-lock revalidation",
                        path=target,
                        root=resolved_root,
                    )
                )
            if _sha256_bytes(_read_bytes(target)) != target_before:
                findings.append(
                    _acceptance_finding(
                        "under-lock-target-changed",
                        "Target bytes changed between preflight and under-lock revalidation",
                        path=target,
                        root=resolved_root,
                    )
                )
            if source_file is not None and _sha256_bytes(_read_bytes(source_file)) != source_fingerprint:
                findings.append(
                    _acceptance_finding(
                        "under-lock-source-changed",
                        "Source bytes changed between preflight and under-lock revalidation",
                        path=source_file,
                        root=resolved_root,
                    )
                )
            if findings:
                return DpaCurrentHandoffResult(
                    result_status="BLOCKED",
                    execute=True,
                    initialized_acceptance=initialize_acceptance and previous_acceptance is None,
                    wrote_target=False,
                    wrote_acceptance_state=False,
                    plan=plan,
                    findings=tuple(findings),
                )

            _write_text_atomic(target, projected_text)
            if _sha256_bytes(_read_bytes(target)) != projected_fingerprint:
                findings.append(
                    _acceptance_finding(
                        "post-write-verification-failed",
                        "Target bytes after Write do not match the projected output fingerprint",
                        path=target,
                        root=resolved_root,
                    )
                )
                return DpaCurrentHandoffResult(
                    result_status="BLOCKED",
                    execute=True,
                    initialized_acceptance=initialize_acceptance and previous_acceptance is None,
                    wrote_target=True,
                    wrote_acceptance_state=False,
                    plan=plan,
                    findings=tuple(findings),
                )

            acceptance = _build_acceptance_state(
                plan=plan,
                target_text=projected_text,
                branch=branch,
                validation_ref=effective_ref,
                contract_id=contract_id,
                target_scope=target_scope,
                writer_id=writer_id,
                renderer_id=renderer_id,
                renderer_semantic_version=renderer_semantic_version,
            )
            _write_json_atomic(acceptance_path, acceptance)
    except WorkspaceLockBusy as exc:
        findings.append(_acceptance_finding("workspace-lock-busy", str(exc), path=target, root=resolved_root))
        return DpaCurrentHandoffResult(
            result_status="BLOCKED",
            execute=True,
            initialized_acceptance=initialize_acceptance and previous_acceptance is None,
            wrote_target=False,
            wrote_acceptance_state=False,
            plan=plan,
            findings=tuple(findings),
        )

    return DpaCurrentHandoffResult(
        result_status="ACCEPTED",
        execute=True,
        initialized_acceptance=initialize_acceptance and previous_acceptance is None,
        wrote_target=True,
        wrote_acceptance_state=True,
        plan=plan,
        acceptance_state=acceptance,
    )


def render_current_handoff_lifecycle_result(result: DpaCurrentHandoffResult) -> str:
    lines = [
        "DPA_CURRENT_HANDOFF_LIFECYCLE",
        f"STATUS={result.result_status}",
        f"TARGET={result.plan.target_path}",
        f"ACCEPTANCE_STATE={result.plan.acceptance_state_path}",
        f"VALIDATION_REF={result.plan.validation_ref}",
        f"FRESHNESS={result.plan.freshness}",
        f"WOULD_CHANGE_TARGET={str(result.plan.would_change_target).lower()}",
        f"EXECUTE={str(result.execute).lower()}",
        f"WROTE_TARGET={str(result.wrote_target).lower()}",
        f"WROTE_ACCEPTANCE_STATE={str(result.wrote_acceptance_state).lower()}",
        f"FINDINGS={len(result.findings)}",
    ]
    for finding in result.findings:
        path = f" path={finding.path}" if finding.path else ""
        lines.append(f"- {finding.severity} {finding.code}:{path} {finding.message}")
    return "\n".join(lines) + "\n"
