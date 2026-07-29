from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import subprocess
from typing import Any

from agentic_project_kit.dpa_readiness import DEFAULT_READINESS_PATH
from agentic_project_kit.workspace import load_workspace

EXPECTED_WRITERS = (
    "WRT-CH-001",
    "WRT-CH-002",
    "WRT-CH-003",
    "WRT-CH-004",
    "WRT-CH-005",
    "WRT-CH-006",
)
PROBE_002_SOURCE_PATHS = (
    "src/agentic_project_kit/doc_lifecycle.py",
    "src/agentic_project_kit/doc_lifecycle_sweep.py",
    "src/agentic_project_kit/cli_commands/docs.py",
    "src/agentic_project_kit/workspace.py",
    "src/agentic_project_kit/workspace_lock.py",
    "src/agentic_project_kit/transfer_repo_actions.py",
    "src/agentic_project_kit/release_prepare.py",
    "src/agentic_project_kit/post_release_closeout.py",
    "src/agentic_project_kit/action_specs.py",
    "src/agentic_project_kit/dpa_workspace_init_projection.py",
    "src/agentic_project_kit/templates.py",
    "src/agentic_project_kit/workspace_init.py",
)
PROBE_002_TEST_GLOBS = (
    "tests/test_doc_lifecycle.py",
    "tests/test_docs_lifecycle_*.py",
    "tests/test_transfer_repo_actions.py",
    "tests/test_release_prepare_command.py",
    "tests/test_release_command_authority.py",
    "tests/test_release_prep_core.py",
    "tests/test_post_release.py",
    "tests/test_post_release_doi_closeout_atomicity.py",
    "tests/test_action_specs.py",
    "tests/test_generator.py",
    "tests/test_workspace_init.py",
)
SELECTED_WRITER_PLAN_PATH = "docs/architecture/dpa/probes/DP1_SELECTED_WRITER_FIXTURE_PLAN_20260727.md"
PROBE_MANUAL_PATH = "docs/architecture/dpa/probes/DP1_PROBE_MANUALS_20260727.md"
PROBE_EXECUTION_PACKAGE_PATH = "docs/architecture/dpa/probes/DP1_PROBE_EXECUTION_PACKAGE_DRAFT_20260727.md"
EVIDENCE_OUTPUT_ROOT_PARTS = ("evidence", "dpa", "probes")

REQUIRED_GROUPS = (
    ("P2-G01", "immutable plan capture", "candidate-preflight"),
    ("P2-G02", "source, target, base, contract, renderer, partition and ownership guards", "candidate-preflight"),
    ("P2-G03", "local Workspace lock and same-process reentrancy rejection", "candidate-preflight"),
    ("P2-G04", "stale-plan rejection before Write and under lock", "candidate-preflight"),
    ("P2-G05", "atomic complete-target or partition-preserving replacement", "candidate-preflight"),
    ("P2-G06", "post-Write verification", "candidate-preflight"),
    ("P2-G07", "acceptance-state creation, tamper detection and scope validation", "candidate-preflight"),
    ("P2-G08", "conditional accepted-base persistence", "candidate-preflight"),
    ("P2-G09", "base-independent post-acceptance evaluation", "candidate-preflight"),
    ("P2-G10", "gate-set re-acceptance without renderer invocation or target mutation", "candidate-preflight"),
    ("P2-G11", "layered acceptance for registered-region projections", "candidate-preflight"),
    ("P2-G12", "lifecycle finding and severity compatibility", "candidate-preflight"),
    ("P2-G13", "every then-known selected writer for selected targets", "selected-writers"),
    ("P2-G14", "explicit out-of-scope adjudication for write-capable paths", "selected-writers"),
)


@dataclass(frozen=True)
class Probe002Finding:
    code: str
    message: str
    path: str

    def as_dict(self) -> dict[str, str]:
        return {"code": self.code, "message": self.message, "path": self.path}


@dataclass(frozen=True)
class Probe002ReadinessResult:
    root: str
    validation_ref: str
    readiness_record: str
    data: dict[str, Any]
    findings: tuple[Probe002Finding, ...]

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
            "kind": "dpa_probe_002_lifecycle_readiness",
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


