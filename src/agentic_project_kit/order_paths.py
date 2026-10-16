"""Confine paths named by LLM-written work orders to the repository (WOTB-03, WOTB-06).

Order files decide where the Kit reads payloads and writes logs, reports and files. A lexical
check alone lets ``..`` segments or symlinks inside the checkout reach files outside it, so every
order-controlled path is checked lexically when the order is parsed and again against the real
filesystem right before it is read or written.
"""

from __future__ import annotations

from pathlib import Path, PurePosixPath


def lexical_repo_path(path_text: str, *, field_name: str, prefix: str = "") -> str:
    """Reject absolute paths and empty, ``.`` or ``..`` segments; optionally require a prefix."""
    if not isinstance(path_text, str) or not path_text.strip():
        raise ValueError(f"{field_name} must be a non-empty repo-relative path")
    if "\\" in path_text or path_text.startswith("/") or PurePosixPath(path_text).is_absolute():
        raise ValueError(f"{field_name} must be repo-relative")
    parts = path_text.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise ValueError(f"{field_name} must not contain empty/current/parent segments")
    if prefix and not path_text.startswith(prefix):
        raise ValueError(f"{field_name} must be under {prefix}")
    return path_text


def confined_repo_path(root: Path, path_text: str, *, field_name: str) -> Path:
    """Return ``root / path_text`` only if no existing component is a symlink and it stays in root."""
    lexical_repo_path(path_text, field_name=field_name)
    root_path = Path(root)
    current = root_path
    for part in path_text.split("/"):
        current = current / part
        if current.is_symlink():
            raise ValueError(f"{field_name} must not pass through a symlink: {path_text}")
    resolved_root = root_path.resolve()
    resolved = (root_path / path_text).resolve()
    if resolved != resolved_root and resolved_root not in resolved.parents:
        raise ValueError(f"{field_name} resolves outside the repository: {path_text}")
    return root_path / path_text
