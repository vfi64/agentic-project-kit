from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any

from agentic_project_kit.chat_entrypoint_contract import (
    COMMAND_REFERENCE_JSON,
    COMMAND_REFERENCE_MARKDOWN,
    command_manifest_ack_line,
    load_command_manifest,
    mandatory_entrypoint_line,
)

TEXT_COMMAND_AUTHORITY_SURFACES: tuple[str, ...] = (
    "AGENTS.md",
    "docs/handoff/START_NEW_CHAT_PROMPT.md",
    "docs/handoff/NEXT_CHAT_BOOTSTRAP.md",
    "docs/handoff/CLOSEOUT_BEFORE_CHAT_SWITCH_PROMPT.md",
    "docs/reports/handoff-packages/latest/successor_prompt.md",
)

EXECUTION_CONTRACT_SURFACE = "docs/reports/handoff-packages/latest/execution_contract.json"


@dataclass(frozen=True)
class CommandAuthorityFinding:
    severity: str
    code: str
    path: str
    message: str

    def as_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class CommandAuthorityAudit:
    root: str
    manifest_sha: str
    findings: tuple[CommandAuthorityFinding, ...]

    @property
    def blockers(self) -> tuple[CommandAuthorityFinding, ...]:
        return tuple(finding for finding in self.findings if finding.severity == "BLOCK")

    @property
    def ok(self) -> bool:
        return not self.blockers

    @property
    def status(self) -> str:
        return "PASS" if self.ok else "BLOCK"

    @property
    def returncode(self) -> int:
        return 0 if self.ok else 2

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "kind": "command_authority_audit",
            "root": self.root,
            "manifest_sha": self.manifest_sha,
            "status": self.status,
            "finding_count": len(self.findings),
            "blocker_count": len(self.blockers),
            "findings": [finding.as_dict() for finding in self.findings],
        }


def _manifest_sha(manifest: dict[str, Any]) -> str:
    meta = manifest.get("meta") if isinstance(manifest.get("meta"), dict) else {}
    return str(meta.get("manifest_sha") or "UNKNOWN")


def _finding(code: str, path: str, message: str) -> CommandAuthorityFinding:
    return CommandAuthorityFinding("BLOCK", code, path, message)


def _required_text_terms(path: str, manifest: dict[str, Any]) -> tuple[str, ...]:
    ack = command_manifest_ack_line(manifest)
    if path == "AGENTS.md":
        return (
            mandatory_entrypoint_line(manifest),
            "agentic-kit command-for",
            ack,
        )
    return (
        ack,
        COMMAND_REFERENCE_JSON,
        COMMAND_REFERENCE_MARKDOWN,
        "agentic-kit command-for",
        "must_not_reconstruct_commands_from_memory",
        "most specific available Kit workflow command",
        "raw git/gh commands with a mapped wrapper are rejected by instruction lint",
    )


def _audit_text_surface(root: Path, path: str, manifest: dict[str, Any]) -> list[CommandAuthorityFinding]:
    target = root / path
    if not target.exists():
        return [_finding("COMMAND_AUTHORITY_SURFACE_MISSING", path, "required command authority surface is missing")]
    text = target.read_text(encoding="utf-8")
    findings: list[CommandAuthorityFinding] = []
    for term in _required_text_terms(path, manifest):
        if term not in text:
            findings.append(
                _finding(
                    "COMMAND_AUTHORITY_TERM_MISSING",
                    path,
                    f"required command authority term is missing: {term}",
                )
            )
    return findings


def _audit_execution_contract(root: Path, manifest: dict[str, Any]) -> list[CommandAuthorityFinding]:
    path = EXECUTION_CONTRACT_SURFACE
    target = root / path
    if not target.exists():
        return [_finding("COMMAND_AUTHORITY_SURFACE_MISSING", path, "execution contract is missing")]
    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [_finding("COMMAND_AUTHORITY_JSON_INVALID", path, f"execution contract is invalid JSON: {exc}")]

    context = payload.get("llm_execution_context") if isinstance(payload.get("llm_execution_context"), dict) else payload
    command_reference = (
        context.get("command_reference")
        if isinstance(context, dict) and isinstance(context.get("command_reference"), dict)
        else {}
    )
    expected_sha = _manifest_sha(manifest)
    expected_ack = command_manifest_ack_line(manifest)
    required_values = {
        "json": COMMAND_REFERENCE_JSON,
        "markdown": COMMAND_REFERENCE_MARKDOWN,
        "manifest_sha": expected_sha,
        "ack": expected_ack,
        "must_not_reconstruct_commands_from_memory": True,
    }
    findings: list[CommandAuthorityFinding] = []
    for key, expected in required_values.items():
        if command_reference.get(key) != expected:
            findings.append(
                _finding(
                    "COMMAND_AUTHORITY_CONTRACT_MISMATCH",
                    path,
                    f"command_reference.{key} must be {expected!r}",
                )
            )
    source_hashes = command_reference.get("source_hashes")
    if not isinstance(source_hashes, dict):
        findings.append(
            _finding("COMMAND_AUTHORITY_SOURCE_HASHES_MISSING", path, "command_reference.source_hashes must be present")
        )
    else:
        for source in (COMMAND_REFERENCE_JSON, COMMAND_REFERENCE_MARKDOWN):
            if source not in source_hashes:
                findings.append(
                    _finding("COMMAND_AUTHORITY_SOURCE_HASH_MISSING", path, f"missing source hash for {source}")
                )
    return findings


def evaluate_command_authority(root: Path = Path(".")) -> CommandAuthorityAudit:
    root = root.resolve()
    manifest = load_command_manifest(root)
    findings: list[CommandAuthorityFinding] = []
    for path in TEXT_COMMAND_AUTHORITY_SURFACES:
        findings.extend(_audit_text_surface(root, path, manifest))
    findings.extend(_audit_execution_contract(root, manifest))
    return CommandAuthorityAudit(
        root=root.as_posix(),
        manifest_sha=_manifest_sha(manifest),
        findings=tuple(findings),
    )


def render_command_authority_audit(audit: CommandAuthorityAudit) -> str:
    lines = [
        "COMMAND_AUTHORITY_AUDIT",
        f"STATUS={audit.status}",
        f"MANIFEST_SHA={audit.manifest_sha}",
        f"FINDING_COUNT={len(audit.findings)}",
        f"BLOCKER_COUNT={len(audit.blockers)}",
    ]
    for finding in audit.findings:
        lines.append(f"FINDING={finding.severity}|{finding.code}|{finding.path}|{finding.message}")
    return "\n".join(lines) + "\n"
