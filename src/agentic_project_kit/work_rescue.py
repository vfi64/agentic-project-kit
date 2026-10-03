from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
import re
import subprocess
from typing import Callable


Runner = Callable[[list[str], Path], subprocess.CompletedProcess[str]]
MAIN_BRANCHES = {"main", "master"}


@dataclass(frozen=True)
class RescueInspection:
    branch: str
    detached: bool
    head_sha: str
    base_ref: str
    base_sha: str
    status_text: str
    unique_commit_count: int
    head_is_ancestor_of_base: bool
    rescue_branch: str
    signature: str

    @property
    def dirty(self) -> bool:
        return bool(self.status_text.strip())

    @property
    def has_unique_commits(self) -> bool:
        return self.unique_commit_count > 0

    @property
    def rescue_required(self) -> bool:
        return self.dirty or self.has_unique_commits


def _run(argv: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(argv, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)


def _step(name: str, completed: subprocess.CompletedProcess[str], *, allowed: set[int] | None = None) -> dict[str, object]:
    allowed_returncodes = allowed or {0}
    return {
        "name": name,
        "argv": list(completed.args) if isinstance(completed.args, list) else [],
        "returncode": completed.returncode,
        "ok": completed.returncode in allowed_returncodes,
        "allowed_returncodes": sorted(allowed_returncodes),
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def _slug_branch_part(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._/-]+", "-", value.strip())
    slug = re.sub(r"/{2,}", "/", slug).strip("/-.")
    return slug or "detached"


def _default_rescue_branch(*, branch: str, detached: bool, head_sha: str, status_text: str) -> str:
    base = "detached" if detached else _slug_branch_part(branch)
    digest = hashlib.sha256(f"{head_sha}\0{status_text}".encode("utf-8")).hexdigest()[:10]
    suffix = f"{head_sha[:8]}-{digest}" if status_text.strip() else head_sha[:8]
    return f"rescue/{base}-{suffix}"


def _rescue_signature(inspection: RescueInspection) -> str:
    material = "\0".join(
        [
            inspection.branch,
            str(inspection.detached),
            inspection.head_sha,
            inspection.base_ref,
            inspection.base_sha,
            inspection.status_text,
            str(inspection.unique_commit_count),
            inspection.rescue_branch,
        ]
    )
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def _rev_parse(runner: Runner, root: Path, ref: str) -> tuple[subprocess.CompletedProcess[str], str]:
    completed = runner(["git", "rev-parse", "--verify", ref], root)
    return completed, completed.stdout.strip() if completed.returncode == 0 else ""


def _is_ancestor(runner: Runner, root: Path, ancestor: str, descendant: str) -> tuple[subprocess.CompletedProcess[str], bool]:
    completed = runner(["git", "merge-base", "--is-ancestor", ancestor, descendant], root)
    return completed, completed.returncode == 0


def _unique_commit_count(runner: Runner, root: Path, base_ref: str) -> tuple[subprocess.CompletedProcess[str], int]:
    completed = runner(["git", "rev-list", "--count", f"{base_ref}..HEAD"], root)
    if completed.returncode != 0:
        return completed, 0
    try:
        return completed, int(completed.stdout.strip() or "0")
    except ValueError:
        return completed, 0


def inspect_work_rescue(
    root: Path | str = ".",
    *,
    base_ref: str = "origin/main",
    rescue_branch: str = "",
    runner: Runner = _run,
) -> tuple[RescueInspection | None, list[dict[str, object]]]:
    base = Path(root)
    steps: list[dict[str, object]] = []

    branch_completed = runner(["git", "branch", "--show-current"], base)
    steps.append(_step("current-branch", branch_completed))
    branch = branch_completed.stdout.strip() if branch_completed.returncode == 0 else ""
    detached = branch == ""

    head_completed, head_sha = _rev_parse(runner, base, "HEAD")
    steps.append(_step("head-sha", head_completed))
    base_completed, base_sha = _rev_parse(runner, base, base_ref)
    steps.append(_step("base-sha", base_completed))

    status_completed = runner(["git", "status", "--porcelain=v1", "--untracked-files=all"], base)
    steps.append(_step("status-porcelain", status_completed))
    status_text = status_completed.stdout if status_completed.returncode == 0 else ""

    unique_completed, unique_count = _unique_commit_count(runner, base, base_ref)
    steps.append(_step("unique-commit-count", unique_completed))

    ancestor_completed, head_is_ancestor = _is_ancestor(runner, base, "HEAD", base_ref)
    steps.append(_step("head-contained-in-base", ancestor_completed, allowed={0, 1}))

    if any(not bool(step["ok"]) for step in steps):
        return None, steps

    selected_rescue_branch = rescue_branch.strip() or _default_rescue_branch(
        branch=branch,
        detached=detached,
        head_sha=head_sha,
        status_text=status_text,
    )
    inspection = RescueInspection(
        branch=branch,
        detached=detached,
        head_sha=head_sha,
        base_ref=base_ref,
        base_sha=base_sha,
        status_text=status_text,
        unique_commit_count=unique_count,
        head_is_ancestor_of_base=head_is_ancestor,
        rescue_branch=selected_rescue_branch,
        signature="",
    )
    inspection = RescueInspection(
        branch=inspection.branch,
        detached=inspection.detached,
        head_sha=inspection.head_sha,
        base_ref=inspection.base_ref,
        base_sha=inspection.base_sha,
        status_text=inspection.status_text,
        unique_commit_count=inspection.unique_commit_count,
        head_is_ancestor_of_base=inspection.head_is_ancestor_of_base,
        rescue_branch=inspection.rescue_branch,
        signature=_rescue_signature(inspection),
    )
    return inspection, steps


def _branch_exists(runner: Runner, root: Path, branch: str) -> tuple[subprocess.CompletedProcess[str], bool]:
    completed = runner(["git", "rev-parse", "--verify", f"refs/heads/{branch}"], root)
    return completed, completed.returncode == 0


def _payload(
    *,
    inspection: RescueInspection | None,
    steps: list[dict[str, object]],
    execute: bool,
    blockers: list[str] | None = None,
) -> dict[str, object]:
    all_blockers = [*(blockers or ()), *[str(step["name"]) for step in steps if not step["ok"]]]
    result_status = "PASS" if not all_blockers else "BLOCKED"
    rescue_required = bool(inspection and inspection.rescue_required)
    payload: dict[str, object] = {
        "schema_version": 1,
        "kind": "human_work_rescue_result",
        "action": "work-rescue",
        "result_status": result_status,
        "returncode": 0 if result_status == "PASS" else 2,
        "dry_run": not execute,
        "execute": execute,
        "destructive": rescue_required,
        "remote_effect": "none",
        "remote_effects": ["none"],
        "blockers": all_blockers,
        "steps": steps,
        "next_action": "Workflow completed.",
    }
    if inspection is not None:
        planned_actions: list[str] = []
        if inspection.rescue_required:
            planned_actions.append("create-rescue-branch")
            if inspection.dirty:
                planned_actions.append("commit-local-changes-on-rescue-branch")
            planned_actions.append("realign-main-to-base")
        payload.update(
            {
                "branch": inspection.branch,
                "detached": inspection.detached,
                "head_sha": inspection.head_sha,
                "base_ref": inspection.base_ref,
                "base_sha": inspection.base_sha,
                "rescue_branch": inspection.rescue_branch,
                "signature": inspection.signature,
                "dirty": inspection.dirty,
                "unique_commit_count": inspection.unique_commit_count,
                "rescue_required": inspection.rescue_required,
                "planned_actions": planned_actions,
            }
        )
        if not execute and inspection.rescue_required and result_status == "PASS":
            payload["next_action"] = "Review the rescue plan, then rerun with --execute and the matching --expected-signature."
    if result_status != "PASS":
        payload["next_action"] = "Inspect blockers before running rescue."
    return payload


def rescue_main_work(
    root: Path | str = ".",
    *,
    execute: bool = False,
    expected_signature: str = "",
    rescue_branch: str = "",
    base_ref: str = "origin/main",
    runner: Runner = _run,
) -> dict[str, object]:
    base = Path(root)
    inspection, steps = inspect_work_rescue(
        base,
        base_ref=base_ref,
        rescue_branch=rescue_branch,
        runner=runner,
    )
    blockers: list[str] = []
    if inspection is None:
        return _payload(inspection=None, steps=steps, execute=execute, blockers=blockers)

    if not inspection.detached and inspection.branch not in MAIN_BRANCHES:
        blockers.append("not-main-or-detached")
    if inspection.rescue_required:
        branch_exists_completed, exists = _branch_exists(runner, base, inspection.rescue_branch)
        steps.append(_step("rescue-branch-available", branch_exists_completed, allowed={1, 128}))
        if exists:
            blockers.append("rescue-branch-exists")
        if execute and not expected_signature:
            blockers.append("expected-signature-required")
        if expected_signature and expected_signature != inspection.signature:
            blockers.append("signature-mismatch")
    if blockers or any(not bool(step["ok"]) for step in steps) or not execute or not inspection.rescue_required:
        return _payload(inspection=inspection, steps=steps, execute=execute, blockers=blockers)

    # workspace_mutation_lock: execution is guarded by the dry-run signature and
    # verified rescue-branch containment before main is reset to the local base ref.
    if inspection.dirty:
        switch_rescue = runner(["git", "switch", "-c", inspection.rescue_branch, "HEAD"], base)
        steps.append(_step("create-and-switch-rescue-branch", switch_rescue))
        if switch_rescue.returncode == 0:
            add_completed = runner(["git", "add", "-A"], base)
            steps.append(_step("stage-local-changes", add_completed))
        if steps[-1]["ok"]:
            commit_completed = runner(
                ["git", "commit", "-m", "Rescue local changes before main realignment"],
                base,
            )
            steps.append(_step("commit-local-changes-on-rescue-branch", commit_completed))
    else:
        create_branch = runner(["git", "branch", inspection.rescue_branch, "HEAD"], base)
        steps.append(_step("create-rescue-branch", create_branch))

    if any(not bool(step["ok"]) for step in steps):
        return _payload(inspection=inspection, steps=steps, execute=execute, blockers=blockers)

    contain_completed, contained = _is_ancestor(runner, base, inspection.head_sha, inspection.rescue_branch)
    steps.append(_step("verify-rescue-contains-original-head", contain_completed))
    if not contained:
        blockers.append("rescue-does-not-contain-original-head")
        return _payload(inspection=inspection, steps=steps, execute=execute, blockers=blockers)

    if inspection.detached:
        switch_main = runner(["git", "switch", "main"], base)
        steps.append(_step("switch-main", switch_main))
    elif inspection.dirty:
        switch_main = runner(["git", "switch", inspection.branch], base)
        steps.append(_step("switch-main", switch_main))

    if any(not bool(step["ok"]) for step in steps):
        return _payload(inspection=inspection, steps=steps, execute=execute, blockers=blockers)

    reset_main = runner(["git", "reset", "--hard", inspection.base_ref], base)
    steps.append(_step("realign-main-to-base", reset_main))

    status_after = runner(["git", "status", "--porcelain=v1", "--untracked-files=all"], base)
    steps.append(_step("verify-clean-status", status_after))
    if status_after.returncode == 0 and status_after.stdout.strip():
        blockers.append("worktree-not-clean-after-rescue")

    main_after, main_sha = _rev_parse(runner, base, "HEAD")
    steps.append(_step("verify-main-head", main_after))
    if main_sha and main_sha != inspection.base_sha:
        blockers.append("main-not-aligned-to-base")

    return _payload(inspection=inspection, steps=steps, execute=execute, blockers=blockers)
