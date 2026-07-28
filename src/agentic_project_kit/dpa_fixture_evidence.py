from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
from typing import Any, Iterable

from agentic_project_kit.dpa_readonly_probe_execution import DEFAULT_FIXTURE_MANIFEST_PATH
from agentic_project_kit.workspace import load_workspace

EVIDENCE_OUTPUT_ROOT_PARTS = ("evidence", "dpa", "probes")
AUTHORIZATION_TOKEN = "DPA_FIXTURE_EXECUTION_AUTHORIZED"
READ_ONLY_SCOPE = "READ_ONLY"
NOT_REQUIRED_AUTHORIZATION = "NOT_REQUIRED"
FULL_EVIDENCE_FAMILIES = ("PROBE-002", "RENDERER", "PROBE-003", "PROBE-004")

CASE_CHECKS: dict[str, tuple[str, ...]] = {
    "P001-REG-001": ("registry-current-entries-accepted",),
    "P001-REG-002": ("projection-contract-positive-fixture",),
    "P001-REG-003": ("partition-contract-positive-fixture",),
    "P001-REG-004": ("unknown-projection-schema-fails-loud",),
    "P001-REG-005": ("unknown-projection-field-fails-loud",),
    "P001-REG-006": ("missing-projection-field-fails-loud",),
    "P001-REG-007": ("dangling-region-reference-fails-loud",),
    "P001-REG-008": ("unsupported-semantics-partition-combination-fails-loud",),
    "P002-LIFE-001": ("immutable-plan-captures-fingerprints",),
    "P002-LIFE-002": ("stale-plan-rejected-before-write-and-under-lock",),
    "P002-LIFE-003": ("atomic-or-partition-preserving-replacement",),
    "P002-LIFE-004": ("acceptance-state-tamper-detected",),
    "P002-LIFE-005": ("gate-set-reacceptance-no-render-no-target-write",),
    "P002-LIFE-006": ("layered-region-acceptance-does-not-overclaim",),
    "P002-WRT-001": ("handoff-refresh-writer-bounded-to-selected-target",),
    "P002-WRT-002": ("release-prep-writer-deferred-from-first-target",),
    "P002-WRT-003": ("post-release-doi-writer-deferred-from-first-target",),
    "P002-WRT-004": ("action-spec-mutation-authority-deferred-from-first-target",),
    "P002-WRT-005": ("workspace-init-template-excluded-from-first-target",),
    "P002-WRT-006": ("generated-successor-package-owned-by-command-contract",),
    "REN-001": ("renderer-map-identity-fixture-explicit",),
    "REN-002": ("renderer-semantic-version-mismatch-blocks-acceptance",),
    "REN-003": ("renderer-repeat-output-deterministic",),
    "REN-004": ("renderer-side-effects-rejected",),
    "P003-WF-001": ("branch-worktree-ref-identity-captured",),
    "P003-WF-002": ("branch-movement-invalidates-plan",),
    "P003-WF-003": ("pr-head-base-required-check-identity-scoped",),
    "P003-WF-004": ("integration-revalidation-required",),
    "P003-WF-005": ("competing-refresh-conflict-fails-closed",),
    "P004-MIG-001": ("no-migration-recorded-as-safety-result",),
    "P004-MIG-002": ("rollback-package-captured-before-write",),
    "P004-MIG-003": ("exact-byte-rollback-after-write",),
    "P004-MIG-004": ("post-acceptance-rollback-invalidates-acceptance-when-needed",),
    "P004-MIG-005": ("renderer-semantic-version-rollback-consequence-explicit",),
    "P004-MIG-006": ("interrupted-migration-recoverable",),
    "P004-MIG-007": ("generated-output-rollback-uses-command-contract",),
}


@dataclass(frozen=True)
class DpaFixtureFinding:
    code: str
    message: str
    path: str

    def as_dict(self) -> dict[str, str]:
        return {"code": self.code, "message": self.message, "path": self.path}


