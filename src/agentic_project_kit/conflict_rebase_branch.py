"""Validate the owning branch of a detached, in-progress Git rebase."""
from pathlib import Path
from typing import Callable


def detached_rebase_branch(run_step: Callable) -> str:
    """Return a proven local branch, or an empty string without changing Git."""
    states = []
    for backend in ("rebase-merge", "rebase-apply"):
        result = run_step(f"{backend}-path", ["git", "rev-parse", "--git-path", backend])
        if result["returncode"] != 0:
            return ""
        path = Path(str(result["stdout"]).strip())
        if path.is_dir():
            states.append(path)
    if len(states) != 1:
        return ""
    try:
        ref, original, onto = (
            (states[0] / name).read_text(encoding="utf-8").strip()
            for name in ("head-name", "orig-head", "onto")
        )
    except (OSError, UnicodeError):
        return ""
    if not ref.startswith("refs/heads/"):
        return ""
    valid = run_step("rebase-branch-format", ["git", "check-ref-format", ref])
    if valid["returncode"] != 0:
        return ""
    # Accept only full object IDs, never revision expressions from metadata.
    if any(len(oid) not in (40, 64) or any(c not in "0123456789abcdef" for c in oid)
           for oid in (original, onto)):
        return ""
    for name, revision, expected in (("owner", ref, original),
                                     ("original", original, original),
                                     ("onto", onto, onto)):
        result = run_step(f"rebase-{name}-commit",
                          ["git", "rev-parse", "--verify", f"{revision}^{{commit}}"])
        if result["returncode"] != 0 or str(result["stdout"]).strip() != expected:
            return ""
    ancestor = run_step("rebase-target-ancestor", ["git", "merge-base", "--is-ancestor", onto, "HEAD"])
    if ancestor["returncode"] != 0:
        return ""
    return ref.removeprefix("refs/heads/")
