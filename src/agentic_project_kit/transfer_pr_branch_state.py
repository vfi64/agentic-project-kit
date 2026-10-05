from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

Run = Callable[..., subprocess.CompletedProcess[str]]


def _default_run(argv: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(argv, cwd=cwd, text=True, capture_output=True, check=False)


@dataclass(frozen=True)
class BranchDiffStatus:
    base: str
    head: str
    base_ref: str
    no_content_diff: bool
    blockers: tuple[str, ...] = ()
    merged_pr: dict[str, object] | None = None
    steps: tuple[dict[str, object], ...] = ()

    def as_payload(self) -> dict[str, object]:
        return {
            "base": self.base,
            "head": self.head,
            "base_ref": self.base_ref,
            "no_content_diff": self.no_content_diff,
            "blockers": list(self.blockers),
            "merged_pr": self.merged_pr,
            "steps": list(self.steps),
        }


def _step(name: str, completed: subprocess.CompletedProcess[str]) -> dict[str, object]:
    return {
        "name": name,
        "argv": list(completed.args),
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "ok": completed.returncode == 0,
    }


def _resolve_base_ref(root: Path, base: str, run: Run) -> tuple[str, list[dict[str, object]], list[str]]:
    steps: list[dict[str, object]] = []
    blockers: list[str] = []
    candidates = [f"origin/{base}", base] if not base.startswith("origin/") else [base]
    for candidate in candidates:
        completed = run(["git", "rev-parse", "--verify", candidate], cwd=root)
        steps.append(_step(f"resolve-base-ref:{candidate}", completed))
        if completed.returncode == 0:
            return candidate, steps, blockers
    blockers.append("base_ref_not_found")
    return candidates[0], steps, blockers


def detect_branch_no_content_diff(
    root: Path | str,
    *,
    base: str,
    head: str,
    run: Run = _default_run,
) -> BranchDiffStatus:
    root_path = Path(root)
    steps: list[dict[str, object]] = []
    blockers: list[str] = []
    base_ref, base_steps, base_blockers = _resolve_base_ref(root_path, base, run)
    steps.extend(base_steps)
    blockers.extend(base_blockers)
    if blockers:
        return BranchDiffStatus(base=base, head=head, base_ref=base_ref, no_content_diff=False, blockers=tuple(blockers), steps=tuple(steps))

    diff = run(["git", "diff", "--quiet", base_ref, head], cwd=root_path)
    steps.append(_step("git-diff-base-head", diff))
    if diff.returncode == 0:
        merged_pr = _latest_merged_pr_for_branch(root_path, base=base, head=head, run=run, steps=steps)
        return BranchDiffStatus(base=base, head=head, base_ref=base_ref, no_content_diff=True, merged_pr=merged_pr, steps=tuple(steps))
    if diff.returncode == 1:
        return BranchDiffStatus(base=base, head=head, base_ref=base_ref, no_content_diff=False, steps=tuple(steps))
    blockers.append("git_diff_failed")
    return BranchDiffStatus(base=base, head=head, base_ref=base_ref, no_content_diff=False, blockers=tuple(blockers), steps=tuple(steps))


def _latest_merged_pr_for_branch(
    root: Path,
    *,
    base: str,
    head: str,
    run: Run,
    steps: list[dict[str, object]],
) -> dict[str, object] | None:
    completed = run(
        [
            "gh",
            "pr",
            "list",
            "--head",
            head,
            "--base",
            base,
            "--state",
            "merged",
            "--limit",
            "10",
            "--json",
            "number,url,state,mergedAt,headRefName,baseRefName,title",
        ],
        cwd=root,
    )
    steps.append(_step("gh-pr-list-merged-for-no-diff-head", completed))
    if completed.returncode != 0:
        return None
    try:
        parsed = json.loads(completed.stdout or "[]")
    except json.JSONDecodeError:
        return None
    if not isinstance(parsed, list) or not parsed:
        return None
    first = parsed[0]
    return first if isinstance(first, dict) else None
