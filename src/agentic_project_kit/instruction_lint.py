from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import shlex
from typing import Any, Iterable

import yaml

from agentic_project_kit.command_manifest import load_manifest

ACK_PREFIX = "COMMAND_MANIFEST_ACK "
COMMAND_PREFIXES = (
    "git",
    "gh",
    "agentic-kit",
    "python -m agentic_project_kit",
)


@dataclass(frozen=True)
class InstructionLintFinding:
    line: int
    severity: str
    rule: str
    message: str
    command: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class InstructionLintResult:
    result_status: str
    findings: tuple[InstructionLintFinding, ...]
    checked_path: str
    manifest_sha: str

    @property
    def blockers(self) -> list[str]:
        return [finding.rule for finding in self.findings if finding.severity == "BLOCK"]

    @property
    def warnings(self) -> list[str]:
        return [finding.rule for finding in self.findings if finding.severity == "WARN"]

    @property
    def returncode(self) -> int:
        if self.blockers:
            return 2
        if self.warnings:
            return 1
        return 0

    def rejection_block(self) -> str:
        if not self.blockers:
            return ""
        lines = [
            "INSTRUCTION_LINT_REJECTION",
            f"manifest_sha={self.manifest_sha}",
            f"checked_path={self.checked_path}",
        ]
        for finding in self.findings:
            if finding.severity != "BLOCK":
                continue
            line = f"line={finding.line}" if finding.line > 0 else "line=structured"
            lines.append(f"{line} rule={finding.rule} message={finding.message}")
        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "kind": "instruction_lint_result",
            "result_status": self.result_status,
            "returncode": self.returncode,
            "manifest_sha": self.manifest_sha,
            "checked_path": self.checked_path,
            "blocker_count": len(self.blockers),
            "warning_count": len(self.warnings),
            "blockers": self.blockers,
            "warnings": self.warnings,
            "findings": [finding.to_dict() for finding in self.findings],
            "rejection_block": self.rejection_block(),
        }


@dataclass(frozen=True)
class _CandidateCommand:
    line: int
    text: str


def manifest_sha_from_manifest(manifest: dict[str, Any]) -> str:
    meta = manifest.get("meta") if isinstance(manifest.get("meta"), dict) else {}
    return str(meta.get("manifest_sha") or "")


def command_manifest_ack_line(manifest: dict[str, Any]) -> str:
    return f"{ACK_PREFIX}{manifest_sha_from_manifest(manifest)}"


def strip_command_manifest_ack_header(text: str) -> str:
    lines = text.splitlines(keepends=True)
    for index, line in enumerate(lines):
        if not line.strip():
            continue
        if line.rstrip("\r\n").startswith(ACK_PREFIX):
            return "".join([*lines[:index], *lines[index + 1 :]])
        return text
    return text


def _first_non_empty_line(text: str) -> str:
    for line in text.splitlines():
        if line.strip():
            return line.rstrip()
    return ""


def _strip_prompt_prefixes(line: str) -> str:
    text = line.strip()
    while text and text[0] in {"$", "#", ">"}:
        text = text[1:].lstrip()
    return " ".join(text.split())


def _starts_with_command_prefix(line: str) -> bool:
    return any(line == prefix or line.startswith(prefix + " ") for prefix in COMMAND_PREFIXES)


def _normalize_runtime_command(line: str) -> str:
    normalized = _strip_prompt_prefixes(line)
    python_prefixes = (
        "python -m agentic_project_kit.cli",
        "python -m agentic_project_kit",
    )
    for prefix in python_prefixes:
        if normalized == prefix:
            return "agentic-kit"
        if normalized.startswith(prefix + " "):
            return "agentic-kit " + normalized[len(prefix) :].strip()
    return normalized


def _iter_text_commands(text: str) -> Iterable[_CandidateCommand]:
    in_fence = False
    fence_marker = ""
    for line_number, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith(("```", "~~~")):
            marker = stripped[:3]
            if not in_fence:
                in_fence = True
                fence_marker = marker
            elif marker == fence_marker:
                in_fence = False
                fence_marker = ""
            continue
        normalized = _normalize_runtime_command(line)
        if not normalized or not _starts_with_command_prefix(normalized):
            continue
        yield _CandidateCommand(line_number, normalized)


def _iter_structured_commands(value: Any) -> Iterable[str]:
    if isinstance(value, dict):
        for key, item in value.items():
            if key in {"run", "command", "cmd", "shell"}:
                if isinstance(item, str):
                    yield item
                    continue
                if isinstance(item, list) and item and all(isinstance(part, str) for part in item):
                    yield " ".join(shlex.quote(part) for part in item)
                    continue
            yield from _iter_structured_commands(item)
    elif isinstance(value, list):
        for item in value:
            yield from _iter_structured_commands(item)


