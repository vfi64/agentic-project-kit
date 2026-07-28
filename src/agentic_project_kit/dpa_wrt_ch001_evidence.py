from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import subprocess
from typing import Any

from agentic_project_kit.workspace import Workspace, load_workspace

EVIDENCE_OUTPUT_ROOT_PARTS = ("evidence", "dpa", "probes")
GH_PR_FIELDS = (
    "number,state,title,baseRefName,headRefName,headRefOid,mergeCommit,files,commits,statusCheckRollup"
)


@dataclass(frozen=True)
class WrtCh001Finding:
    code: str
    message: str
    path: str = "github-pr"

    def as_dict(self) -> dict[str, str]:
        return {"code": self.code, "message": self.message, "path": self.path}


@dataclass(frozen=True)
class WrtCh001EvidenceResult:
    source_pr: int
    admin_pr: int
    data: dict[str, Any]
    findings: tuple[WrtCh001Finding, ...]

    @property
    def structural_ok(self) -> bool:
        return not self.findings

    @property
    def result_status(self) -> str:
        if not self.structural_ok:
            return "STRUCTURAL_BLOCK"
        return "OBSERVED_ADMIN_REFRESH_NOT_DISPOSABLE_FIXTURE"

    @property
    def full_wrt_ch001_fixture_satisfied(self) -> bool:
        return False

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "kind": "dpa_wrt_ch001_admin_refresh_observation",
            "result_status": self.result_status,
            "source_pr": self.source_pr,
            "admin_pr": self.admin_pr,
            "structural_ok": self.structural_ok,
            "full_wrt_ch001_fixture_satisfied": self.full_wrt_ch001_fixture_satisfied,
            "finding_count": len(self.findings),
            "findings": [finding.as_dict() for finding in self.findings],
            **self.data,
        }


