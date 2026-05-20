from __future__ import annotations

import os
import py_compile
from pathlib import Path


class SafeReplaceError(RuntimeError):
    pass


def validate_replacement(target: Path, replacement: Path) -> None:
    if not replacement.exists():
        raise SafeReplaceError(f"replacement does not exist: {replacement}")
    if not replacement.is_file():
        raise SafeReplaceError(f"replacement is not a file: {replacement}")
    if replacement.is_symlink():
        raise SafeReplaceError(f"replacement must not be a symlink: {replacement}")
    if target.suffix == ".py":
        try:
            py_compile.compile(str(replacement), doraise=True)
        except py_compile.PyCompileError as exc:
            raise SafeReplaceError(f"replacement failed py_compile: {replacement}") from exc


def safe_replace(target: Path | str, replacement: Path | str) -> Path:
    target_path = Path(target)
    replacement_path = Path(replacement)
    if target_path.is_symlink():
        raise SafeReplaceError(f"target must not be a symlink: {target_path}")
    if not target_path.parent.exists():
        raise SafeReplaceError(f"target parent does not exist: {target_path.parent}")
    validate_replacement(target_path, replacement_path)
    os.replace(replacement_path, target_path)
    return target_path
