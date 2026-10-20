"""Light-path SKIPPED checks a consumer declared, accepted only for a light pull request (KIT-GF-073).

A consumer's custom CI (the KIT-GF-063 fragment) skips its heavy jobs when `ci runtime-plan`
classifies a pull request as light. Those jobs then report SKIPPED, which every Kit readiness
route treated as not green. A workspace may name them in `.agentic/config.yaml`:

    gates:
      light_path_skipped_checks: [playwright]

The names are accepted as SKIPPED only when the Kit re-derives, from local Git objects, that the
pull request itself is light: the same `ci runtime-plan` classifier over merge-base..head with the
pull request's head branch. Unknown input, missing commits, a full classification or an invalid
manifest yield no allowance, so a skipped job on a full pull request still blocks.
"""

from __future__ import annotations

from pathlib import Path
import subprocess
from typing import Any

_CACHE: dict[tuple[str, str, str, str, tuple[str, ...]], frozenset[str]] = {}


def declared_light_path_skipped_checks(root: Path) -> tuple[str, ...]:
    from agentic_project_kit.workspace import load_workspace

    try:
        return load_workspace(root.resolve(), suppress_legacy_profile_warning=True).gates_light_path_skipped_checks
    except (OSError, RuntimeError, ValueError):
        return ()


def declared_required_checks(root: Path) -> tuple[str, ...]:
    """KIT-GF-079: checks `gates.required_checks` names; readiness waits until each exists.

    Unreadable or invalid configuration yields nothing, so readiness keeps its earlier rules.
    """
    from agentic_project_kit.workspace import load_workspace

    try:
        return load_workspace(root.resolve(), suppress_legacy_profile_warning=True).gates_required_checks
    except (OSError, RuntimeError, ValueError):
        return ()


def light_path_skip_allowance(root: Path, *, base: str, head: str, branch: str) -> frozenset[str]:
    """Return the declared names when base..head of this PR is classified light, else nothing."""
    names = declared_light_path_skipped_checks(root)
    if not names or not base or not head or not branch:
        return frozenset()
    key = (str(root.resolve()), base, head, branch, names)
    if key in _CACHE:
        return _CACHE[key]
    allowance: frozenset[str] = frozenset()
    try:
        merge_base = subprocess.run(
            ["git", "merge-base", "--end-of-options", base, head],
            cwd=root, capture_output=True, text=True, check=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        merge_base = ""
    if merge_base:
        from agentic_project_kit.ci_runtime_plan import runtime_plan

        plan = runtime_plan(root, merge_base, head, branch=branch, event_name="pull_request")
        if plan.get("mode") == "light":
            allowance = frozenset(names)
    _CACHE[key] = allowance
    return allowance


def light_path_skip_allowance_for_pr(payload: dict[str, Any], root: Path | None = None) -> frozenset[str]:
    """Allowance for a `gh pr view` payload with baseRefOid, headRefOid and headRefName."""
    return light_path_skip_allowance(
        root or Path("."),
        base=str(payload.get("baseRefOid") or ""),
        head=str(payload.get("headRefOid") or ""),
        branch=str(payload.get("headRefName") or ""),
    )
