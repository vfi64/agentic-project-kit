from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
import json
from pathlib import Path
import re

from agentic_project_kit.release import CommandResult, run_command


PatchCycleRunner = Callable[[Path, Sequence[str]], CommandResult]

PATCH_CYCLE_STEPS: tuple[str, ...] = (
    "PATCH_SLICE",
    "PATCH_PR",
    "HANDOFF_REFRESH_SLICE",
    "HANDOFF_REFRESH_PR",
    "POST_MERGE_CLEAN_STATE",
)


@dataclass(frozen=True)
class PatchCycleStep:
    id: str
    status: str
    allowed_next_actions: tuple[str, ...]
    blockers: tuple[str, ...] = ()
    evidence: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "status": self.status,
            "allowed_next_actions": list(self.allowed_next_actions),
            "blockers": list(self.blockers),
            "evidence": list(self.evidence),
        }


@dataclass(frozen=True)
class PatchCycleStatus:
    schema_version: int
    kind: str
    current_stage: str
    result_status: str
    branch: str
    head_sha: str
    origin_main_sha: str
    worktree_clean: bool
    dirty_paths: tuple[str, ...]
    pr_number: int | None
    pr: dict[str, object] | None
    handoff_generated_head: str
    handoff_validation_status: str
    handoff_fresh_for_head: bool
    steps: tuple[PatchCycleStep, ...]
    next_action: str
    recommended_next_action: str
    disabled_actions: tuple[dict[str, object], ...]
    traffic_lights: dict[str, str]
    blockers: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "kind": self.kind,
            "current_stage": self.current_stage,
            "result_status": self.result_status,
            "branch": self.branch,
            "head_sha": self.head_sha,
            "origin_main_sha": self.origin_main_sha,
            "worktree_clean": self.worktree_clean,
            "dirty_paths": list(self.dirty_paths),
            "pr_number": self.pr_number,
            "pr": self.pr,
            "handoff_generated_head": self.handoff_generated_head,
            "handoff_validation_status": self.handoff_validation_status,
            "handoff_fresh_for_head": self.handoff_fresh_for_head,
            "steps": [step.as_dict() for step in self.steps],
            "next_action": self.next_action,
            "recommended_next_action": self.recommended_next_action,
            "disabled_actions": list(self.disabled_actions),
            "traffic_lights": self.traffic_lights,
            "blockers": list(self.blockers),
        }


def build_patch_cycle_status(
    project_root: Path,
    *,
    pr_number: int | None = None,
    include_ci: bool = False,
    command_runner: PatchCycleRunner | None = None,
) -> PatchCycleStatus:
    runner = command_runner or run_command
    branch = _stdout(runner(project_root, ["git", "branch", "--show-current"]))
    head_sha = _stdout(runner(project_root, ["git", "rev-parse", "HEAD"]))
    origin_main_sha = _stdout(runner(project_root, ["git", "rev-parse", "origin/main"]))
    status_result = runner(project_root, ["git", "status", "--short", "--untracked-files=all"])
    dirty_paths = tuple(line.strip() for line in status_result.stdout.splitlines() if line.strip())
    worktree_clean = status_result.returncode == 0 and not dirty_paths
    handoff_validation = _read_handoff_validation(project_root)
    handoff_generated_head = str(handoff_validation.get("generated_head") or "")
    handoff_validation_status = str(handoff_validation.get("status") or "MISSING")
    handoff_fresh_for_head = bool(head_sha and handoff_generated_head == head_sha)
    pr = _read_pr(project_root, pr_number, include_ci, runner) if pr_number is not None else None
    current_stage = _current_stage(
        branch=branch,
        worktree_clean=worktree_clean,
        handoff_fresh_for_head=handoff_fresh_for_head,
    )
    blockers = _global_blockers(
        branch=branch,
        head_sha=head_sha,
        origin_main_sha=origin_main_sha,
        dirty_paths=dirty_paths,
        pr=pr,
    )
    steps = _steps_for(
        current_stage=current_stage,
        branch=branch,
        worktree_clean=worktree_clean,
        dirty_paths=dirty_paths,
        pr_number=pr_number,
        pr=pr,
        handoff_fresh_for_head=handoff_fresh_for_head,
        head_sha=head_sha,
        origin_main_sha=origin_main_sha,
    )
    next_action = _next_action(current_stage, blockers, steps)
    disabled_actions = _disabled_actions(steps, blockers)
    traffic_lights = _traffic_lights(steps, blockers)
    result_status = "BLOCKED" if blockers else ("PASS" if current_stage == "POST_MERGE_CLEAN_STATE" else "READY")
    return PatchCycleStatus(
        schema_version=1,
        kind="patch_cycle_workflow_status",
        current_stage=current_stage,
        result_status=result_status,
        branch=branch,
        head_sha=head_sha,
        origin_main_sha=origin_main_sha,
        worktree_clean=worktree_clean,
        dirty_paths=dirty_paths,
        pr_number=pr_number,
        pr=pr,
        handoff_generated_head=handoff_generated_head,
        handoff_validation_status=handoff_validation_status,
        handoff_fresh_for_head=handoff_fresh_for_head,
        steps=steps,
        next_action=next_action,
        recommended_next_action=next_action,
        disabled_actions=disabled_actions,
        traffic_lights=traffic_lights,
        blockers=blockers,
    )


