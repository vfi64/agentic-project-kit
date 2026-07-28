from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import subprocess
from typing import Any, Callable, Iterable

from agentic_project_kit.workspace import load_workspace

DEFAULT_FIXTURE_MANIFEST_PATH = Path(
    "docs/architecture/dpa/probes/fixtures/DP1_PROBE_FIXTURE_MANIFEST_20260727.json"
)
EVIDENCE_OUTPUT_ROOT_PARTS = ("evidence", "dpa", "probes")
READ_ONLY_SCOPE = "READ_ONLY"
NOT_REQUIRED_AUTHORIZATION = "NOT_REQUIRED"


@dataclass(frozen=True)
class ReadonlyProbeFinding:
    code: str
    message: str
    path: str

    def as_dict(self) -> dict[str, str]:
        return {"code": self.code, "message": self.message, "path": self.path}


@dataclass(frozen=True)
class CommandExecution:
    argv: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str
    timed_out: bool = False

    @property
    def ok(self) -> bool:
        return self.returncode == 0 and not self.timed_out

    def as_dict(self) -> dict[str, Any]:
        return {
            "argv": list(self.argv),
            "returncode": self.returncode,
            "ok": self.ok,
            "timed_out": self.timed_out,
            "stdout_summary": _truncate(self.stdout),
            "stderr_summary": _truncate(self.stderr),
        }


@dataclass(frozen=True)
class ReadonlyProbeExecutionResult:
    root: str
    validation_ref: str
    fixture_manifest: str
    plan_only: bool
    data: dict[str, Any]
    findings: tuple[ReadonlyProbeFinding, ...]

    @property
    def structural_ok(self) -> bool:
        return not self.findings

    @property
    def command_failures(self) -> tuple[dict[str, Any], ...]:
        failures: list[dict[str, Any]] = []
        for family in self.data.get("families", ()):
            for case in family.get("cases", ()):
                if case.get("result_status") == "FAIL":
                    failures.append(case)
        return tuple(failures)

    @property
    def blocked_cases(self) -> tuple[dict[str, Any], ...]:
        blocked: list[dict[str, Any]] = []
        for family in self.data.get("families", ()):
            for case in family.get("cases", ()):
                if str(case.get("result_status", "")).startswith("BLOCKED"):
                    blocked.append(case)
        return tuple(blocked)

    @property
    def result_status(self) -> str:
        if not self.structural_ok:
            return "STRUCTURAL_BLOCK"
        if self.command_failures:
            return "READ_ONLY_FAIL"
        if self.plan_only:
            return "READ_ONLY_PLAN_ONLY"
        return "READ_ONLY_EXECUTED_WITH_LIMITATIONS"

    @property
    def full_probe_pass_satisfied(self) -> bool:
        return False

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "kind": "dpa_readonly_probe_execution",
            "result_status": self.result_status,
            "validation_ref": self.validation_ref,
            "fixture_manifest": self.fixture_manifest,
            "structural_ok": self.structural_ok,
            "plan_only": self.plan_only,
            "full_probe_pass_satisfied": self.full_probe_pass_satisfied,
            "finding_count": len(self.findings),
            "command_failure_count": len(self.command_failures),
            "blocked_case_count": len(self.blocked_cases),
            "findings": [finding.as_dict() for finding in self.findings],
            **self.data,
        }


CommandRunner = Callable[[Path, tuple[str, ...], int], CommandExecution]