def _iter_yaml_commands(text: str) -> Iterable[_CandidateCommand]:
    try:
        loaded = yaml.safe_load(strip_command_manifest_ack_header(text))
    except Exception:
        return
    for command in _iter_structured_commands(loaded):
        normalized = _normalize_runtime_command(command)
        if normalized and _starts_with_command_prefix(normalized):
            yield _CandidateCommand(0, normalized)


def _matches_prefix(command_line: str, prefix: str) -> bool:
    return command_line == prefix or command_line.startswith(prefix + " ")


def _manifest_commands(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    return [command for command in manifest.get("commands") or [] if isinstance(command, dict)]


def _match_raw_replacement(manifest: dict[str, Any], command_line: str) -> dict[str, Any] | None:
    matches: list[tuple[str, dict[str, Any]]] = []
    for command in _manifest_commands(manifest):
        for raw_prefix in command.get("replaces_raw") or []:
            normalized_prefix = _strip_prompt_prefixes(str(raw_prefix))
            if normalized_prefix and _matches_prefix(command_line, normalized_prefix):
                matches.append((normalized_prefix, command))
    if not matches:
        return None
    longest = max(len(prefix) for prefix, _command in matches)
    selected = [command for prefix, command in matches if len(prefix) == longest]
    selected.sort(key=lambda command: str(command.get("qualified_name") or ""))
    return selected[0]


def _match_manifest_command(manifest: dict[str, Any], command_line: str) -> dict[str, Any] | None:
    matches: list[dict[str, Any]] = []
    for command in _manifest_commands(manifest):
        qualified_name = str(command.get("qualified_name") or "")
        if qualified_name and _matches_prefix(command_line, qualified_name):
            matches.append(command)
    if not matches:
        return None
    longest = max(len(str(command.get("qualified_name") or "")) for command in matches)
    selected = [command for command in matches if len(str(command.get("qualified_name") or "")) == longest]
    selected.sort(key=lambda command: str(command.get("qualified_name") or ""))
    return selected[0]


def _command_options(command: dict[str, Any]) -> set[str]:
    options: set[str] = set()
    for param in command.get("params") or []:
        if not isinstance(param, dict):
            continue
        options.update(str(opt) for opt in param.get("opts") or [])
        options.update(str(opt) for opt in param.get("secondary_opts") or [])
    return options


def _tokens(command_line: str) -> set[str]:
    try:
        return set(shlex.split(command_line))
    except ValueError:
        return set(command_line.split())


def _is_dry_run_variant(command_line: str, command: dict[str, Any]) -> bool:
    tokens = _tokens(command_line)
    options = _command_options(command)
    if "--dry-run" in tokens:
        return True
    if "--execute" in options and "--execute" not in tokens and "--allow-execute" not in tokens:
        return True
    return False


def _finding(
    candidate: _CandidateCommand,
    *,
    severity: str,
    rule: str,
    message: str,
) -> InstructionLintFinding:
    return InstructionLintFinding(
        line=candidate.line,
        severity=severity,
        rule=rule,
        message=message,
        command=candidate.text,
    )


def unreadable_instruction_result(
    *,
    checked_path: str,
    message: str,
    manifest_sha: str = "",
) -> InstructionLintResult:
    return InstructionLintResult(
        result_status="BLOCKED",
        findings=(
            InstructionLintFinding(
                line=1,
                severity="BLOCK",
                rule="INPUT_UNREADABLE",
                message=f"REJECTED: instruction input is unreadable: {message}",
                command="",
            ),
        ),
        checked_path=checked_path,
        manifest_sha=manifest_sha,
    )


def lint_instruction_text(
    text: str,
    *,
    manifest: dict[str, Any],
    checked_path: str = "<stdin>",
    require_ack: bool = True,
    strict_unknown: bool = False,
    include_structured_commands: bool = False,
) -> InstructionLintResult:
    manifest_sha = manifest_sha_from_manifest(manifest)
    findings: list[InstructionLintFinding] = []
    if not text.strip():
        findings.append(
            InstructionLintFinding(
                line=1,
                severity="BLOCK",
                rule="EMPTY_INPUT",
                message="REJECTED: instruction input is empty",
                command="",
            )
        )
    elif require_ack and _first_non_empty_line(text) != command_manifest_ack_line(manifest):
        findings.append(
            InstructionLintFinding(
                line=1,
                severity="BLOCK",
                rule="ACK",
                message=(
                    "REJECTED: missing/stale COMMAND_MANIFEST_ACK - read "
                    f"docs/reference/agentic-kit-commands.json (sha {manifest_sha}) first"
                ),
                command="",
            )
        )

    seen_dry_run_bases: set[str] = set()
    candidates = list(_iter_text_commands(text))
    if include_structured_commands:
        candidates.extend(_iter_yaml_commands(text))

    for candidate in candidates:
        raw_replacement = _match_raw_replacement(manifest, candidate.text)
        if raw_replacement is not None:
            wrapper = str(raw_replacement.get("qualified_name") or "")
            safety = str(raw_replacement.get("safety") or "")
            findings.append(
                _finding(
                    candidate,
                    severity="BLOCK",
                    rule="RAW_REPLACED",
                    message=f"REJECTED: use `{wrapper}` instead of `{candidate.text}` (safety: {safety})",
                )
            )
            continue

        manifest_command = _match_manifest_command(manifest, candidate.text)
        if candidate.text == "agentic-kit" or candidate.text.startswith("agentic-kit "):
            if manifest_command is None:
                findings.append(
                    _finding(
                        candidate,
                        severity="BLOCK",
                        rule="UNKNOWN_SUBCOMMAND",
                        message=f"REJECTED: unknown agentic-kit command `{candidate.text}`",
                    )
                )
                continue
            qualified_name = str(manifest_command.get("qualified_name") or "")
            if (
                manifest_command.get("safety") == "DESTRUCTIVE"
                and bool(manifest_command.get("dry_run_available"))
            ):
                if _is_dry_run_variant(candidate.text, manifest_command):
                    seen_dry_run_bases.add(qualified_name)
                elif qualified_name not in seen_dry_run_bases:
                    findings.append(
                        _finding(
                            candidate,
                            severity="BLOCK",
                            rule="DESTRUCTIVE_NO_DRYRUN",
                            message=(
                                "REJECTED: run a dry-run/plan variant before "
                                f"`{qualified_name}`"
                            ),
                        )
                    )
            continue

        if candidate.text.startswith(("git ", "gh ")):
            severity = "BLOCK" if strict_unknown else "WARN"
            findings.append(
                _finding(
                    candidate,
                    severity=severity,
                    rule="UNKNOWN_RAW",
                    message=f"UNKNOWN_RAW: no manifest mapping for `{candidate.text}`",
                )
            )

    if any(finding.severity == "BLOCK" for finding in findings):
        result_status = "BLOCKED"
    elif any(finding.severity == "WARN" for finding in findings):
        result_status = "WARN"
    else:
        result_status = "PASS"
    return InstructionLintResult(
        result_status=result_status,
        findings=tuple(findings),
        checked_path=checked_path,
        manifest_sha=manifest_sha,
    )


def lint_instruction_file(
    path: str | Path,
    *,
    root: Path = Path("."),
    require_ack: bool = True,
    strict_unknown: bool = False,
    include_structured_commands: bool = False,
) -> InstructionLintResult:
    payload_path = Path(path)
    try:
        text = payload_path.read_text(encoding="utf-8")
    except Exception as exc:
        return unreadable_instruction_result(
            checked_path=str(payload_path),
            message=str(exc),
        )
    return lint_instruction_text(
        text,
        manifest=load_manifest(root.resolve()),
        checked_path=str(payload_path),
        require_ack=require_ack,
        strict_unknown=strict_unknown,
        include_structured_commands=include_structured_commands,
    )


def lint_transfer_instruction(path: str | Path, *, root: Path = Path(".")) -> InstructionLintResult:
    return lint_instruction_file(path, root=root, include_structured_commands=True)


def render_instruction_lint_result(result: InstructionLintResult) -> str:
    lines = [
        "INSTRUCTION_LINT",
        f"STATUS={result.result_status}",
        f"MANIFEST_SHA={result.manifest_sha}",
        f"CHECKED_PATH={result.checked_path}",
        f"FINDING_COUNT={len(result.findings)}",
        f"BLOCKER_COUNT={len(result.blockers)}",
        f"WARNING_COUNT={len(result.warnings)}",
    ]
    for finding in result.findings:
        line = finding.line if finding.line > 0 else "structured"
        lines.append(
            f"FINDING={line}|{finding.severity}|{finding.rule}|{finding.message}"
        )
    if result.rejection_block():
        lines.extend(["", "REJECTION_BLOCK", result.rejection_block()])
    return "\n".join(lines) + "\n"
