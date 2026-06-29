from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Literal

WorkPhase = Literal["start", "changes", "check", "finish", "recover"]


@dataclass(frozen=True)
class WorkCyclePhaseView:
    phase_id: WorkPhase
    label: str
    command_hint: str
    tooltip: str
    is_current: bool
    is_available: bool


@dataclass(frozen=True)
class WorkResultMessage:
    headline: str
    detail: str
    blockers_human: tuple[str, ...]
    suggested_next: str
    allow_confirm_publish: bool = False
    allow_confirm_discard: bool = False


@dataclass(frozen=True)
class ChangedPath:
    path: str
    selected: bool = True


@dataclass(frozen=True)
class WorkBranchOption:
    option_id: str
    label: str
    branch: str
    purpose: str
    safe_default: bool = False


_PHASE_DEFINITIONS: tuple[tuple[WorkPhase, str, str, str], ...] = (
    (
        "start",
        "Start work",
        "agentic-kit work start --branch <generated> --json",
        "Create a safe workspace for this change and run the standard startup checks.",
    ),
    (
        "changes",
        "Make changes",
        "Use the file-transfer task editor",
        "Describe the work for the assistant; this phase does not run a repository command.",
    ),
    (
        "check",
        "Check",
        "agentic-kit work check --profile code --json",
        "Run the standard checks before publishing the change.",
    ),
    (
        "finish",
        "Finish & publish",
        "agentic-kit work finish --dry-run/--execute --json",
        "Preview, then explicitly confirm saving, publishing, and closing the work slice.",
    ),
    (
        "recover",
        "Needs recovery",
        "agentic-kit work recover --json",
        "Run safe recovery checks when the repository or workflow state needs attention.",
    ),
)

_AVAILABLE_PHASES_BY_CURRENT: dict[WorkPhase, frozenset[WorkPhase]] = {
    "start": frozenset({"start"}),
    "changes": frozenset({"changes", "check"}),
    "check": frozenset({"changes", "check"}),
    "finish": frozenset({"check", "finish"}),
    "recover": frozenset({"recover"}),
}


BLOCKER_EXPLANATIONS: dict[str, str] = {
    "repo-status": "The repository state needs attention.",
    "command-reference-check": "The command reference needs to be refreshed.",
    "ruff": "Code style needs cleanup.",
    "pytest-core": "Some tests are failing; the code needs fixing.",
    "docs-audit": "Documentation checks need attention.",
    "audit-doc-currency": "Current-state documentation is stale.",
    "audit-ns-legacy-references": "Legacy command references need review.",
    "standard-error-scan": "A release or workflow safety scan found a problem.",
    "protected-diff-plan": "A protected-file change needs review before publishing.",
    "path-selection": "Choose which changed files should be included.",
    "main-branch": "Discard all changes is blocked on main.",
    "signature-mismatch": "The worktree changed after the dry-run preview.",
    "current-branch": "The current branch could not be identified.",
    "status-porcelain": "The changed files could not be listed.",
    "reset-hard": "Tracked changes could not be discarded.",
    "clean-untracked": "Untracked files could not be removed.",
    "commit": "The selected files could not be saved.",
    "rules-acknowledge": "The project rules acknowledgement step needs attention.",
    "push-current": "The change could not be published to the server.",
    "pr-create-complete": "The publish-and-review workflow did not complete.",
    "sync-main": "The local main branch could not be synchronized.",
    "post-merge-check": "The post-merge repository check needs attention.",
    "restore-known-volatile": "Known volatile local files could not be restored safely.",
    "normalize-session": "The local session could not be normalized safely.",
    "conflict-status": "A conflict or interrupted operation needs diagnosis.",
    "patch-cycle-status": "The patch-cycle state needs diagnosis.",
}

_VOLATILE_STATUS_PATH_PREFIXES = (
    ".agentic/transfer/outbox/",
    "docs/reports/terminal/transfer_handoff_reports/latest-",
)


def derive_work_phase(
    *,
    repo_clean: bool,
    on_feature_branch: bool,
    has_blockers: bool,
    has_changes: bool = False,
    last_check_passed: bool = False,
) -> WorkPhase:
    """Derive a conservative human work phase from available read-only signals."""
    if has_blockers:
        return "recover"
    if not on_feature_branch:
        return "start" if repo_clean else "recover"
    if has_changes and last_check_passed:
        return "finish"
    if has_changes:
        return "check"
    return "changes"


def build_work_cycle_views(current: WorkPhase) -> tuple[WorkCyclePhaseView, ...]:
    views: list[WorkCyclePhaseView] = []
    available_phases = _AVAILABLE_PHASES_BY_CURRENT[current]
    for phase_id, label, command_hint, tooltip in _PHASE_DEFINITIONS:
        views.append(
            WorkCyclePhaseView(
                phase_id=phase_id,
                label=label,
                command_hint=command_hint,
                tooltip=tooltip,
                is_current=phase_id == current,
                is_available=phase_id in available_phases,
            )
        )
    return tuple(views)


