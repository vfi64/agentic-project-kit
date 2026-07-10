from __future__ import annotations

from pathlib import Path
import hashlib
from typing import Any

COMMAND_REFERENCE_JSON = "docs/reference/agentic-kit-commands.json"
COMMAND_REFERENCE_MARKDOWN = "docs/reference/AGENTIC_KIT_COMMANDS.md"


def command_reference_contract(root: Path | str = ".") -> dict[str, Any]:
    repo_root = Path(root)
    source_hashes: dict[str, str] = {}
    for rel in (COMMAND_REFERENCE_JSON, COMMAND_REFERENCE_MARKDOWN):
        path = repo_root / rel
        if path.exists():
            source_hashes[rel] = hashlib.sha256(path.read_bytes()).hexdigest()

    return {
        "json": COMMAND_REFERENCE_JSON,
        "markdown": COMMAND_REFERENCE_MARKDOWN,
        "must_not_reconstruct_commands_from_memory": True,
        "source_hashes": source_hashes,
    }


def command_reference_prompt_block(root: Path | str = ".") -> str:
    contract = command_reference_contract(root)
    hashes = contract["source_hashes"]
    hash_lines = "\n".join(f"- {path}: {digest}" for path, digest in sorted(hashes.items()))
    if not hash_lines:
        hash_lines = "- source_hashes: unavailable; regenerate from repository root"

    return (
        "Command reference contract:\n"
        f"- Read `{COMMAND_REFERENCE_JSON}` before composing agentic-kit commands.\n"
        f"- Read `{COMMAND_REFERENCE_MARKDOWN}` before composing agentic-kit commands.\n"
        "- `must_not_reconstruct_commands_from_memory: true`.\n"
        "- Treat `source_hashes` as freshness evidence.\n"
        "source_hashes:\n"
        f"{hash_lines}"
    )


def ensure_command_reference_in_prompt(prompt_text: str, root: Path | str = ".") -> str:
    if COMMAND_REFERENCE_JSON in prompt_text and "must_not_reconstruct_commands_from_memory" in prompt_text:
        return prompt_text
    return prompt_text.rstrip() + "\n\n" + command_reference_prompt_block(root) + "\n"
