"""Bounded read-only observations for intent selection, never cached caller facts."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess

from .repo_identity import detect_origin_github_repo, github_pr_url_matches
from .task_selection import valid_value
from .workspace import load_workspace


def _read(root: Path, argv: list[str]) -> str | None:
    try:
        done = subprocess.run(
            argv, cwd=root, text=True, capture_output=True, timeout=20, check=False, env=None
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return done.stdout.strip() if done.returncode == 0 else None


def observe_facts(
    root: Path, manifest: dict, inputs: dict, *, observe_pr: bool = False
) -> tuple[dict, dict]:
    root = root.resolve()
    head = _read(root, ["git", "rev-parse", "HEAD"])
    top = _read(root, ["git", "rev-parse", "--show-toplevel"])
    context = {
        "root": str(root),
        "current_root": str(root),
        "observed_head": head,
        "manifest_sha": manifest.get("meta", {}).get("manifest_sha"),
    }
    facts = {}
    # A nested path must not inherit facts from a different Git root.
    if not top or Path(top).resolve() != root:
        context["current_head"] = None
        return facts, context
    try:
        workspace = load_workspace(root, suppress_legacy_profile_warning=True)
    except (OSError, ValueError, RuntimeError):
        context["current_head"] = head
        return facts, context
    managed = (
        workspace.manifest_schema_version > 0 or (root / "src/agentic_project_kit/cli.py").is_file()
    )
    facts["workspace_mode"] = "managed" if managed else "unmanaged"
    branch = _read(root, ["git", "branch", "--show-current"])
    default = _read(root, ["git", "symbolic-ref", "refs/remotes/origin/HEAD"])
    if branch and default and default.startswith("refs/remotes/origin/"):
        facts["branch_role"] = (
            "main" if branch == default.removeprefix("refs/remotes/origin/") else "work"
        )
    status = _read(root, ["git", "status", "--porcelain", "--untracked-files=all"])
    if status is not None:
        facts["worktree_clean"] = not status
    version = inputs.get("version")
    if valid_value(version, "stable_version"):
        state = workspace.tmp_file(f"release-run-{version}.json")
        # Any existing run requires its own explicit resume intent, even malformed state.
        try:
            state_exists = state.exists()
        except OSError:
            state_exists = None
        if state_exists is not None:
            facts["release_state"] = "prepared" if state_exists else "none"
        tag = _read(root, ["git", "tag", "--list", f"v{version}"])
        if tag:
            facts["release_state"] = "published"
    if observe_pr:
        _observe_pr(root, inputs, facts, context)
    context["current_head"] = _read(root, ["git", "rev-parse", "HEAD"])
    if (
        _read(root, ["git", "branch", "--show-current"]) != branch
        or _read(root, ["git", "status", "--porcelain", "--untracked-files=all"]) != status
    ):
        context["current_head"] = None
    return facts, context


def _observe_pr(root: Path, inputs: dict, facts: dict, context: dict) -> None:
    number = inputs.get("pr_number", inputs.get("after_pr"))
    if not valid_value(number, "positive_integer"):
        return
    repo = detect_origin_github_repo(root)
    if not repo:
        return
    # Explicit opt-in and exact number: no PR search, remote crawl, fetch or mutation.
    text = _read(
        root,
        ["gh", "pr", "view", str(number), "--repo", repo, "--json", "number,state,headRefOid,url"],
    )
    try:
        data = json.loads(text or "null")
    except ValueError:
        return
    if not isinstance(data, dict) or data.get("number") != number:
        return
    if not isinstance(data.get("url"), str) or not github_pr_url_matches(data["url"], repo, number):
        return
    state = {"OPEN": "open", "MERGED": "merged", "CLOSED": "closed"}.get(data.get("state"))
    if not state or not valid_value(data.get("headRefOid"), "full_commit"):
        return
    facts["pr_state"] = state
    context["repository"] = repo
    context["pr"] = {"repository": repo, "number": number, "head": data["headRefOid"]}


def select_observed_intent(root: Path, intent: str, inputs: str, *, observe_pr: bool = False):
    """CLI boundary: no caller facts, structured errors for invalid workspaces."""
    from .command_manifest import load_manifest
    from .command_selector import CommandSelection, select_for_intent

    try:
        parameters = json.loads(inputs)
        if not isinstance(parameters, dict):
            raise ValueError("inputs must be an object")
        manifest = load_manifest(root.resolve(), suppress_legacy_profile_warning=True)
        facts, context = observe_facts(root, manifest, parameters, observe_pr=observe_pr)
        return select_for_intent(manifest, intent, facts, parameters, context)
    except (ValueError, OSError, RuntimeError) as exc:
        return CommandSelection(
            "INVALID_INPUT",
            {
                "mode": "intent",
                "intent": intent,
                "result_status": "INVALID_INPUT",
                "execution_authorized": False,
                "reasons": [str(exc)],
            },
        )