def humanize_work_result(payload: dict[str, Any]) -> WorkResultMessage:
    status = str(payload.get("result_status", "")).upper()
    action = str(payload.get("action", ""))
    dry_run = bool(payload.get("dry_run"))
    blockers = tuple(str(item) for item in payload.get("blockers", ()) if str(item))
    if status == "PASS" and action == "work-finish" and dry_run:
        paths = payload.get("paths", ())
        path_count = len(paths) if isinstance(paths, list) else 0
        return WorkResultMessage(
            headline="Ready to publish.",
            detail=(
                f"The dry-run passed for {path_count} selected file"
                f"{'' if path_count == 1 else 's'}. Review it, then confirm publish."
            ),
            blockers_human=(),
            suggested_next="Confirm publish",
            allow_confirm_publish=True,
        )
    if status == "PASS" and action == "work-discard-changes" and dry_run:
        paths = payload.get("changed_paths", ())
        path_count = len(paths) if isinstance(paths, list) else 0
        if path_count == 0:
            return WorkResultMessage(
                headline="Nothing to discard.",
                detail="The dry-run found no feature-branch changes.",
                blockers_human=(),
                suggested_next="Continue with the next safe step.",
            )
        return WorkResultMessage(
            headline="Ready to discard changes.",
            detail=(
                f"The dry-run found {path_count} changed path"
                f"{'' if path_count == 1 else 's'}. Confirm only if you want to delete them."
            ),
            blockers_human=(),
            suggested_next="Confirm discard",
            allow_confirm_discard=True,
        )
    if status == "PASS":
        return WorkResultMessage(
            headline="Done.",
            detail=str(payload.get("next_action") or "The workflow step completed successfully."),
            blockers_human=(),
            suggested_next="Continue with the next safe step.",
        )
    human_blockers = tuple(BLOCKER_EXPLANATIONS.get(blocker, f"A step did not pass: {blocker}.") for blocker in blockers)
    count = len(human_blockers)
    suggested_next = _suggest_next_for_blockers(blockers)
    return WorkResultMessage(
        headline=f"{count if count else 1} check{'s' if count != 1 else ''} need attention.",
        detail="No publishing action was run. Preserve the evidence and address the blockers first.",
        blockers_human=human_blockers or ("A workflow step did not pass.",),
        suggested_next=suggested_next,
    )


def _suggest_next_for_blockers(blockers: tuple[str, ...]) -> str:
    blocker_set = set(blockers)
    if blocker_set & {"restore-known-volatile", "normalize-session", "conflict-status", "repo-status"}:
        return "Run recovery, then check again."
    if blocker_set & {"ruff", "pytest-core"}:
        return "Fix the code through the task editor, then run Check again."
    if blocker_set & {"docs-audit", "audit-doc-currency", "command-reference-check", "audit-ns-legacy-references"}:
        return "Fix the documentation or generated references, then run Check again."
    if "protected-diff-plan" in blocker_set:
        return "Inspect protected-file changes before publishing."
    if "path-selection" in blocker_set:
        return "Select changed files before finishing."
    return "Inspect the blocked steps, then re-check."


def slugify_work_title(text: str, *, prefix: str = "codex") -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", text.casefold()).strip("-")
    slug = normalized or "work-slice"
    slug = re.sub(r"-{2,}", "-", slug)[:64].strip("-") or "work-slice"
    clean_prefix = prefix.strip("/")
    return f"{clean_prefix}/{slug}" if clean_prefix else slug


def build_branch_selection_options(
    title: str,
    *,
    release_version: str = "",
) -> tuple[WorkBranchOption, ...]:
    """Build human-oriented branch choices without exposing Git jargon first."""
    patch_branch = slugify_work_title(title, prefix="codex")
    docs_branch = slugify_work_title(title, prefix="docs")
    options = [
        WorkBranchOption(
            option_id="patch",
            label="Regular change",
            branch=patch_branch,
            purpose="Use for normal code, GUI, workflow, documentation, or test changes.",
            safe_default=True,
        ),
        WorkBranchOption(
            option_id="docs",
            label="Documentation refresh",
            branch=docs_branch,
            purpose="Use for administrative handoff, planning, or documentation-only refreshes.",
        ),
    ]
    cleaned_version = release_version.strip().lstrip("v")
    if cleaned_version:
        options.append(
            WorkBranchOption(
                option_id="release",
                label="Release preparation",
                branch=f"release/prepare-v{cleaned_version}",
                purpose="Use only for an explicit release-preparation slice.",
            )
        )
    return tuple(options)


def changed_paths_from_status(status_text: str) -> tuple[ChangedPath, ...]:
    paths: list[ChangedPath] = []
    for raw_line in status_text.splitlines():
        line = raw_line.rstrip()
        if len(line) < 4:
            continue
        path = line[3:].strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1].strip()
        path = path.strip('"')
        if not path or _is_volatile_status_path(path):
            continue
        paths.append(ChangedPath(path=path))
    return tuple(paths)


def _is_volatile_status_path(path: str) -> bool:
    return any(path.startswith(prefix) for prefix in _VOLATILE_STATUS_PATH_PREFIXES)


def build_work_finish_args(
    *,
    branch: str,
    title: str,
    message: str,
    paths: tuple[ChangedPath, ...],
    execute: bool = False,
) -> tuple[str, ...]:
    args: list[str] = [
        "work",
        "finish",
        "--branch",
        branch,
        "--title",
        title,
        "--message",
        message,
    ]
    for changed_path in paths:
        if changed_path.selected:
            args.extend(["--path", changed_path.path])
    args.append("--execute" if execute else "--dry-run")
    args.append("--json")
    return tuple(args)
