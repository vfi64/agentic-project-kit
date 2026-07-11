from __future__ import annotations

import json
from pathlib import Path
import hashlib
import re
from typing import Any

COMMAND_REFERENCE_JSON = "docs/reference/agentic-kit-commands.json"
COMMAND_REFERENCE_MARKDOWN = "docs/reference/AGENTIC_KIT_COMMANDS.md"
ENTRYPOINT_START = "<!-- command-manifest-entrypoint:start -->"
ENTRYPOINT_END = "<!-- command-manifest-entrypoint:end -->"
ENTRYPOINT_SOURCE_PATHS = (
    "AGENTS.md",
    "src/agentic_project_kit/workspace_init.py",
    "src/agentic_project_kit/gui_task_editor.py",
)
CHAT_MODES = ("copy-paste", "remote", "file-transfer")
_SHA_REFERENCE_RE = re.compile(
    r"(?:manifest_sha:\s*|COMMAND_MANIFEST_ACK\s+)(?P<sha>[0-9a-f]{12}|stale|UNKNOWN)"
)


def load_command_manifest(root: Path | str = ".") -> dict[str, Any]:
    path = Path(root) / COMMAND_REFERENCE_JSON
    if not path.exists():
        return {"meta": {"manifest_sha": "UNKNOWN"}, "commands": []}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"meta": {"manifest_sha": "UNKNOWN"}, "commands": []}


def command_manifest_sha(manifest: dict[str, Any]) -> str:
    meta = manifest.get("meta") if isinstance(manifest.get("meta"), dict) else {}
    return str(meta.get("manifest_sha") or "UNKNOWN")