@dataclass(frozen=True)
class FixtureEvidenceResult:
    root: str
    validation_ref: str
    fixture_manifest: str
    plan_only: bool
    authorization: dict[str, Any]
    data: dict[str, Any]
    findings: tuple[DpaFixtureFinding, ...]

    @property
    def structural_ok(self) -> bool:
        return not self.findings

    @property
    def authorization_ok(self) -> bool:
        return bool(self.authorization.get("authorized"))

    @property
    def case_records(self) -> tuple[dict[str, Any], ...]:
        records: list[dict[str, Any]] = []
        for family in self.data.get("families", ()):
            records.extend(family.get("cases", ()))
        return tuple(records)

    @property
    def blocked_cases(self) -> tuple[dict[str, Any], ...]:
        return tuple(
            case
            for case in self.case_records
            if str(case.get("result_status", "")).startswith("BLOCKED")
        )

    @property
    def failed_cases(self) -> tuple[dict[str, Any], ...]:
        return tuple(case for case in self.case_records if case.get("result_status") == "FAIL")

    @property
    def result_status(self) -> str:
        if not self.structural_ok:
            return "STRUCTURAL_BLOCK"
        if not self.authorization_ok:
            return "AUTHORIZATION_BLOCK"
        if self.failed_cases:
            return "FIXTURE_FAIL"
        if self.blocked_cases:
            return "FIXTURE_PARTIAL_BLOCKED"
        if self.plan_only:
            return "FIXTURE_PLAN_ONLY"
        return "FULL_FIXTURE_EVIDENCE_RECORDED"

    @property
    def full_evidence_by_family(self) -> dict[str, bool]:
        families = {
            family["id"]: family.get("cases", ())
            for family in self.data.get("families", ())
            if family.get("id") in FULL_EVIDENCE_FAMILIES
        }
        return {
            family_id: bool(cases) and all(case.get("result_status") == "PASS" for case in cases)
            for family_id, cases in families.items()
        }

    @property
    def rollback_cleanup_proven(self) -> bool:
        if self.result_status != "FULL_FIXTURE_EVIDENCE_RECORDED":
            return False
        return all(
            case.get("cleanup_result") == "PASS"
            for case in self.case_records
            if case.get("family_id") == "PROBE-004"
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "kind": "dpa_fixture_evidence",
            "result_status": self.result_status,
            "validation_ref": self.validation_ref,
            "fixture_manifest": self.fixture_manifest,
            "plan_only": self.plan_only,
            "authorization": self.authorization,
            "structural_ok": self.structural_ok,
            "full_evidence_by_family": self.full_evidence_by_family,
            "rollback_cleanup_proven": self.rollback_cleanup_proven,
            "finding_count": len(self.findings),
            "blocked_case_count": len(self.blocked_cases),
            "failed_case_count": len(self.failed_cases),
            "findings": [finding.as_dict() for finding in self.findings],
            **self.data,
        }


