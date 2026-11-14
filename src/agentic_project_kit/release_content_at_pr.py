"""G2 (owner 2026-11-13): release checks that depend only on repository content run at the PR.

``release ready`` (A2) runs ``transfer standard-error-scan --before-release``. Without
``--before-release`` the same command runs the repository-content part of that scan, and
``work finish`` runs it before the commit, together with the Kit CI pin guard of
``release prepare`` (KIT-CHK-RELEASE-CONTENT-AT-PR). Every release step that only the release
runs is listed with its stage and reason in ``reference/check-producers.json`` (``release_path``);
``tests/test_g2_release_checks_at_pr.py`` derives the release steps from the source and fails on
an unlisted one.
"""
from __future__ import annotations

import json
from pathlib import Path

CHECK_ID = "KIT-CHK-RELEASE-CONTENT-AT-PR"
SCAN_DETAIL_COMMAND = "agentic-kit transfer standard-error-scan --json"


def release_run_covering_branch(root: Path, branch: str) -> str:
    """Version of a release run whose A2 already scanned main and which owns this branch, else ''.

    The release run (``release run``) finishes A2 (the full ``--before-release`` scan) on main and
    then calls ``work finish`` for its own release branch (B3/B4) and DOI branch (D3/D4). Those
    branches add generated release metadata only; the PR scan would repeat A2 and, for the Kit's
    own release, compare the bumped version with the installed one. The decision reads the run
    state, not the branch name.
    """
    from agentic_project_kit.workspace import load_workspace

    try:
        tmp = load_workspace(root, suppress_legacy_profile_warning=True).tmp()
    except (OSError, ValueError, RuntimeError):
        return ""
    for state_path in sorted(tmp.glob("release-run-*.json")):
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            continue
        if not isinstance(state, dict) or state.get("kind") != "release_run_state":
            continue
        release_branch = str(state.get("release_branch") or "")
        finished = state.get("finished_steps") or []
        if release_branch and branch in {release_branch, f"{release_branch}-doi"} and "A2" in finished:
            return str(state.get("version") or "")
    return ""


def scan_summary(stdout: str) -> tuple[str, list[str], list[str]]:
    """Result status, blockers and warnings of a standard-error-scan JSON payload."""
    try:
        payload = json.loads(stdout)
    except (json.JSONDecodeError, TypeError):
        return "<no JSON>", [], []
    if not isinstance(payload, dict):
        return "<no JSON>", [], []
    return (
        str(payload.get("result_status") or ""),
        [str(item) for item in payload.get("blockers") or []],
        [str(item) for item in payload.get("warnings") or []],
    )