def computed_command_manifest_sha(manifest: dict[str, Any]) -> str:
    commands = manifest.get("commands")
    if not isinstance(commands, list):
        return command_manifest_sha(manifest)
    canonical = json.dumps(commands, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()[:12]


def command_manifest_ack_line(manifest: dict[str, Any]) -> str:
    return f"COMMAND_MANIFEST_ACK {command_manifest_sha(manifest)}"


def mandatory_entrypoint_line(manifest: dict[str, Any]) -> str:
    sha = command_manifest_sha(manifest)
    return (
        f"MANDATORY FIRST READ: {COMMAND_REFERENCE_JSON} (manifest_sha: {sha}). "
        "Every reply containing commands MUST start with: "
        f"COMMAND_MANIFEST_ACK {sha}. Consult `agentic-kit command-for` before proposing commands."
    )


def mandatory_entrypoint_block(manifest: dict[str, Any]) -> str:
    return "\n".join((ENTRYPOINT_START, mandatory_entrypoint_line(manifest), ENTRYPOINT_END))


def chat_refresher_lines(mode: str, manifest: dict[str, Any]) -> tuple[str, ...]:
    normalized_mode = _normalize_chat_mode(mode)
    sha = command_manifest_sha(manifest)
    mode_lines = {
        "copy-paste": "Mode copy-paste: your reply will be linted before execution.",
        "remote": "Mode remote: read the manifest file first, it is the single source.",
        "file-transfer": "Mode file-transfer: the carrier header pins the manifest sha.",
    }
    return (
        command_manifest_ack_line(manifest),
        f"Manifest: {COMMAND_REFERENCE_JSON} (manifest_sha: {sha}).",
        "Before proposing ANY command run/consult `agentic-kit command-for`.",
        "raw git/gh commands with a mapped wrapper are rejected by instruction lint.",
        mode_lines[normalized_mode],
        f"Readable reference: {COMMAND_REFERENCE_MARKDOWN}.",
    )


def render_chat_refresher(mode: str = "copy-paste", root: Path | str = ".") -> str:
    return "\n".join(chat_refresher_lines(mode, load_command_manifest(root))) + "\n"


def render_chat_session_start(mode: str = "copy-paste", root: Path | str = ".") -> str:
    manifest = load_command_manifest(root)
    lines = [*chat_refresher_lines(mode, manifest), "", "Command manifest inline list:"]
    for command in manifest.get("commands") or []:
        if not isinstance(command, dict):
            continue
        lines.append(
            f"{command.get('qualified_name', '')} · {command.get('safety', '')} · "
            f"{command.get('when_to_use', '')}"
        )
    return "\n".join(lines).rstrip() + "\n"


def _normalize_chat_mode(mode: str) -> str:
    normalized = str(mode or "").strip().lower().replace("_", "-")
    if normalized not in CHAT_MODES:
        raise ValueError(f"unsupported chat mode: {mode}")
    return normalized


def command_reference_contract(root: Path | str = ".") -> dict[str, Any]:
    repo_root = Path(root)
    manifest = load_command_manifest(repo_root)
    source_hashes: dict[str, str] = {}
    for rel in (COMMAND_REFERENCE_JSON, COMMAND_REFERENCE_MARKDOWN):
        path = repo_root / rel
        if path.exists():
            source_hashes[rel] = hashlib.sha256(path.read_bytes()).hexdigest()

    return {
        "json": COMMAND_REFERENCE_JSON,
        "markdown": COMMAND_REFERENCE_MARKDOWN,
        "manifest_sha": command_manifest_sha(manifest),
        "ack": command_manifest_ack_line(manifest),
        "must_not_reconstruct_commands_from_memory": True,
        "source_hashes": source_hashes,
    }


def command_reference_prompt_block(root: Path | str = ".") -> str:
    contract = command_reference_contract(root)
    manifest = load_command_manifest(root)
    hashes = contract["source_hashes"]
    hash_lines = "\n".join(f"- {path}: {digest}" for path, digest in sorted(hashes.items()))
    if not hash_lines:
        hash_lines = "- source_hashes: unavailable; regenerate from repository root"

    return (
        "Command manifest entrypoint:\n"
        f"- {mandatory_entrypoint_line(manifest)}\n"
        f"- {chat_refresher_lines('remote', manifest)[2]}\n"
        f"- {chat_refresher_lines('remote', manifest)[3]}\n\n"
        "Command reference contract:\n"
        f"- Read `{COMMAND_REFERENCE_JSON}` before composing agentic-kit commands.\n"
        f"- Read `{COMMAND_REFERENCE_MARKDOWN}` before composing agentic-kit commands.\n"
        "- `must_not_reconstruct_commands_from_memory: true`.\n"
        "- Treat `source_hashes` as freshness evidence.\n"
        "source_hashes:\n"
        f"{hash_lines}"
    )


def ensure_command_reference_in_prompt(prompt_text: str, root: Path | str = ".") -> str:
    manifest = load_command_manifest(root)
    if (
        COMMAND_REFERENCE_JSON in prompt_text
        and command_manifest_ack_line(manifest) in prompt_text
        and "must_not_reconstruct_commands_from_memory" in prompt_text
    ):
        return prompt_text
    return prompt_text.rstrip() + "\n\n" + command_reference_prompt_block(root) + "\n"


def upsert_mandatory_entrypoint_block(text: str, manifest: dict[str, Any]) -> str:
    block = mandatory_entrypoint_block(manifest)
    if ENTRYPOINT_START in text and ENTRYPOINT_END in text:
        pattern = re.compile(
            re.escape(ENTRYPOINT_START) + r".*?" + re.escape(ENTRYPOINT_END),
            re.DOTALL,
        )
        return pattern.sub(block, text, count=1)
    heading = "# Agent Instructions"
    if heading in text:
        return text.replace(heading, heading + "\n\n" + block, 1)
    return block + "\n\n" + text


def sync_entrypoint_files(
    root: Path | str,
    *,
    manifest: dict[str, Any],
    markdown: str,
    execute: bool = False,
) -> dict[str, Any]:
    repo_root = Path(root)
    targets: dict[str, str] = {
        COMMAND_REFERENCE_JSON: json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        COMMAND_REFERENCE_MARKDOWN: markdown,
    }
    agents_path = repo_root / "AGENTS.md"
    if agents_path.exists():
        targets["AGENTS.md"] = upsert_mandatory_entrypoint_block(
            agents_path.read_text(encoding="utf-8"),
            manifest,
        )

    changed_paths: list[str] = []
    for relative, desired in targets.items():
        path = repo_root / relative
        current = path.read_text(encoding="utf-8") if path.exists() else ""
        if current != desired:
            changed_paths.append(relative)
            if execute:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(desired, encoding="utf-8")

    return {
        "schema_version": 1,
        "kind": "commands_sync_entrypoints_result",
        "result_status": "PASS",
        "manifest_sha": command_manifest_sha(manifest),
        "changed": bool(changed_paths),
        "execute": execute,
        "changed_paths": changed_paths,
    }


def audit_entrypoint_manifest_references(
    root: Path | str,
    manifest: dict[str, Any],
) -> list[dict[str, str]]:
    repo_root = Path(root)
    expected_sha = computed_command_manifest_sha(manifest)
    findings: list[dict[str, str]] = []
    for relative in ENTRYPOINT_SOURCE_PATHS:
        path = repo_root / relative
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        if relative == "AGENTS.md" and mandatory_entrypoint_line(manifest) not in text:
            findings.append(
                {
                    "code": "ENTRYPOINT_MANIFEST_BLOCK_MISSING",
                    "message": f"{relative}: missing current command manifest entrypoint block",
                }
            )
        for match in _SHA_REFERENCE_RE.finditer(text):
            found = match.group("sha")
            if found != expected_sha:
                findings.append(
                    {
                        "code": "ENTRYPOINT_MANIFEST_SHA_MISMATCH",
                        "message": f"{relative}: expected {expected_sha}, found {found}",
                    }
                )
    return findings
