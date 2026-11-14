"""KIT-GF-080 and K7: continue a blocked B4 of the release run from the state it left.

B4 is ``work finish --execute`` on the release branch. It commits the release metadata
(``Prepare release <v>``), refreshes and commits the handoff projections (``Refresh handoff for
Release <v>``), in the Kit's own workspace rebuilds the docs-pages projection (``Refresh
docs-pages projection for Release <v>``), pushes, opens the release PR and completes it. A stop on
that path left the release without a route: a new run met committed changes and blocked with
``changed-paths-drift``.

KIT-GF-080 (release 1.1.4): B4 stopped with an open release PR. The gate completes that PR with
``transfer pr-complete`` and exact head checks.

K7 (owner plan 2026-11-13, release 1.3.0 stopped between its two commits on a locked index): B4
stopped before its PR existed, after at least the release commit. The gate publishes the existing
commits with ``work finish`` (K1 without ``--path``); projection files B4 wrote but did not commit
are committed first with the subject B4 would have used. The approved release content is exactly
the first commit; every later commit and every uncommitted file may touch only the projections.

Both resumes apply only when the previous B4 attempt failed, the branch holds a linear history on
the approved base that matches the B4 pattern, and main has not moved since that base. The gate
names base, head and the commits, so its signature covers them. Whether the branch exists on the
origin is read with ``git ls-remote``; a PR can be open only while its head branch exists, so the
GitHub lookup runs only then.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from agentic_project_kit.release_run import ReleaseRun

RESUME_MODE = "resume-existing-release-pr"
UNPUBLISHED_MODE = "resume-unpublished-release-commits"


def _approved_b4_base(run: "ReleaseRun") -> str:
    for approval in reversed(run.state.get("approvals") or []):
        if approval.get("step_id") == "B4":
            return str((approval.get("gate") or {}).get("target_commit") or "")
    return ""


def previous_b4_failed(run: "ReleaseRun") -> bool:
    path = run.step_dir / "B4.json"
    if not path.is_file():
        return False
    try:
        previous = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    return isinstance(previous, dict) and previous.get("returncode", 0) != 0


def projection_subjects(version: str) -> dict[str, str]:
    """Subjects of the commits B4's work finish writes after the release commit, by kind."""
    title = f"Release {version}"
    return {f"Refresh handoff for {title}": "handoff", f"Refresh docs-pages projection for {title}": "docs"}


def _matches(path: str, entry: str) -> bool:
    # git status lists an untracked directory as "dir/"; the commit then holds files under it.
    return path == entry or (entry.endswith("/") and path.startswith(entry))


def covers_approved_paths(files: list[str], approved: list[str]) -> bool:
    """Every changed file is an approved path (or under an approved directory) and every approved path changed."""
    if not files:
        return False
    return (all(any(_matches(f, entry) for entry in approved) for f in files)
            and all(any(_matches(f, entry) for f in files) for entry in approved))


def projection_paths(run: "ReleaseRun") -> dict[str, tuple[str, ...]]:
    from agentic_project_kit.docs_pages_projection import DOCS_PAGES_COMMIT_PATHS
    from agentic_project_kit.handoff_closeout import handoff_closeout_paths
    from agentic_project_kit.workspace import load_workspace

    workspace = load_workspace(run.root, suppress_legacy_profile_warning=True)
    handoff = tuple(workspace.path_text(path) for path in handoff_closeout_paths(workspace))
    return {"handoff": handoff, "docs": tuple(DOCS_PAGES_COMMIT_PATHS)}


def projection_kind(run: "ReleaseRun", files: list[str]) -> str:
    """'handoff' or 'docs' when every file belongs to that projection, else ''."""
    if not files:
        return ""
    for kind, entries in projection_paths(run).items():
        if all(f in entries or (kind == "docs" and any(f.startswith(e + "/") for e in entries)) for f in files):
            return kind
    return ""