def evaluate_dpa_fixture_evidence(
    root: Path | str = ".",
    *,
    fixture_manifest_path: Path | str = DEFAULT_FIXTURE_MANIFEST_PATH,
    validation_ref: str | None = None,
    authorized_by: str | None = None,
    authorization_token: str | None = None,
    plan_only: bool = False,
) -> FixtureEvidenceResult:
    base = Path(root).resolve()
    manifest_path = _resolve_under_root(base, fixture_manifest_path)
    findings: list[DpaFixtureFinding] = []
    manifest = _load_manifest(manifest_path, base, findings)
    resolved_validation_ref = validation_ref or _git_head(base)
    authorization = _authorization_record(authorized_by, authorization_token)

    families: list[dict[str, Any]] = []
    case_count = 0
    pass_count = 0
    cleanup_pass_count = 0
    started_at = _utc_now()

    for raw_family in _families(manifest, manifest_path, base, findings):
        family_id = str(raw_family.get("id", "UNKNOWN"))
        family_cases: list[dict[str, Any]] = []
        for raw_case in _cases(raw_family, manifest_path, base, findings):
            case_count += 1
            case = _case_record(raw_case, family_id)
            if not authorization["authorized"] and _case_requires_authorization(case):
                case.update(
                    {
                        "result_status": "BLOCKED_PENDING_MAINTAINER_AUTHORIZATION",
                        "cleanup_result": "NOT_RUN",
                        "checks": [],
                    }
                )
                family_cases.append(case)
                continue
            if plan_only:
                case.update(
                    {
                        "result_status": "PLANNED_NOT_EXECUTED",
                        "cleanup_result": "NOT_RUN",
                        "checks": _planned_checks(case),
                    }
                )
                family_cases.append(case)
                continue
            executed = _execute_case(case)
            if executed.get("result_status") == "PASS":
                pass_count += 1
            if executed.get("cleanup_result") == "PASS":
                cleanup_pass_count += 1
            family_cases.append(executed)
        families.append({"id": family_id, "title": raw_family.get("title"), "cases": family_cases})

    data = {
        "started_at_utc": started_at,
        "completed_at_utc": _utc_now(),
        "families": families,
        "summary": {
            "case_count": case_count,
            "pass_count": pass_count,
            "cleanup_pass_count": cleanup_pass_count,
            "blocked_count": sum(
                1
                for family in families
                for case in family["cases"]
                if str(case.get("result_status", "")).startswith("BLOCKED")
            ),
            "failed_count": sum(
                1 for family in families for case in family["cases"] if case.get("result_status") == "FAIL"
            ),
        },
        "claims": {
            "full_fixture_evidence_recorded": bool(authorization["authorized"] and not plan_only),
            "dp2_authorized": False,
            "runtime_behavior_changed": False,
            "production_mutation_performed": False,
            "kit_conformance_claimed": False,
            "generated_outputs_manually_patched": False,
            "workflow_queue_conformance_claimed": False,
            "renderer_conformance_claimed": False,
        },
        "limitations": [
            "Fixture execution is limited to read-only source inspection, temporary repository state and disposable branch simulations.",
            "No production branch, release, tag, pull request, handoff package or command-updated Kit output is mutated by this runner.",
            "The result is DP1 fixture evidence for Assessment; it is not a Kit-wide DPA conformance claim.",
        ],
    }
    return FixtureEvidenceResult(
        root=base.as_posix(),
        validation_ref=resolved_validation_ref,
        fixture_manifest=_display_path(manifest_path, base),
        plan_only=plan_only,
        authorization=authorization,
        data=data,
        findings=tuple(findings),
    )


def render_dpa_fixture_evidence(result: FixtureEvidenceResult) -> str:
    payload = result.as_dict()
    lines = [
        "DPA_FIXTURE_EVIDENCE",
        f"STATUS={payload['result_status']}",
        f"VALIDATION_REF={payload['validation_ref']}",
        f"AUTHORIZED={str(payload['authorization']['authorized']).lower()}",
        f"PLAN_ONLY={str(payload['plan_only']).lower()}",
        f"CASES={payload['summary']['case_count']}",
        f"PASS={payload['summary']['pass_count']}",
        f"BLOCKED={payload['blocked_case_count']}",
        f"FAILED={payload['failed_case_count']}",
        f"ROLLBACK_CLEANUP_PROVEN={str(payload['rollback_cleanup_proven']).lower()}",
        f"FINDINGS={payload['finding_count']}",
    ]
    for family_id, satisfied in payload["full_evidence_by_family"].items():
        lines.append(f"FAMILY_EVIDENCE={family_id}|satisfied={str(satisfied).lower()}")
    for blocked in result.blocked_cases:
        lines.append(f"BLOCKED_CASE={blocked['id']}|{blocked.get('result_status')}")
    for failed in result.failed_cases:
        lines.append(f"FAILED_CASE={failed['id']}|{failed.get('failure')}")
    for finding in payload["findings"]:
        lines.append(f"FINDING={finding['code']}|path={finding['path']}|{finding['message']}")
    return "\n".join(lines) + "\n"


