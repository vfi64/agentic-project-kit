from __future__ import annotations

import subprocess
from pathlib import Path
from urllib.parse import urlparse


def _strip_dot_git(value: str) -> str:
    return value[:-4] if value.endswith(".git") else value


def _repo_name_from_path(value: str) -> str | None:
    path = _strip_dot_git(value.strip().strip("/"))
    parts = [part for part in path.split("/") if part]
    if len(parts) != 2:
        return None
    owner, repo = parts
    if not owner or not repo:
        return None
    return f"{owner}/{repo}"


def _repo_name_from_remote_url(remote_url: str) -> str | None:
    url = remote_url.strip()
    if not url:
        return None

    scp_prefix = "git@github.com:"
    if url.startswith(scp_prefix):
        return _repo_name_from_path(url[len(scp_prefix) :])

    parsed = urlparse(url)
    if parsed.hostname != "github.com":
        return None
    return _repo_name_from_path(parsed.path)


def _repo_identity_fallback(root: Path, reason: str) -> str:
    return f"{Path(root).name} ({reason})"


def detect_repo_full_name(root: Path) -> str:
    completed = subprocess.run(
        ["git", "-C", str(root), "remote", "get-url", "origin"],
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        return _repo_identity_fallback(root, "no git remote 'origin'")

    full_name = _repo_name_from_remote_url(completed.stdout)
    if full_name is None:
        return _repo_identity_fallback(root, "unrecognized git remote 'origin'")
    return full_name


def default_local_path_hint(root: Path) -> str:
    return f"cd /path/to/{Path(root).name}"