def release_commits(run: "ReleaseRun", base: str, head: str) -> tuple[list[dict[str, str]], str]:
    """The B4 commits on base..head, or a blocker.

    The history must be linear on the approved base; the first commit is the release commit with
    exactly the approved paths, every later one a projection commit that touches only its projection.
    """
    listed = run._command("B4-resume-commits", ["git", "rev-list", "--reverse", "--parents", f"{base}..{head}"])
    lines = [line.split() for line in listed["stdout"].splitlines() if line.strip()] if listed["result_status"] == "PASS" else []
    if not lines:
        return [], "release-resume-unexpected-commits"
    parent = base
    for fields in lines:
        if len(fields) != 2 or fields[1] != parent:
            return [], "release-resume-unexpected-commits"   # merge, gap or side history
        parent = fields[0]
    if parent != head:
        return [], "release-resume-unexpected-commits"
    kinds = projection_subjects(run.version)
    commits: list[dict[str, str]] = []
    for index, (sha, _parent) in enumerate(lines):
        shown = run._command("B4-resume-subject", ["git", "log", "-1", "--format=%s", sha])
        subject = shown["stdout"].strip() if shown["result_status"] == "PASS" else ""
        changed = run._command("B4-resume-paths", ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", sha])
        files = sorted(changed["stdout"].split()) if changed["result_status"] == "PASS" else []
        if index == 0:
            if subject != f"Prepare release {run.version}":
                return [], "release-resume-unexpected-commits"
            if not covers_approved_paths(files, list(run.state.get("b_paths") or [])):
                return [], "release-resume-paths-differ"
        else:
            kind = kinds.get(subject)
            if kind is None:
                return [], "release-resume-unexpected-commits"
            if projection_kind(run, files) != kind:
                return [], "release-resume-paths-differ"
        commits.append({"sha": sha, "subject": subject})
    return commits, ""


def _remote_heads(run: "ReleaseRun") -> dict[str, str] | None:
    listed = run._command("B4-resume-remote", ["git", "ls-remote", "origin", f"refs/heads/{run.branch}", "refs/heads/main"])
    if listed["returncode"] != 0:
        return None
    heads: dict[str, str] = {}
    for line in listed["stdout"].splitlines():
        fields = line.split()
        if len(fields) == 2:
            heads[fields[1]] = fields[0]
    return heads


def _pending_paths(run: "ReleaseRun") -> list[str] | None:
    # Tracked changes only; untracked files (the run state under tmp/, Download/) stay out, as in K1.
    status = run.runner(["git", "status", "--porcelain", "--untracked-files=no"], run.root)
    if status.returncode != 0:
        return None
    return sorted(line[3:] for line in status.stdout.splitlines() if line.strip())


def plan(run: "ReleaseRun") -> dict[str, Any]:
    """{} keeps the ordinary B4; otherwise the resume fields or blockers for the gate."""
    if not previous_b4_failed(run):
        return {}
    base = _approved_b4_base(run)
    if not base:
        return {"blockers": ["release-resume-approval-missing"]}
    heads = _remote_heads(run)
    if heads is None:
        return {"blockers": ["release-resume-remote-unavailable"]}
    remote_head = heads.get(f"refs/heads/{run.branch}", "")
    if not remote_head:
        return _unpublished_plan(run, base, heads, remote_head)
    lookup = run._command("B4-resume-lookup", [run.executable, "transfer", "pr-existing-for-branch", "--head",
                                               run.branch, "--state", "open", "--json"])
    payload = lookup.get("json")
    if not isinstance(payload, dict):
        return {"blockers": ["release-resume-lookup-invalid-response"]}
    if lookup["returncode"] == 2 and payload.get("result_status") == "MISS":
        return _unpublished_plan(run, base, heads, remote_head)
    number = payload.get("pr_number")
    if lookup["result_status"] != "PASS" or not isinstance(number, int) or number < 1:
        return {"blockers": ["release-resume-lookup-unavailable"]}
    view = run._command("B4-resume-view", ["gh", "pr", "view", str(number), "--json",
                                           "headRefOid,headRefName,baseRefName,state"])
    info = view.get("json")
    if view["result_status"] != "PASS" or not isinstance(info, dict):
        return {"blockers": ["release-resume-pr-view-unavailable"]}
    head = str(info.get("headRefOid") or "")
    if info.get("state") != "OPEN" or info.get("baseRefName") != "main" or info.get("headRefName") != run.branch or not head:
        return {"blockers": ["release-resume-pr-invalid"]}
    _commits, blocker = release_commits(run, base, head)
    if blocker:
        return {"blockers": [blocker]}
    main = run._command("B4-resume-main", ["gh", "api", "repos/{owner}/{repo}/branches/main", "--jq", ".commit.sha"])
    if main["result_status"] != "PASS" or main["stdout"].strip() != base:
        return {"blockers": ["release-resume-base-moved"]}
    return {"mode": RESUME_MODE, "pr_number": number, "source_head": head, "target_commit": base,
            "action": "complete the existing release PR with exact-head CI checks and post-merge handoff"}


def _unpublished_plan(run: "ReleaseRun", base: str, heads: dict[str, str], remote_head: str) -> dict[str, Any]:
    """K7: B4 stopped before its PR existed."""
    head = run._current_head()
    if head == base and not remote_head:
        return {}   # nothing committed yet: the ordinary B4 with its changed-paths check
    if heads.get("refs/heads/main", "") != base:
        return {"blockers": ["release-resume-base-moved"]}
    branch = run._command("B4-resume-branch", ["git", "branch", "--show-current"])
    if branch["result_status"] != "PASS" or branch["stdout"].strip() != run.branch:
        return {"blockers": ["release-resume-not-on-release-branch"]}
    commits, blocker = release_commits(run, base, head)
    if blocker:
        return {"blockers": [blocker]}
    if remote_head and remote_head not in {commit["sha"] for commit in commits}:
        return {"blockers": ["release-resume-remote-diverged"]}
    pending = _pending_paths(run)
    if pending is None:
        return {"blockers": ["release-resume-status-unavailable"]}
    message = f"Prepare release {run.version}"   # K1 publishes without a new commit; the option is still required
    if pending:
        kind = projection_kind(run, pending)
        if not kind:
            return {"blockers": ["release-resume-worktree-unexpected"]}
        message = next(subject for subject, value in projection_subjects(run.version).items() if value == kind)
    return {"mode": UNPUBLISHED_MODE, "source_head": head, "target_commit": base, "remote_head": remote_head,
            "commits": commits, "pending_paths": pending, "finish_message": message,
            "action": ("publish the release branch's existing B4 commits with work finish (K7): "
                       "commit pending projection files, push, PR, exact-head CI, merge and post-merge handoff")}


def finish_argv(run: "ReleaseRun", gate: dict[str, Any]) -> list[str]:
    from agentic_project_kit.release_run import RELEASE_CI_TIMEOUT_SECONDS

    argv = [run.executable, "work", "finish", "--branch", run.branch, "--title", f"Release {run.version}",
            "--message", str(gate["finish_message"])]
    for path in gate.get("pending_paths") or []:
        argv.extend(["--path", str(path)])
    return [*argv, "--ci-timeout-seconds", str(RELEASE_CI_TIMEOUT_SECONDS), "--execute", "--json"]


def complete(run: "ReleaseRun", gate: dict[str, Any]) -> dict[str, Any]:
    from agentic_project_kit.release_run import RELEASE_CI_TIMEOUT_SECONDS

    if gate.get("mode") == UNPUBLISHED_MODE:
        if run._current_head() != gate["source_head"]:
            return {"step_id": "B4", "result_status": "BLOCKED", "blockers": ["release-resume-head-drift"],
                    "next_action": f"Rerun agentic-kit release run --version {run.version} --json for a fresh resume gate."}
        # keeps B4.json, the evidence of the stopped attempt, so a later stop resumes again
        result = run._command("B4-resume-finish", finish_argv(run, gate), expected_status="PASS")
        result["step_id"] = "B4"
        return result
    result = run._command(
        "B4-resume-complete",   # keeps B4.json, the evidence of the stopped attempt
        [run.executable, "transfer", "pr-complete", str(gate["pr_number"]), "--expected-head-sha", gate["source_head"],
         "--timeout-seconds", str(RELEASE_CI_TIMEOUT_SECONDS), "--interval-seconds", "30",
         "--post-merge-complete", "--json"],
        expected_status="PASS",
    )
    result["step_id"] = "B4"
    return result