def evaluate_probe_002_lifecycle_readiness(
    root: Path | str = ".",
    *,
    readiness_path: Path | str = DEFAULT_READINESS_PATH,
    validation_ref: str | None = None,
) -> Probe002ReadinessResult:
    base = Path(root).resolve()
    record_path = _resolve_under_root(base, readiness_path)
    findings: list[Probe002Finding] = []

    source_surfaces = _path_records(base, PROBE_002_SOURCE_PATHS)
    test_surfaces = _glob_records(base, PROBE_002_TEST_GLOBS)
    for item in (*source_surfaces, *test_surfaces):
        if not item["present"]:
            findings.append(
                Probe002Finding(
                    code="required-surface-missing",
                    message=f"Required PROBE-002 surface is missing: {item['path']}",
                    path=item["path"],
                )
            )

    for required_path in (
        SELECTED_WRITER_PLAN_PATH,
        PROBE_MANUAL_PATH,
        PROBE_EXECUTION_PACKAGE_PATH,
    ):
        if not (base / required_path).exists():
            findings.append(
                Probe002Finding(
                    code="required-dpa-control-surface-missing",
                    message=f"Required DPA control surface is missing: {required_path}",
                    path=required_path,
                )
            )

    readiness_data = _load_readiness_data(record_path, base, findings)
    selected_writers = _selected_writer_records(readiness_data)
    missing_writers = sorted(set(EXPECTED_WRITERS) - {item["id"] for item in selected_writers})
    for writer in missing_writers:
        findings.append(
            Probe002Finding(
                code="selected-writer-missing",
                message=f"Selected-writer disposition is missing from readiness record: {writer}",
                path=_display_path(record_path, base),
            )
        )

    blockers = _blockers_for(selected_writers)
    groups = _group_records(blockers)
    validation = validation_ref or _git_head(base)
    data = {
        "source_surfaces": source_surfaces,
        "test_surfaces": test_surfaces,
        "control_surfaces": [
            {"path": SELECTED_WRITER_PLAN_PATH, "present": (base / SELECTED_WRITER_PLAN_PATH).exists()},
            {"path": PROBE_MANUAL_PATH, "present": (base / PROBE_MANUAL_PATH).exists()},
            {
                "path": PROBE_EXECUTION_PACKAGE_PATH,
                "present": (base / PROBE_EXECUTION_PACKAGE_PATH).exists(),
            },
        ],
        "required_groups": groups,
        "selected_writers": selected_writers,
        "blockers": blockers,
        "claims": {
            "probe_execution_claimed": False,
            "dp2_authorized": False,
            "production_mutation_performed": False,
            "generated_outputs_manually_patched": False,
        },
    }
    return Probe002ReadinessResult(
        root=base.as_posix(),
        validation_ref=validation,
        readiness_record=_display_path(record_path, base),
        data=data,
        findings=tuple(findings),
    )


def render_probe_002_lifecycle_readiness(result: Probe002ReadinessResult) -> str:
    payload = result.as_dict()
    lines = [
        "DPA_PROBE_002_READINESS",
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


def write_probe_002_readiness_json(
    result: Probe002ReadinessResult,
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
    findings: list[Probe002Finding],
) -> dict[str, Any]:
    if not path.exists():
        findings.append(
            Probe002Finding(
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
            Probe002Finding(
                code="readiness-record-json-invalid",
                message=f"DPA readiness record is not valid JSON: {exc}",
                path=_display_path(path, root),
            )
        )
        return {}
    if not isinstance(data, dict):
        findings.append(
            Probe002Finding(
                code="readiness-record-not-object",
                message="DPA readiness record must contain a JSON object",
                path=_display_path(path, root),
            )
        )
        return {}
    return data


def _selected_writer_records(readiness_data: dict[str, Any]) -> list[dict[str, str]]:
    raw = readiness_data.get("selected_writer_status")
    if not isinstance(raw, dict):
        return []
    records = []
    for writer_id in EXPECTED_WRITERS:
        status = raw.get(writer_id)
        if isinstance(status, str):
            records.append(
                {
                    "id": writer_id,
                    "status": status,
                    "fixture_status": _fixture_status_for(writer_id, status),
                }
            )
    return records


def _fixture_status_for(writer_id: str, status: str) -> str:
    if writer_id == "WRT-CH-006":
        return "DEFERRED_TO_PROBE_004_GENERATED_OUTPUT_CONTRACT"
    if status == "EXTERNAL_HABITABILITY_ONLY":
        return "OUT_OF_SCOPE_FOR_FIRST_SELF_HOSTING_TARGET"
    if status == "NEEDS_MAINTAINER_DECISION":
        return "BLOCKED_REQUIRES_MAINTAINER_DECISION"
    if status in {"SELECTED_FOR_FIXTURE", "OBSERVED_ADMIN_REFRESH_REQUIRES_DISPOSABLE_FIXTURE"}:
        return "BLOCKED_REQUIRES_CURRENT_DISPOSABLE_FIXTURE_EXECUTION"
    return "BLOCKED_REQUIRES_REVALIDATION"


def _blockers_for(selected_writers: list[dict[str, str]]) -> list[dict[str, str]]:
    blockers: list[dict[str, str]] = []
    selected_fixture_ids = [
        item["id"]
        for item in selected_writers
        if item["fixture_status"] == "BLOCKED_REQUIRES_CURRENT_DISPOSABLE_FIXTURE_EXECUTION"
    ]
    if selected_fixture_ids:
        blockers.append(
            {
                "id": "selected-writer-current-fixtures",
                "message": "Selected writers still require current disposable fixture execution: "
                + ", ".join(selected_fixture_ids),
            }
        )
    maintainer_decision_ids = [
        item["id"]
        for item in selected_writers
        if item["fixture_status"] == "BLOCKED_REQUIRES_MAINTAINER_DECISION"
    ]
    if maintainer_decision_ids:
        blockers.append(
            {
                "id": "selected-writer-maintainer-decisions",
                "message": "Write-capable paths still need Maintainer select/defer decisions: "
                + ", ".join(maintainer_decision_ids),
            }
        )
    blockers.append(
        {
            "id": "probe-002-executable-fixture-run",
            "message": "PROBE-002 has not been executed as a full exact-ref disposable fixture run.",
        }
    )
    return blockers


def _group_records(blockers: list[dict[str, str]]) -> list[dict[str, str]]:
    has_writer_blocker = any(item["id"].startswith("selected-writer") for item in blockers)
    records: list[dict[str, str]] = []
    for group_id, label, category in REQUIRED_GROUPS:
        if category == "selected-writers" and has_writer_blocker:
            status = "BLOCKED_REQUIRES_FIXTURE_OR_ADJUDICATION"
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
