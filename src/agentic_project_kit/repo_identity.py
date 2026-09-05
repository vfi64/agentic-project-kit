from __future__ import annotations

import configparser
import os
import subprocess
from pathlib import Path
from typing import Mapping
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


def _gitdir_from_pointer(root: Path, pointer: Path) -> Path | None:
    try:
        text = pointer.read_text(encoding="utf-8")
    except OSError:
        return None
    prefix = "gitdir:"
    if not text.startswith(prefix):
        return None
    gitdir = Path(text[len(prefix) :].strip())
    if not gitdir.is_absolute():
        gitdir = root / gitdir
    return gitdir


def _git_config_candidates(root: Path) -> tuple[Path, ...]:
    git_path = root / ".git"
    if git_path.is_dir():
        return (git_path / "config",)
    if not git_path.is_file():
        return ()
    gitdir = _gitdir_from_pointer(root, git_path)
    if gitdir is None:
        return ()
    candidates = [gitdir / "config"]
    common_dir_file = gitdir / "commondir"
    try:
        common_dir_text = common_dir_file.read_text(encoding="utf-8").strip()
    except OSError:
        common_dir_text = ""
    if common_dir_text:
        common_dir = Path(common_dir_text)
        if not common_dir.is_absolute():
            common_dir = gitdir / common_dir
        candidates.append(common_dir / "config")
    return tuple(candidates)


def _origin_url_from_git_config(root: Path) -> str | None:
    parser = configparser.ConfigParser()
    for candidate in _git_config_candidates(root):
        if not candidate.exists():
            continue
        try:
            parser.read(candidate, encoding="utf-8")
        except configparser.Error:
            continue
        if parser.has_option('remote "origin"', "url"):
            return parser.get('remote "origin"', "url")
    return None


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


def detect_origin_github_repo(root: Path) -> str | None:
    """Return owner/repo from the current repository's origin remote when it is GitHub."""
    root = Path(root)
    if not (root / ".git").exists():
        return None
    config_url = _origin_url_from_git_config(root)
    if config_url is not None:
        return _repo_name_from_remote_url(config_url)
    completed = subprocess.run(
        ["git", "-C", str(root), "remote", "get-url", "origin"],
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        return None
    return _repo_name_from_remote_url(completed.stdout)


def github_cli_env_for_origin(root: Path, base_env: Mapping[str, str] | None = None) -> dict[str, str] | None:
    """Build a GitHub CLI environment pinned to origin, overriding stale GH_REPO context."""
    repo = detect_origin_github_repo(root)
    if repo is None:
        return None
    env = dict(os.environ if base_env is None else base_env)
    env["GH_REPO"] = repo
    return env


def bind_github_cli_env_for_origin(root: Path) -> dict[str, str] | None:
    """Pin child GitHub CLI calls in this process to the repository origin."""
    env = github_cli_env_for_origin(root)
    if env is not None:
        os.environ["GH_REPO"] = env["GH_REPO"]
    return env


def default_local_path_hint(root: Path) -> str:
    return f"cd /path/to/{Path(root).name}"