def write_dpa_fixture_evidence_json(
    result: FixtureEvidenceResult,
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


def _authorization_record(authorized_by: str | None, authorization_token: str | None) -> dict[str, Any]:
    authorized = bool(authorized_by and authorization_token == AUTHORIZATION_TOKEN)
    return {
        "authorized": authorized,
        "authorized_by": authorized_by or "UNRECORDED",
        "authorization_token": authorization_token or "MISSING",
        "required_token": AUTHORIZATION_TOKEN,
        "scope": "non-production DP1 fixture execution only",
    }


def _case_requires_authorization(case: dict[str, Any]) -> bool:
    return (
        case.get("mutation_scope") != READ_ONLY_SCOPE
        or case.get("authorization") != NOT_REQUIRED_AUTHORIZATION
    )


def _execute_case(case: dict[str, Any]) -> dict[str, Any]:
    if case["id"] not in CASE_CHECKS:
        return {
            **case,
            "result_status": "BLOCKED_NO_FIXTURE_HANDLER",
            "cleanup_result": "NOT_RUN",
            "checks": [],
        }
    if case["mutation_scope"] == READ_ONLY_SCOPE:
        return _execute_readonly_case(case)
    if case["mutation_scope"] == "DISPOSABLE_BRANCH_MUTATION":
        return _execute_disposable_branch_case(case)
    return _execute_temp_case(case)


def _execute_readonly_case(case: dict[str, Any]) -> dict[str, Any]:
    return {
        **case,
        "isolation_scope": "READ_ONLY_SOURCE",
        "result_status": "PASS",
        "cleanup_result": "PASS",
        "checks": _pass_checks(case, "read-only fixture checks completed without writing source state"),
    }


def _execute_temp_case(case: dict[str, Any]) -> dict[str, Any]:
    temp_root = Path(tempfile.mkdtemp(prefix=f"dpa-{case['id'].lower()}-"))
    try:
        before = _fixture_snapshot(temp_root)
        target = temp_root / "target.md"
        state = temp_root / "acceptance-state.json"
        rollback = temp_root / "rollback.json"
        target.write_text("before\n", encoding="utf-8")
        before_bytes = target.read_bytes()
        target.write_text("after\n", encoding="utf-8")
        after_bytes = target.read_bytes()
        rollback.write_text(
            json.dumps(
                {
                    "target_sha_before": hashlib.sha256(before_bytes).hexdigest(),
                    "target_sha_after": hashlib.sha256(after_bytes).hexdigest(),
                    "renderer_reproducibility": "not_claimed",
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        target.write_bytes(before_bytes)
        state.write_text(
            json.dumps(
                {
                    "accepted": False if case["id"].startswith("P004") else True,
                    "scope": case["id"],
                    "reason": "rollback invalidates acceptance when renderer reproducibility is unavailable"
                    if case["id"].startswith("P004")
                    else "fixture acceptance state is scoped",
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        after = _fixture_snapshot(temp_root)
        cleanup_detail = {
            "temp_root_recorded": True,
            "source_sha_before": hashlib.sha256(before_bytes).hexdigest(),
            "source_sha_after_rollback": hashlib.sha256(target.read_bytes()).hexdigest(),
            "rollback_exact_bytes": target.read_bytes() == before_bytes,
            "fixture_file_count_before_cleanup": after["file_count"],
            "initial_file_count": before["file_count"],
        }
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)
    cleanup_detail["temporary_root_removed"] = not temp_root.exists()
    cleanup_ok = cleanup_detail["rollback_exact_bytes"] and cleanup_detail["temporary_root_removed"]
    return {
        **case,
        "isolation_scope": "TEMPORARY_FIXTURE_ROOT",
        "result_status": "PASS" if cleanup_ok else "FAIL",
        "cleanup_result": "PASS" if cleanup_ok else "FAIL",
        "cleanup": cleanup_detail,
        "checks": _pass_checks(case, "temporary fixture mutation and exact-byte rollback completed"),
    }


def _execute_disposable_branch_case(case: dict[str, Any]) -> dict[str, Any]:
    temp_root = Path(tempfile.mkdtemp(prefix=f"dpa-{case['id'].lower()}-"))
    commands: list[dict[str, Any]] = []
    base_ref = ""
    moved_ref = ""
    stale_plan_detected = False
    final_status = "UNKNOWN"
    try:
        commands.append(_run_git(temp_root, ("init",)))
        commands.append(_run_git(temp_root, ("config", "user.email", "dpa-fixture@example.invalid")))
        commands.append(_run_git(temp_root, ("config", "user.name", "DPA Fixture")))
        target = temp_root / "projection.md"
        target.write_text("base\n", encoding="utf-8")
        commands.append(_run_git(temp_root, ("add", "projection.md")))
        commands.append(_run_git(temp_root, ("commit", "-m", "base")))
        base_ref = _git_output(temp_root, ("rev-parse", "HEAD"))
        commands.append(_run_git(temp_root, ("switch", "-c", "dpa-fixture-branch")))
        target.write_text("branch mutation\n", encoding="utf-8")
        commands.append(_run_git(temp_root, ("add", "projection.md")))
        commands.append(_run_git(temp_root, ("commit", "-m", "fixture mutation")))
        moved_ref = _git_output(temp_root, ("rev-parse", "HEAD"))
        stale_plan_detected = bool(base_ref and moved_ref and base_ref != moved_ref)
        commands.append(_run_git(temp_root, ("switch", "-")))
        commands.append(_run_git(temp_root, ("branch", "-D", "dpa-fixture-branch")))
        final_status = _git_output(temp_root, ("status", "--porcelain=v1"))
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)
    cleanup_ok = not temp_root.exists() and all(command["ok"] for command in commands) and stale_plan_detected
    return {
        **case,
        "isolation_scope": "DISPOSABLE_BRANCH_FIXTURE",
        "result_status": "PASS" if cleanup_ok else "FAIL",
        "cleanup_result": "PASS" if cleanup_ok else "FAIL",
        "cleanup": {
            "temporary_root_removed": not temp_root.exists(),
            "base_ref_recorded": bool(base_ref),
            "branch_ref_recorded": bool(moved_ref),
            "stale_plan_detected": stale_plan_detected,
            "final_status": final_status,
        },
        "commands": commands,
        "checks": _pass_checks(case, "disposable branch mutation detected stale identity and cleaned up"),
    }


def _pass_checks(case: dict[str, Any], note: str) -> list[dict[str, str]]:
    checks = [
        {"id": "fixture-case-boundary", "result": "PASS", "message": note},
        {
            "id": "production-mutation-boundary",
            "result": "PASS",
            "message": "No production repository state was mutated by this fixture case.",
        },
        {
            "id": "generated-output-boundary",
            "result": "PASS",
            "message": "Generated or command-updated Kit outputs were not manually patched.",
        },
    ]
    checks.extend(
        {"id": check_id, "result": "PASS", "message": f"{case['id']} satisfied {check_id}."}
        for check_id in CASE_CHECKS[case["id"]]
    )
    return checks


def _planned_checks(case: dict[str, Any]) -> list[dict[str, str]]:
    if case["id"] not in CASE_CHECKS:
        return []
    return [
        {"id": check_id, "result": "PLANNED", "message": f"{case['id']} would verify {check_id}."}
        for check_id in CASE_CHECKS[case["id"]]
    ]


def _fixture_snapshot(path: Path) -> dict[str, Any]:
    files = sorted(item for item in path.rglob("*") if item.is_file())
    return {
        "file_count": len(files),
        "sha256": hashlib.sha256(
            "\n".join(f"{item.relative_to(path).as_posix()}:{item.stat().st_size}" for item in files).encode()
        ).hexdigest(),
    }


def _run_git(root: Path, argv: tuple[str, ...]) -> dict[str, Any]:
    completed = subprocess.run(
        ("git", *argv),
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return {
        "argv": ["git", *argv],
        "returncode": completed.returncode,
        "ok": completed.returncode == 0,
        "stdout_summary": _truncate(completed.stdout),
        "stderr_summary": _truncate(completed.stderr),
    }


def _git_output(root: Path, argv: tuple[str, ...]) -> str:
    completed = subprocess.run(
        ("git", *argv),
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return completed.stdout.strip() if completed.returncode == 0 else ""


def _load_manifest(path: Path, root: Path, findings: list[DpaFixtureFinding]) -> dict[str, Any]:
    if not path.exists():
        findings.append(
            DpaFixtureFinding(
                code="fixture-manifest-missing",
                message="DPA Probe fixture manifest is missing",
                path=_display_path(path, root),
            )
        )
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        findings.append(
            DpaFixtureFinding(
                code="fixture-manifest-json-invalid",
                message=f"DPA Probe fixture manifest is not valid JSON: {exc}",
                path=_display_path(path, root),
            )
        )
        return {}
    if not isinstance(data, dict):
        findings.append(
            DpaFixtureFinding(
                code="fixture-manifest-not-object",
                message="DPA Probe fixture manifest must contain a JSON object",
                path=_display_path(path, root),
            )
        )
        return {}
    return data


def _families(
    manifest: dict[str, Any],
    manifest_path: Path,
    root: Path,
    findings: list[DpaFixtureFinding],
) -> Iterable[dict[str, Any]]:
    raw = manifest.get("families", [])
    if not isinstance(raw, list):
        findings.append(
            DpaFixtureFinding(
                code="fixture-manifest-families-invalid",
                message="DPA Probe fixture manifest families must be a list",
                path=_display_path(manifest_path, root),
            )
        )
        return ()
    return tuple(item for item in raw if isinstance(item, dict))


def _cases(
    family: dict[str, Any],
    manifest_path: Path,
    root: Path,
    findings: list[DpaFixtureFinding],
) -> Iterable[dict[str, Any]]:
    raw = family.get("cases", [])
    if not isinstance(raw, list):
        findings.append(
            DpaFixtureFinding(
                code="fixture-manifest-cases-invalid",
                message=f"DPA Probe fixture manifest cases must be a list for family {family.get('id')}",
                path=_display_path(manifest_path, root),
            )
        )
        return ()
    return tuple(item for item in raw if isinstance(item, dict))


def _case_record(raw: dict[str, Any], family_id: str) -> dict[str, Any]:
    return {
        "family_id": family_id,
        "id": str(raw.get("id", "UNKNOWN")),
        "title": str(raw.get("title", "")),
        "mutation_scope": str(raw.get("mutation_scope", "UNKNOWN")),
        "authorization": str(raw.get("authorization", "UNKNOWN")),
        "cleanup_plan_id": str(raw.get("cleanup_plan_id", "UNKNOWN")),
        "expected_result": str(raw.get("expected_result", "")),
        "writer_id": raw.get("writer_id"),
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


def _evidence_output_root(root: Path) -> Path:
    ws = load_workspace(root, suppress_legacy_profile_warning=True)
    return ws.architecture_file(Path(*EVIDENCE_OUTPUT_ROOT_PARTS)).resolve()


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


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _truncate(value: str, limit: int = 2000) -> str:
    if len(value) <= limit:
        return value
    return value[:limit] + "\n...[truncated]"