def evaluate_dpa_readonly_probe_execution(
    root: Path | str = ".",
    *,
    fixture_manifest_path: Path | str = DEFAULT_FIXTURE_MANIFEST_PATH,
    validation_ref: str | None = None,
    plan_only: bool = False,
    timeout_seconds: int = 180,
    command_runner: CommandRunner | None = None,
) -> ReadonlyProbeExecutionResult:
    base = Path(root).resolve()
    manifest_path = _resolve_under_root(base, fixture_manifest_path)
    findings: list[ReadonlyProbeFinding] = []
    manifest = _load_manifest(manifest_path, base, findings)
    resolved_validation_ref = validation_ref or _git_head(base)

    families: list[dict[str, Any]] = []
    selected_readonly = 0
    executed_readonly = 0
    blocked_mutating = 0
    blocked_context = 0

    for raw_family in _families(manifest, manifest_path, base, findings):
        family_id = str(raw_family.get("id", "UNKNOWN"))
        family_cases: list[dict[str, Any]] = []
        for raw_case in _cases(raw_family, manifest_path, base, findings):
            record = _case_record(raw_case)
            case_id = record["id"]
            mutation_scope = record["mutation_scope"]
            authorization = record["authorization"]

            if mutation_scope != READ_ONLY_SCOPE or authorization != NOT_REQUIRED_AUTHORIZATION:
                record.update(
                    {
                        "selected_for_readonly_execution": False,
                        "result_status": "BLOCKED_PENDING_MAINTAINER_AUTHORIZATION",
                        "blocker": "mutable_or_authorized_fixture_not_executed",
                        "commands": [],
                    }
                )
                blocked_mutating += 1
                family_cases.append(record)
                continue

            selected_readonly += 1
            commands, context_blocker = _commands_for_case(case_id)
            record["selected_for_readonly_execution"] = True
            if context_blocker is not None:
                record.update(
                    {
                        "result_status": "BLOCKED_PENDING_CONTEXT",
                        "blocker": context_blocker,
                        "commands": [],
                    }
                )
                blocked_context += 1
                family_cases.append(record)
                continue

            record["commands"] = [list(command) for command in commands]
            if plan_only:
                record["result_status"] = "PLANNED_READ_ONLY_NOT_EXECUTED"
                family_cases.append(record)
                continue

            runner = command_runner or _run_command
            command_records = [runner(base, command, timeout_seconds) for command in commands]
            executed_readonly += 1
            record["command_results"] = [item.as_dict() for item in command_records]
            record["result_status"] = "PASS" if all(item.ok for item in command_records) else "FAIL"
            family_cases.append(record)

        families.append(
            {
                "id": family_id,
                "title": raw_family.get("title"),
                "cases": family_cases,
            }
        )

    data = {
        "families": families,
        "summary": {
            "readonly_cases_selected": selected_readonly,
            "readonly_cases_executed": executed_readonly,
            "mutable_or_authorized_cases_blocked": blocked_mutating,
            "context_dependent_readonly_cases_blocked": blocked_context,
        },
        "claims": {
            "full_probe_pass_claimed": False,
            "dp2_authorized": False,
            "production_mutation_performed": False,
            "generated_outputs_manually_patched": False,
            "renderer_conformance_claimed": False,
            "workflow_queue_conformance_claimed": False,
        },
        "limitations": [
            "Only READ_ONLY fixtures with NOT_REQUIRED authorization are eligible for this wrapper.",
            "Mutable, disposable-branch and temp-repository fixtures remain blocked pending Maintainer authorization.",
            "This command does not satisfy full PROBE-002, Renderer, PROBE-003 or PROBE-004 evidence.",
            "This command does not authorize DP2 implementation or claim Kit DPA conformance.",
        ],
    }
    return ReadonlyProbeExecutionResult(
        root=base.as_posix(),
        validation_ref=resolved_validation_ref,
        fixture_manifest=_display_path(manifest_path, base),
        plan_only=plan_only,
        data=data,
        findings=tuple(findings),
    )


def render_dpa_readonly_probe_execution(result: ReadonlyProbeExecutionResult) -> str:
    payload = result.as_dict()
    lines = [
        "DPA_READONLY_PROBE_EXECUTION",
        f"STATUS={payload['result_status']}",
        f"VALIDATION_REF={payload['validation_ref']}",
        f"PLAN_ONLY={str(payload['plan_only']).lower()}",
        f"FULL_PROBE_PASS_SATISFIED={str(payload['full_probe_pass_satisfied']).lower()}",
        f"READONLY_CASES_SELECTED={payload['summary']['readonly_cases_selected']}",
        f"READONLY_CASES_EXECUTED={payload['summary']['readonly_cases_executed']}",
        f"BLOCKED_CASES={payload['blocked_case_count']}",
        f"FINDINGS={payload['finding_count']}",
    ]
    for failure in result.command_failures:
        lines.append(f"COMMAND_FAILURE={failure['id']}|{failure['title']}")
    for blocked in result.blocked_cases:
        lines.append(f"BLOCKED_CASE={blocked['id']}|{blocked.get('blocker', 'blocked')}")
    for finding in payload["findings"]:
        lines.append(f"FINDING={finding['code']}|path={finding['path']}|{finding['message']}")
    return "\n".join(lines) + "\n"