def fetch_admin_refresh_pr_data(admin_pr: int, *, root: Path | str = ".") -> dict[str, Any]:
    completed = subprocess.run(
        ["gh", "pr", "view", str(admin_pr), "--json", GH_PR_FIELDS],
        cwd=Path(root),
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    data = json.loads(completed.stdout)
    if not isinstance(data, dict):
        raise ValueError("gh pr view did not return a JSON object")
    return data


def load_pr_data(path: Path | str) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("PR evidence input must contain a JSON object")
    return data


def evaluate_wrt_ch001_admin_refresh_observation(
    root: Path | str,
    *,
    source_pr: int,
    admin_pr: int,
    pr_data: dict[str, Any],
) -> WrtCh001EvidenceResult:
    base = Path(root).resolve()
    ws = load_workspace(base, suppress_legacy_profile_warning=True)
    findings: list[WrtCh001Finding] = []

    expected_head_ref = f"{ws.admin_refresh_branch_prefix()}{source_pr}-handoff-refresh"
    expected_title = f"Refresh handoff state after PR{source_pr}"
    expected_files = _expected_admin_refresh_paths(ws, source_pr)
    observed_files = _observed_file_paths(pr_data)

    _require(pr_data.get("number") == admin_pr, findings, "admin-pr-number-mismatch", f"Expected PR #{admin_pr}.")
    _require(pr_data.get("state") == "MERGED", findings, "admin-pr-not-merged", "Admin refresh PR must be merged.")
    _require(
        pr_data.get("baseRefName") == "main",
        findings,
        "admin-pr-base-not-main",
        "Admin refresh PR base must be main.",
    )
    _require(
        pr_data.get("headRefName") == expected_head_ref,
        findings,
        "admin-pr-head-ref-mismatch",
        f"Admin refresh PR head must be {expected_head_ref}.",
    )
    _require(
        pr_data.get("title") == expected_title,
        findings,
        "admin-pr-title-mismatch",
        f"Admin refresh PR title must be {expected_title}.",
    )

    merge_commit = pr_data.get("mergeCommit")
    merge_oid = merge_commit.get("oid") if isinstance(merge_commit, dict) else None
    _require(isinstance(merge_oid, str) and len(merge_oid) == 40, findings, "merge-commit-missing", "Admin refresh PR must have a merge commit oid.")

    missing_files = sorted(expected_files - observed_files)
    unexpected_files = sorted(observed_files - expected_files)
    for item in missing_files:
        findings.append(
            WrtCh001Finding(
                code="admin-refresh-file-missing",
                message=f"Expected admin refresh file is missing from PR files: {item}",
                path=item,
            )
        )
    for item in unexpected_files:
        findings.append(
            WrtCh001Finding(
                code="admin-refresh-file-unexpected",
                message=f"Unexpected file in admin refresh PR: {item}",
                path=item,
            )
        )

    for item in sorted(expected_files):
        if not (base / item).exists():
            findings.append(
                WrtCh001Finding(
                    code="admin-refresh-file-missing-locally",
                    message=f"Expected merged admin refresh file is missing locally: {item}",
                    path=item,
                )
            )

    check_records = _check_records(pr_data)
    if not check_records:
        findings.append(
            WrtCh001Finding(
                code="admin-refresh-checks-missing",
                message="Admin refresh PR must have at least one status check record.",
            )
        )
    for check in check_records:
        if check["status"] != "COMPLETED" or check["conclusion"] != "SUCCESS":
            findings.append(
                WrtCh001Finding(
                    code="admin-refresh-check-not-successful",
                    message=f"Admin refresh check is not successful: {check['name']}",
                )
            )

    commits = pr_data.get("commits")
    commit_headlines = [
        str(item.get("messageHeadline"))
        for item in commits
        if isinstance(item, dict) and isinstance(item.get("messageHeadline"), str)
    ] if isinstance(commits, list) else []
    _require(
        commit_headlines == [expected_title],
        findings,
        "admin-refresh-commit-shape-mismatch",
        f"Admin refresh PR must contain one commit titled {expected_title}.",
    )

    data = {
        "validation_ref": merge_oid or "UNKNOWN",
        "admin_refresh_head_ref": pr_data.get("headRefName"),
        "admin_refresh_head_oid": pr_data.get("headRefOid"),
        "observed_files": sorted(observed_files),
        "expected_files": sorted(expected_files),
        "status_checks": check_records,
        "commit_headlines": commit_headlines,
        "claims": {
            "admin_refresh_observed": True,
            "disposable_fixture_claimed": False,
            "full_probe_002_claimed": False,
            "dp2_authorized": False,
            "production_mutation_performed_by_this_command": False,
            "generated_outputs_manually_patched": False,
        },
        "limitations": [
            "This observes the merged Kit administrative handoff refresh PR.",
            "It is not a disposable WRT-CH-001 fixture execution.",
            "It does not satisfy full PROBE-002 evidence or authorize DP2.",
        ],
        "raw_pr": pr_data,
    }
    return WrtCh001EvidenceResult(
        source_pr=source_pr,
        admin_pr=admin_pr,
        data=data,
        findings=tuple(findings),
    )


def render_wrt_ch001_evidence(result: WrtCh001EvidenceResult) -> str:
    payload = result.as_dict()
    lines = [
        "DPA_WRT_CH001_ADMIN_REFRESH_OBSERVATION",
        f"STATUS={payload['result_status']}",
        f"SOURCE_PR={payload['source_pr']}",
        f"ADMIN_PR={payload['admin_pr']}",
        f"VALIDATION_REF={payload['validation_ref']}",
        f"FULL_WRT_CH001_FIXTURE_SATISFIED={str(payload['full_wrt_ch001_fixture_satisfied']).lower()}",
        f"FINDINGS={payload['finding_count']}",
    ]
    for finding in payload["findings"]:
        lines.append(f"FINDING={finding['code']}|path={finding['path']}|{finding['message']}")
    return "\n".join(lines) + "\n"


def write_wrt_ch001_evidence_json(
    result: WrtCh001EvidenceResult,
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


def _expected_admin_refresh_paths(ws: Workspace, source_pr: int) -> set[str]:
    paths = {
        ws.handoff_state_path(),
        ws.operational_handoff_state_path(),
        ws.status_path(),
        ws.handoff_file("CURRENT_HANDOFF.md"),
        ws.handoff_file("NEXT_CHAT_BOOTSTRAP.md"),
        ws.handoff_file("START_NEW_CHAT_PROMPT.md"),
        ws.package_file("execution_contract.json"),
        ws.package_file("source_manifest.json"),
        ws.package_file("successor_context.yaml"),
        ws.package_file("successor_prompt.md"),
        ws.package_file("validation_report.json"),
        ws.post_pr_successor_chat_handoff_path(source_pr),
    }
    return {ws.path_text(item) for item in paths}


def _observed_file_paths(pr_data: dict[str, Any]) -> set[str]:
    files = pr_data.get("files")
    if not isinstance(files, list):
        return set()
    return {
        str(item["path"])
        for item in files
        if isinstance(item, dict) and isinstance(item.get("path"), str)
    }


def _check_records(pr_data: dict[str, Any]) -> list[dict[str, str]]:
    checks = pr_data.get("statusCheckRollup")
    if not isinstance(checks, list):
        return []
    records: list[dict[str, str]] = []
    for item in checks:
        if not isinstance(item, dict):
            continue
        records.append(
            {
                "name": str(item.get("name") or ""),
                "status": str(item.get("status") or ""),
                "conclusion": str(item.get("conclusion") or ""),
                "workflowName": str(item.get("workflowName") or ""),
            }
        )
    return records


def _require(condition: bool, findings: list[WrtCh001Finding], code: str, message: str) -> None:
    if not condition:
        findings.append(WrtCh001Finding(code=code, message=message))


def _resolve_under_root(root: Path, path: Path | str) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return root / candidate


def _evidence_output_root(root: Path) -> Path:
    ws = load_workspace(root, suppress_legacy_profile_warning=True)
    return ws.architecture_file(Path(*EVIDENCE_OUTPUT_ROOT_PARTS)).resolve()