def render_patch_cycle_status(status: PatchCycleStatus) -> str:
    lines = [
        "PATCH_CYCLE_WORKFLOW_STATUS",
        f"RESULT_STATUS={status.result_status}",
        f"CURRENT_STAGE={status.current_stage}",
        f"BRANCH={status.branch or '<unknown>'}",
        f"HEAD={status.head_sha or '<unknown>'}",
        f"ORIGIN_MAIN={status.origin_main_sha or '<unknown>'}",
        f"WORKTREE_CLEAN={str(status.worktree_clean).lower()}",
        f"HANDOFF_VALIDATION_STATUS={status.handoff_validation_status}",
        f"HANDOFF_FRESH_FOR_HEAD={str(status.handoff_fresh_for_head).lower()}",
    ]
    if status.pr_number is not None:
        lines.append(f"PR={status.pr_number}")
    for step in status.steps:
        lines.append(
            "STEP="
            + "|".join(
                [
                    step.id,
                    step.status,
                    ",".join(step.allowed_next_actions) or "<none>",
                    ",".join(step.blockers) or "<none>",
                ]
            )
        )
    for blocker in status.blockers:
        lines.append(f"BLOCKER={blocker}")
    lines.append(f"NEXT={status.next_action}")
    lines.append(f"FINAL_SIGNAL={'f' if status.blockers else 'd'}")
    return "\n".join(lines) + "\n"


def _stdout(result: CommandResult) -> str:
    return (result.stdout or "").strip() if result.returncode == 0 else ""


def _read_handoff_validation(project_root: Path) -> dict[str, object]:
    path = project_root / "docs/reports/handoff-packages/latest/validation_report.json"
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"status": "INVALID"}
    return payload


def _read_pr(project_root: Path, pr_number: int, include_ci: bool, runner: PatchCycleRunner) -> dict[str, object]:
    fields = "number,state,mergeStateStatus,headRefName,headRefOid,isDraft,url"
    if include_ci:
        fields += ",statusCheckRollup"
    result = runner(
        project_root,
        [
            "gh",
            "pr",
            "view",
            str(pr_number),
            "--json",
            fields,
        ],
    )
    if result.returncode != 0:
        return {
            "number": pr_number,
            "available": False,
            "error": (result.stderr or result.stdout).strip(),
        }
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        return {"number": pr_number, "available": False, "error": f"invalid_pr_json:{exc}"}
    payload["available"] = True
    if include_ci:
        payload["checks"] = _summarize_checks(payload.get("statusCheckRollup"))
        payload["checks_status"] = _checks_status(payload["checks"])
    return payload


def _summarize_checks(raw_checks: object) -> list[dict[str, object]]:
    if not isinstance(raw_checks, list):
        return []
    checks: list[dict[str, object]] = []
    for item in raw_checks:
        if not isinstance(item, dict):
            continue
        checks.append(
            {
                "name": item.get("name") or item.get("workflowName") or item.get("context") or "<unknown>",
                "status": item.get("status"),
                "conclusion": item.get("conclusion"),
                "state": item.get("state"),
            }
        )
    return checks