def write_dpa_readonly_probe_execution_json(
    result: ReadonlyProbeExecutionResult,
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


def _commands_for_case(case_id: str) -> tuple[tuple[tuple[str, ...], ...], str | None]:
    commands: dict[str, tuple[tuple[str, ...], ...]] = {
        "P001-REG-001": (
            (".venv/bin/agentic-kit", "docs-registry"),
            (".venv/bin/agentic-kit", "doc-registry", "check-unregistered", "--json"),
            (
                ".venv/bin/python",
                "-m",
                "pytest",
                "-q",
                "tests/test_documentation_registry.py",
                "tests/test_doc_mesh.py",
            ),
        ),
        "P002-WRT-004": (
            (".venv/bin/agentic-kit", "actions", "list"),
            (".venv/bin/python", "-m", "pytest", "-q", "tests/test_action_specs.py"),
        ),
        "P002-WRT-006": (
            (".venv/bin/agentic-kit", "handoff", "check"),
            (".venv/bin/python", "-m", "pytest", "-q", "tests/test_successor_handoff_package.py"),
        ),
        "P003-WF-001": (
            ("git", "branch", "--show-current"),
            ("git", "rev-parse", "HEAD"),
            ("git", "status", "--short"),
            (".venv/bin/agentic-kit", "transfer", "repo-status", "--json"),
            (".venv/bin/agentic-kit", "transfer", "divergence-status", "--json"),
        ),
        "P004-MIG-001": (
            (".venv/bin/agentic-kit", "handoff", "check"),
            (".venv/bin/agentic-kit", "dpa", "readiness", "--json"),
        ),
    }
    context_blockers = {
        "REN-001": "approved_dpa_renderer_map_missing",
        "REN-002": "approved_dpa_renderer_map_missing",
        "P003-WF-003": "target_pr_context_required",
        "P003-WF-004": "integration_ref_context_required",
    }
    if case_id in context_blockers:
        return (), context_blockers[case_id]
    return commands.get(case_id, ()), None if case_id in commands else "readonly_case_runner_not_defined"


def _run_command(root: Path, argv: tuple[str, ...], timeout_seconds: int) -> CommandExecution:
    try:
        completed = subprocess.run(
            list(argv),
            cwd=root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return CommandExecution(
            argv=argv,
            returncode=124,
            stdout=exc.stdout or "",
            stderr=exc.stderr or "",
            timed_out=True,
        )
    return CommandExecution(
        argv=argv,
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )


def _load_manifest(path: Path, root: Path, findings: list[ReadonlyProbeFinding]) -> dict[str, Any]:
    if not path.exists():
        findings.append(
            ReadonlyProbeFinding(
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
            ReadonlyProbeFinding(
                code="fixture-manifest-json-invalid",
                message=f"DPA Probe fixture manifest is not valid JSON: {exc}",
                path=_display_path(path, root),
            )
        )
        return {}
    if not isinstance(data, dict):
        findings.append(
            ReadonlyProbeFinding(
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
    findings: list[ReadonlyProbeFinding],
) -> Iterable[dict[str, Any]]:
    raw = manifest.get("families", [])
    if not isinstance(raw, list):
        findings.append(
            ReadonlyProbeFinding(
                code="fixture-manifest-families-invalid",
                message="DPA Probe fixture manifest families must be a list",
                path=_display_path(manifest_path, root),
            )
        )
        return ()
    families: list[dict[str, Any]] = []
    for index, family in enumerate(raw):
        if not isinstance(family, dict):
            findings.append(
                ReadonlyProbeFinding(
                    code="fixture-manifest-family-invalid",
                    message=f"DPA Probe fixture manifest family at index {index} must be an object",
                    path=_display_path(manifest_path, root),
                )
            )
            continue
        families.append(family)
    return tuple(families)


def _cases(
    family: dict[str, Any],
    manifest_path: Path,
    root: Path,
    findings: list[ReadonlyProbeFinding],
) -> Iterable[dict[str, Any]]:
    raw = family.get("cases", [])
    if not isinstance(raw, list):
        findings.append(
            ReadonlyProbeFinding(
                code="fixture-manifest-cases-invalid",
                message=f"DPA Probe fixture manifest cases for {family.get('id', 'UNKNOWN')} must be a list",
                path=_display_path(manifest_path, root),
            )
        )
        return ()
    cases: list[dict[str, Any]] = []
    for index, case in enumerate(raw):
        if not isinstance(case, dict):
            findings.append(
                ReadonlyProbeFinding(
                    code="fixture-manifest-case-invalid",
                    message=f"DPA Probe fixture manifest case at index {index} must be an object",
                    path=_display_path(manifest_path, root),
                )
            )
            continue
        cases.append(case)
    return tuple(cases)


def _case_record(raw_case: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(raw_case.get("id", "UNKNOWN")),
        "title": str(raw_case.get("title", "")),
        "mutation_scope": str(raw_case.get("mutation_scope", "")),
        "authorization": str(raw_case.get("authorization", "")),
        "cleanup_plan_id": str(raw_case.get("cleanup_plan_id", "")),
        "expected_result": str(raw_case.get("expected_result", "")),
        "writer_id": raw_case.get("writer_id"),
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
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if completed.returncode == 0:
        return completed.stdout.strip()
    return "UNKNOWN"


def _truncate(value: str, *, limit: int = 4000) -> str:
    if len(value) <= limit:
        return value
    return value[:limit] + "\n...[truncated]"
