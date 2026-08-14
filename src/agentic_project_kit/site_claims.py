from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import subprocess
import sys
import tomllib
from typing import Any

import yaml

from agentic_project_kit.command_manifest import load_manifest


CLAIM_STATUSES = {"verified", "unverified", "planned"}
FORBIDDEN_STORED_STATUS_FIELDS = {"status", "verified"}
CommandRunner = Callable[[Path, Sequence[str], int], "CommandExecution"]


@dataclass(frozen=True)
class CommandExecution:
    returncode: int
    stdout: str
    stderr: str = ""


@dataclass(frozen=True)
class EvidenceEvaluation:
    evidence_type: str
    status: str
    detail: str

    @property
    def ok(self) -> bool:
        return self.status == "verified"

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class ClaimEvaluation:
    id: str
    text: str
    required: bool
    planned: bool
    status: str
    evidence: tuple[EvidenceEvaluation, ...]
    blockers: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return self.status == "verified" or not self.required

    def as_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "text": self.text,
            "required": self.required,
            "planned": self.planned,
            "status": self.status,
            "evidence": [item.as_dict() for item in self.evidence],
            "blockers": list(self.blockers),
        }


@dataclass(frozen=True)
class ClaimEvaluationReport:
    claims: tuple[ClaimEvaluation, ...]
    schema_blockers: tuple[str, ...]

    @property
    def required_unverified(self) -> tuple[ClaimEvaluation, ...]:
        return tuple(
            claim for claim in self.claims if claim.required and claim.status != "verified"
        )

    @property
    def blockers(self) -> tuple[str, ...]:
        required = tuple(f"required claim is not verified: {claim.id}" for claim in self.required_unverified)
        return (*self.schema_blockers, *required)

    @property
    def ok(self) -> bool:
        return not self.blockers

    @property
    def status(self) -> str:
        return "PASS" if self.ok else "BLOCK"

    def status_counts(self) -> dict[str, int]:
        return {
            status: len([claim for claim in self.claims if claim.status == status])
            for status in sorted(CLAIM_STATUSES)
        }

    def required_counts(self) -> dict[str, int]:
        return {
            "required": len([claim for claim in self.claims if claim.required]),
            "optional": len([claim for claim in self.claims if not claim.required]),
        }

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "kind": "site_claim_evaluation_report",
            "status": self.status,
            "claim_count": len(self.claims),
            "status_counts": self.status_counts(),
            "required_counts": self.required_counts(),
            "blockers": list(self.blockers),
            "schema_blockers": list(self.schema_blockers),
            "claims": [claim.as_dict() for claim in self.claims],
        }


def evaluate_site_claims(
    root: Path = Path("."),
    *,
    claims_path: Path | None = None,
    command_catalog: object | None = None,
    command_runner: CommandRunner | None = None,
) -> ClaimEvaluationReport:
    root = root.resolve()
    path = claims_path or root / "site" / "content" / "claims.yaml"
    if not path.exists():
        return ClaimEvaluationReport(claims=(), schema_blockers=())
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    claim_records = data.get("claims") if isinstance(data, dict) else None
    if not isinstance(claim_records, list):
        return ClaimEvaluationReport(
            claims=(),
            schema_blockers=("site claim file must contain a claims list",),
        )

    schema_blockers: list[str] = []
    claims: list[ClaimEvaluation] = []
    pyproject = _read_pyproject(root)
    manifest = _read_manifest(root)
    runner = command_runner or _run_command
    for index, record in enumerate(claim_records):
        if not isinstance(record, dict):
            schema_blockers.append(f"claim {index} is not an object")
            continue
        claim_id = _string(record.get("id")) or f"claim-{index}"
        forbidden = sorted(FORBIDDEN_STORED_STATUS_FIELDS.intersection(record))
        if forbidden:
            schema_blockers.append(f"{claim_id}: stored derived status fields are forbidden: {', '.join(forbidden)}")
        text = _string(record.get("text"))
        if not text:
            schema_blockers.append(f"{claim_id}: text is missing")
        required = bool(record.get("required"))
        planned = bool(record.get("planned"))
        if required and planned:
            schema_blockers.append(f"{claim_id}: planned claims must not be required")
        evidence_records = _evidence_records(record.get("evidence"))
        evidence = tuple(
            _evaluate_evidence(
                root,
                evidence_record,
                pyproject=pyproject,
                manifest=manifest,
                command_catalog=command_catalog,
                command_runner=runner,
            )
            for evidence_record in evidence_records
        )
        if planned:
            status = "planned"
        elif evidence and all(item.ok for item in evidence):
            status = "verified"
        else:
            status = "unverified"
        blockers = tuple(item.detail for item in evidence if not item.ok)
        claims.append(
            ClaimEvaluation(
                id=claim_id,
                text=text,
                required=required,
                planned=planned,
                status=status,
                evidence=evidence,
                blockers=blockers,
            )
        )
    return ClaimEvaluationReport(claims=tuple(claims), schema_blockers=tuple(schema_blockers))


