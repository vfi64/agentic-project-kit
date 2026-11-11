"""Decide whether Git's file inventory belongs to the requested scan root."""

from pathlib import Path
import subprocess


def is_git_worktree_root(root: Path) -> bool:
    """A nested directory in someone else's repository must use filesystem scanning."""
    prefix = subprocess.run(
        ["git", "-C", root.as_posix(), "rev-parse", "--show-prefix"],
        text=True, capture_output=True, check=False,
    )
    return prefix.returncode == 0 and not prefix.stdout.strip()