def _checks_status(checks: object) -> str:
    if not isinstance(checks, list) or not checks:
        return "UNKNOWN"
    conclusions = {str(item.get("conclusion") or item.get("state") or item.get("status") or "").upper() for item in checks if isinstance(item, dict)}
    if any(value in {"FAILURE", "FAILED", "CANCELLED", "TIMED_OUT", "ACTION_REQUIRED"} for value in conclusions):
        return "FAIL"
    if any(value in {"PENDING", "IN_PROGRESS", "QUEUED", "REQUESTED", "WAITING"} for value in conclusions):
        return "PENDING"
    if conclusions and all(value in {"SUCCESS", "COMPLETED", "NEUTRAL", "SKIPPED"} for value in conclusions):
        return "PASS"
    return "UNKNOWN"


def _current_stage(*, branch: str, worktree_clean: bool, handoff_fresh_for_head: bool) -> str:
    if branch == "main":
        return "POST_MERGE_CLEAN_STATE" if worktree_clean and handoff_fresh_for_head else "HANDOFF_REFRESH_SLICE"
    if _is_handoff_refresh_branch(branch):
        return "HANDOFF_REFRESH_PR" if worktree_clean else "HANDOFF_REFRESH_SLICE"
    return "PATCH_PR" if worktree_clean else "PATCH_SLICE"


def _global_blockers(
    *,
    branch: str,
    head_sha: str,
    origin_main_sha: str,
    dirty_paths: tuple[str, ...],
    pr: dict[str, object] | None,
) -> tuple[str, ...]:
    blockers: list[str] = []
    if not branch:
        blockers.append("branch_unknown")
    if not head_sha:
        blockers.append("head_unknown")
    if branch == "main" and dirty_paths:
        blockers.append("main_dirty")
    if branch == "main" and origin_main_sha and head_sha and head_sha != origin_main_sha:
        blockers.append("main_not_synced_with_origin_main")
    if pr is not None and pr.get("available") is False:
        blockers.append("pr_metadata_unavailable")
    if pr is not None and pr.get("checks_status") == "FAIL":
        blockers.append("pr_checks_failing")
    return tuple(blockers)


def _steps_for(
    *,
    current_stage: str,
    branch: str,
    worktree_clean: bool,
    dirty_paths: tuple[str, ...],
    pr_number: int | None,
    pr: dict[str, object] | None,
    handoff_fresh_for_head: bool,
    head_sha: str,
    origin_main_sha: str,
) -> tuple[PatchCycleStep, ...]:
    patch_pr_state = _pr_state(pr)
    return (
        PatchCycleStep(
            "PATCH_SLICE",
            "ACTIVE" if current_stage == "PATCH_SLICE" else ("DONE" if current_stage in {"PATCH_PR", "HANDOFF_REFRESH_SLICE", "HANDOFF_REFRESH_PR", "POST_MERGE_CLEAN_STATE"} else "PENDING"),
            _actions("protected_diff_plan", "commit", "push_current") if current_stage == "PATCH_SLICE" else (),
            ("worktree_dirty",) if current_stage == "PATCH_SLICE" and dirty_paths else (),
            dirty_paths[:20],
        ),
        PatchCycleStep(
            "PATCH_PR",
            "ACTIVE" if current_stage == "PATCH_PR" else ("DONE" if current_stage in {"HANDOFF_REFRESH_SLICE", "HANDOFF_REFRESH_PR", "POST_MERGE_CLEAN_STATE"} else "PENDING"),
            _actions("pr_create_complete", "pr_status") if current_stage == "PATCH_PR" else (),
            _pr_blockers(pr_number, pr),
            _pr_evidence(pr_number, patch_pr_state),
        ),
        PatchCycleStep(
            "HANDOFF_REFRESH_SLICE",
            "ACTIVE" if current_stage == "HANDOFF_REFRESH_SLICE" else ("DONE" if current_stage in {"HANDOFF_REFRESH_PR", "POST_MERGE_CLEAN_STATE"} and handoff_fresh_for_head else "PENDING"),
            _actions("admin_refresh_pr", "prepare_successor_handoff", "publish_last_report") if current_stage == "HANDOFF_REFRESH_SLICE" else (),
            () if branch != "main" or not worktree_clean or handoff_fresh_for_head else ("handoff_generated_head_mismatch",),
            (f"handoff_fresh_for_head={handoff_fresh_for_head}",),
        ),
        PatchCycleStep(
            "HANDOFF_REFRESH_PR",
            "ACTIVE" if current_stage == "HANDOFF_REFRESH_PR" else ("DONE" if current_stage == "POST_MERGE_CLEAN_STATE" else "PENDING"),
            _actions("pr_create_complete", "pr_status") if current_stage == "HANDOFF_REFRESH_PR" else (),
            (),
            (f"branch={branch}",) if _is_handoff_refresh_branch(branch) else (),
        ),
        PatchCycleStep(
            "POST_MERGE_CLEAN_STATE",
            "DONE" if current_stage == "POST_MERGE_CLEAN_STATE" else "PENDING",
            _actions("sync_main", "post_merge_check", "repo_status") if current_stage == "POST_MERGE_CLEAN_STATE" else (),
            () if branch != "main" or (worktree_clean and head_sha == origin_main_sha) else ("main_not_clean_or_not_synced",),
            (f"origin_main={origin_main_sha}",) if origin_main_sha else (),
        ),
    )