def _evaluate_evidence(
    root: Path,
    evidence: dict[str, Any],
    *,
    pyproject: dict[str, Any],
    manifest: dict[str, Any],
    command_catalog: object | None,
    command_runner: CommandRunner,
) -> EvidenceEvaluation:
    evidence_type = _string(evidence.get("type"))
    if evidence_type == "pyproject-entrypoint":
        return _evaluate_pyproject_entrypoint(evidence, pyproject)
    if evidence_type == "pyproject-value":
        return _evaluate_pyproject_value(evidence, pyproject)
    if evidence_type == "command-manifest":
        return _evaluate_command_manifest(evidence, manifest)
    if evidence_type == "pytest-node":
        return _evaluate_pytest_node(root, evidence, command_runner)
    if evidence_type == "command-probe":
        return _evaluate_command_probe(root, evidence, command_runner)
    if evidence_type == "file-contains":
        return _evaluate_file_contains(root, evidence)
    if evidence_type == "generated-artifact":
        return _evaluate_generated_artifact(evidence, manifest, command_catalog)
    return EvidenceEvaluation(evidence_type or "<missing>", "unverified", "unsupported evidence type")


def _evaluate_pyproject_entrypoint(
    evidence: dict[str, Any],
    pyproject: dict[str, Any],
) -> EvidenceEvaluation:
    script = _string(evidence.get("script"))
    target = _string(evidence.get("target"))
    scripts = _get_path(pyproject, "project.scripts")
    if not isinstance(scripts, dict):
        return EvidenceEvaluation("pyproject-entrypoint", "unverified", "project.scripts is missing")
    actual = scripts.get(script)
    if not isinstance(actual, str):
        return EvidenceEvaluation("pyproject-entrypoint", "unverified", f"script missing: {script}")
    if target and actual != target:
        return EvidenceEvaluation(
            "pyproject-entrypoint",
            "unverified",
            f"script {script} target mismatch: expected {target}, found {actual}",
        )
    return EvidenceEvaluation("pyproject-entrypoint", "verified", f"{script}={actual}")


def _evaluate_pyproject_value(
    evidence: dict[str, Any],
    pyproject: dict[str, Any],
) -> EvidenceEvaluation:
    key = _string(evidence.get("key"))
    expected = evidence.get("equals")
    actual = _get_path(pyproject, key)
    if actual is None:
        return EvidenceEvaluation("pyproject-value", "unverified", f"pyproject value missing: {key}")
    if "equals" in evidence and actual != expected:
        return EvidenceEvaluation(
            "pyproject-value",
            "unverified",
            f"pyproject value mismatch for {key}: expected {expected!r}, found {actual!r}",
        )
    return EvidenceEvaluation("pyproject-value", "verified", f"{key}={actual}")


def _evaluate_command_manifest(
    evidence: dict[str, Any],
    manifest: dict[str, Any],
) -> EvidenceEvaluation:
    qualified_name = _string(evidence.get("qualified_name"))
    command = _manifest_command(manifest, qualified_name)
    if command is None:
        return EvidenceEvaluation("command-manifest", "unverified", f"command missing: {qualified_name}")
    mismatches: list[str] = []
    for key, expected in evidence.items():
        if key in {"type", "qualified_name"}:
            continue
        if command.get(key) != expected:
            mismatches.append(f"{key}: expected {expected!r}, found {command.get(key)!r}")
    if mismatches:
        return EvidenceEvaluation("command-manifest", "unverified", "; ".join(mismatches))
    return EvidenceEvaluation("command-manifest", "verified", qualified_name)


def _evaluate_pytest_node(
    root: Path,
    evidence: dict[str, Any],
    command_runner: CommandRunner,
) -> EvidenceEvaluation:
    node_id = _string(evidence.get("node_id"))
    timeout = int(evidence.get("timeout_seconds") or 120)
    if not node_id:
        return EvidenceEvaluation("pytest-node", "unverified", "pytest node_id is missing")
    result = command_runner(root, [sys.executable, "-m", "pytest", "-q", node_id], timeout)
    if result.returncode != 0:
        return EvidenceEvaluation("pytest-node", "unverified", f"{node_id} failed")
    return EvidenceEvaluation("pytest-node", "verified", node_id)


