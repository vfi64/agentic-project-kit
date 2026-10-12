"""Content-sensitive local preview identity, independent of widget state."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
import stat
import subprocess


def repository_preview_signature(root: Path) -> str:
    digest = hashlib.sha256(str(root.resolve()).encode())

    def git(*args: str) -> str:
        completed = subprocess.run(
            ["git", *args], cwd=root, text=True, capture_output=True, check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError(f"Cannot verify preview state: git {' '.join(args[:2])}: {completed.stderr.strip()}")
        digest.update(completed.stdout.encode())
        digest.update(b"\0")
        return completed.stdout

    git("rev-parse", "HEAD")
    git("symbolic-ref", "--short", "HEAD")
    git("diff", "--cached", "--raw", "--no-abbrev", "--no-ext-diff", "HEAD")
    entries = iter(git("status", "--porcelain=v1", "-z", "--untracked-files=all").split("\0"))
    for entry in entries:
        if not entry:
            continue
        relative = Path(entry[3:])
        if relative.is_absolute() or ".." in relative.parts:
            raise RuntimeError("Invalid repository-relative preview path.")
        if entry[0] in {"R", "C"} or entry[1] in {"R", "C"}:
            next(entries, None)  # -z supplies the source name after the destination.
        path = root / relative
        if not path.parent.resolve().is_relative_to(root.resolve()):
            raise RuntimeError("Preview path resolves outside the selected repository.")
        try:
            metadata = path.lstat()
        except FileNotFoundError:
            digest.update(b"deleted\0")
            continue
        digest.update(str(metadata.st_mode).encode())
        if stat.S_ISLNK(metadata.st_mode):
            digest.update(hashlib.sha256(os.readlink(path).encode()).digest())
        elif stat.S_ISREG(metadata.st_mode):
            content = hashlib.sha256()
            with path.open("rb") as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    content.update(chunk)
            digest.update(content.digest())
            after = path.lstat()
            if (metadata.st_size, metadata.st_mtime_ns, metadata.st_ino) != (after.st_size, after.st_mtime_ns, after.st_ino):
                raise RuntimeError("Repository content changed while inspecting the preview.")
        else:
            raise RuntimeError(f"Preview requires manual review of a non-file change: {relative}")
        digest.update(b"\0")
    return digest.hexdigest()