def _actions(*names: str) -> tuple[str, ...]:
    mapping = {
        "protected_diff_plan": "agentic-kit transfer protected-diff-plan --label <slice-label>",
        "commit": "agentic-kit transfer commit --message <message> --path <explicit-path>",
        "push_current": "agentic-kit transfer push-current",
        "pr_create_complete": "agentic-kit transfer pr-create-complete --title <title> --body <body>",
        "pr_status": "agentic-kit transfer pr-status <pr-number> --json",
        "admin_refresh_pr": "agentic-kit transfer admin-refresh-pr --after-pr <pr-number> --json",
        "prepare_successor_handoff": "agentic-kit transfer prepare-successor-handoff --render-prompt",
        "publish_last_report": "agentic-kit transfer publish-last-report",
        "sync_main": "agentic-kit transfer sync-main",
        "post_merge_check": "agentic-kit transfer post-merge-check",
        "repo_status": "agentic-kit transfer repo-status",
    }
    return tuple(mapping[name] for name in names)


def _next_action(
    current_stage: str,
    blockers: tuple[str, ...],
    steps: tuple[PatchCycleStep, ...],
) -> str:
    if blockers:
        return "Diagnose blockers before continuing: " + ", ".join(blockers)
    active = next((step for step in steps if step.id == current_stage), None)
    if active and active.allowed_next_actions:
        return active.allowed_next_actions[0]
    if current_stage == "POST_MERGE_CLEAN_STATE":
        return "Patch cycle is clean; start the next planned slice when ready."
    return "Inspect patch-cycle status and choose the next wrapper-backed action."


def _pr_state(pr: dict[str, object] | None) -> str:
    if not pr:
        return "unknown"
    if pr.get("available") is False:
        return "unavailable"
    return str(pr.get("state") or "unknown").lower()


def _pr_blockers(pr_number: int | None, pr: dict[str, object] | None) -> tuple[str, ...]:
    if pr_number is None:
        return ()
    if pr and pr.get("available") is False:
        return ("pr_metadata_unavailable",)
    if pr and pr.get("checks_status") == "FAIL":
        return ("pr_checks_failing",)
    return ()


def _pr_evidence(pr_number: int | None, pr_state: str) -> tuple[str, ...]:
    if pr_number is None:
        return ()
    return (f"pr={pr_number}", f"pr_state={pr_state}")


def _disabled_actions(steps: tuple[PatchCycleStep, ...], blockers: tuple[str, ...]) -> tuple[dict[str, object], ...]:
    disabled: list[dict[str, object]] = []
    for step in steps:
        if step.status == "ACTIVE":
            continue
        disabled.append({"step": step.id, "reason": f"step_status_{step.status.lower()}"})
    for blocker in blockers:
        disabled.append({"step": "GLOBAL", "reason": blocker})
    return tuple(disabled)


def _traffic_lights(steps: tuple[PatchCycleStep, ...], blockers: tuple[str, ...]) -> dict[str, str]:
    lights: dict[str, str] = {}
    for step in steps:
        if step.blockers:
            lights[step.id] = "red"
        elif step.status == "DONE":
            lights[step.id] = "green"
        elif step.status == "ACTIVE":
            lights[step.id] = "yellow"
        else:
            lights[step.id] = "gray"
    if blockers:
        lights["GLOBAL"] = "red"
    return lights


def _is_handoff_refresh_branch(branch: str) -> bool:
    return bool(re.match(r"^(docs|codex)/post-pr\\d+-handoff-refresh$", branch)) or (
        "handoff" in branch and "refresh" in branch
    )