def _evaluate_command_probe(
    root: Path,
    evidence: dict[str, Any],
    command_runner: CommandRunner,
) -> EvidenceEvaluation:
    command = evidence.get("command")
    if not isinstance(command, list) or not all(isinstance(item, str) for item in command):
        return EvidenceEvaluation("command-probe", "unverified", "command probe command must be a string list")
    timeout = int(evidence.get("timeout_seconds") or 120)
    result = command_runner(root, _resolved_command(command), timeout)
    if result.returncode != 0:
        return EvidenceEvaluation("command-probe", "unverified", "command probe failed")
    assertion = evidence.get("assertion")
    if isinstance(assertion, dict):
        actual = _json_assertion_value(result.stdout, _string(assertion.get("json_path")))
        expected = assertion.get("equals")
        if actual != expected:
            return EvidenceEvaluation(
                "command-probe",
                "unverified",
                f"assertion mismatch: expected {expected!r}, found {actual!r}",
            )
    return EvidenceEvaluation("command-probe", "verified", " ".join(command))


def _evaluate_file_contains(root: Path, evidence: dict[str, Any]) -> EvidenceEvaluation:
    relative_path = _string(evidence.get("path"))
    needle = _string(evidence.get("contains"))
    if not relative_path:
        return EvidenceEvaluation("file-contains", "unverified", "path is missing")
    if not needle:
        return EvidenceEvaluation("file-contains", "unverified", "contains is missing")
    target = (root / relative_path).resolve()
    try:
        target.relative_to(root)
    except ValueError:
        return EvidenceEvaluation(
            "file-contains",
            "unverified",
            f"path escapes root: {relative_path}",
        )
    if not target.exists():
        return EvidenceEvaluation("file-contains", "unverified", f"file missing: {relative_path}")
    text = target.read_text(encoding="utf-8")
    if needle not in text:
        return EvidenceEvaluation(
            "file-contains",
            "unverified",
            f"file {relative_path} does not contain required text",
        )
    return EvidenceEvaluation("file-contains", "verified", f"{relative_path} contains required text")


def _evaluate_generated_artifact(
    evidence: dict[str, Any],
    manifest: dict[str, Any],
    command_catalog: object | None,
) -> EvidenceEvaluation:
    assertion = _string(evidence.get("assertion"))
    if assertion != "manifest-command-coverage":
        return EvidenceEvaluation("generated-artifact", "unverified", "unsupported generated-artifact assertion")
    commands = manifest.get("commands") if isinstance(manifest.get("commands"), list) else []
    manifest_names = {str(command.get("qualified_name")) for command in commands if isinstance(command, dict)}
    catalog_entries = getattr(command_catalog, "entries", ())
    catalog_names = {str(getattr(entry, "qualified_name", "")) for entry in catalog_entries}
    if not manifest_names:
        return EvidenceEvaluation("generated-artifact", "unverified", "manifest has no commands")
    if catalog_names != manifest_names:
        missing = sorted(manifest_names - catalog_names)
        extra = sorted(catalog_names - manifest_names)
        return EvidenceEvaluation(
            "generated-artifact",
            "unverified",
            f"catalog coverage mismatch: missing={missing[:3]}, extra={extra[:3]}",
        )
    return EvidenceEvaluation("generated-artifact", "verified", f"commands={len(catalog_names)}")


def _evidence_records(raw: object) -> tuple[dict[str, Any], ...]:
    if isinstance(raw, dict):
        return (raw,)
    if isinstance(raw, list):
        return tuple(item for item in raw if isinstance(item, dict))
    return ()


def _read_pyproject(root: Path) -> dict[str, Any]:
    path = root / "pyproject.toml"
    if not path.exists():
        return {}
    return tomllib.loads(path.read_text(encoding="utf-8"))


def _read_manifest(root: Path) -> dict[str, Any]:
    try:
        return load_manifest(root)
    except Exception:
        return {}


def _manifest_command(manifest: dict[str, Any], qualified_name: str) -> dict[str, Any] | None:
    commands = manifest.get("commands")
    if not isinstance(commands, list):
        return None
    for command in commands:
        if isinstance(command, dict) and command.get("qualified_name") == qualified_name:
            return command
    return None


def _get_path(data: dict[str, Any], dotted: str) -> Any:
    current: Any = data
    for part in dotted.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def _json_assertion_value(stdout: str, path: str) -> object:
    data = json.loads(stdout)
    if not path.startswith("$."):
        return None
    current: object = data
    for part in path[2:].split("."):
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return current


def _resolved_command(command: Sequence[str]) -> list[str]:
    if command and command[0] == "agentic-kit":
        return [sys.executable, "-m", "agentic_project_kit.cli", *command[1:]]
    if command and command[0] == "python":
        return [sys.executable, *command[1:]]
    return list(command)


def _run_command(root: Path, command: Sequence[str], timeout: int) -> CommandExecution:
    completed = subprocess.run(
        list(command),
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )
    return CommandExecution(completed.returncode, completed.stdout, completed.stderr)


def _string(value: object) -> str:
    return value if isinstance(value, str) else ""
