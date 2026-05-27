from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GuiButtonDefinition:
    command_id: str
    label: str
    category: str
    tooltip: str
    icon_text: str
    safety_class: str
    implementation_state: str
    enabled: bool
    disabled_reason: str = ""


def _button(
    command_id: str,
    label: str,
    category: str,
    tooltip: str,
    icon_text: str,
    *,
    safety_class: str = "read-only",
    implementation_state: str = "implemented",
    enabled: bool = True,
    disabled_reason: str = "",
) -> GuiButtonDefinition:
    return GuiButtonDefinition(
        command_id=command_id,
        label=label,
        category=category,
        tooltip=tooltip,
        icon_text=icon_text,
        safety_class=safety_class,
        implementation_state=implementation_state,
        enabled=enabled,
        disabled_reason=disabled_reason,
    )


GUI_BUTTON_CATALOG: tuple[GuiButtonDefinition, ...] = (
    _button(
        "branch-status-check",
        "Branch Status",
        "Session",
        "Show current branch, HEAD, and dirty state.",
        "branch",
    ),
    _button(
        "next-turn-status",
        "Next-Turn Status",
        "Session",
        "Inspect the fixed next-turn slot and overwrite safety.",
        "status",
    ),
    _button(
        "last-result",
        "Last Result",
        "Session",
        "Inspect structured result and evidence lookup order before asking for paste-output.",
        "history",
    ),
    _button(
        "handoff-check",
        "Handoff Check",
        "Session",
        "Validate persistent handoff state without mutation.",
        "handoff",
    ),
    _button(
        "handoff-prompt",
        "Handoff Prompt",
        "Session",
        "Render the current successor handoff prompt for review.",
        "prompt",
    ),
    _button(
        "bootstrap-show",
        "Show Bootstrap",
        "Session",
        "Display the generated successor-chat bootstrap file.",
        "bootstrap",
    ),
    _button(
        "terminal-remote-preflight",
        "Remote Preflight",
        "Evidence",
        "Check clean state before remote mutation or merge verification.",
        "shield",
    ),
    _button(
        "cockpit-readiness",
        "Cockpit Readiness",
        "Quality Gates",
        "Render static cockpit readiness metadata.",
        "cockpit",
    ),
    _button(
        "doctor", "Doctor", "Quality Gates", "Run compact project health checks.", "stethoscope"
    ),
    _button(
        "check-docs",
        "Check Docs",
        "Quality Gates",
        "Run documentation coverage and lifecycle checks.",
        "document-check",
    ),
    _button(
        "docs-audit",
        "Docs Audit",
        "Quality Gates",
        "Run the umbrella documentation-system audit.",
        "audit",
    ),
    _button(
        "governance-check",
        "Governance Check",
        "Quality Gates",
        "Run deterministic governance checks.",
        "governance",
    ),
    _button(
        "state-freshness",
        "State Freshness",
        "Quality Gates",
        "Detect stale status, handoff, or handoff-state fragments.",
        "fresh",
    ),
    _button(
        "workflow-guard-check",
        "Workflow Guard",
        "Quality Gates",
        "Diagnose recurring workflow drift before mutation.",
        "guard",
    ),
    _button(
        "patch-preflight",
        "Patch Preflight",
        "Quality Gates",
        "Run patch artifact and protected-control preflight checks.",
        "preflight",
    ),
    _button(
        "rule-registry-check",
        "Rule Registry Check",
        "Quality Gates",
        "Validate governed rule-registry artifacts.",
        "rules",
    ),
    _button(
        "rule-registry-report",
        "Rule Registry Report",
        "Quality Gates",
        "Render direct-coverage and follow-up state.",
        "report",
    ),
    _button(
        "gui-dry-run",
        "GUI Dry Run",
        "Quality Gates",
        "Render deterministic no-window GUI summary.",
        "play",
    ),
    _button(
        "actions-list",
        "Actions List",
        "Diagnostics",
        "List known action metadata and safety classes.",
        "list",
    ),
    _button(
        "evidence-inspect-log",
        "Inspect Evidence Log",
        "Evidence",
        "Requires a selected log path before execution.",
        "evidence",
        enabled=False,
        implementation_state="planned",
        disabled_reason="requires a selected terminal log path",
    ),
    _button(
        "protected-change-plan",
        "Protected Change Plan",
        "Evidence",
        "Requires an actual diff file before protected-file commits.",
        "protected",
        enabled=False,
        implementation_state="planned",
        disabled_reason="requires --diff-file for the actual git diff",
    ),
    _button(
        "pr-status",
        "PR Status",
        "Git Workflow",
        "Requires a PR number before execution.",
        "pr",
        enabled=False,
        implementation_state="planned",
        disabled_reason="requires a PR number",
    ),
    _button(
        "pr-create",
        "Create PR",
        "Git Workflow",
        "Creates or updates a pull request only after local gates.",
        "pr-create",
        safety_class="remote-mutation",
        implementation_state="planned",
        enabled=False,
        disabled_reason="remote mutation requires guarded dispatch",
    ),
    _button(
        "merge-if-green",
        "Merge If Green",
        "Git Workflow",
        "Merge is routed only through head/base-pinned green-CI gates.",
        "merge",
        safety_class="remote-mutation",
        implementation_state="planned",
        enabled=False,
        disabled_reason="merge remains gated outside the GUI",
    ),
    _button(
        "push-branch",
        "Push Branch",
        "Git Workflow",
        "Pushes a feature branch only through guarded workflow state.",
        "push",
        safety_class="remote-mutation",
        implementation_state="planned",
        enabled=False,
        disabled_reason="remote mutation requires guarded dispatch",
    ),
    _button(
        "commit-prepare",
        "Prepare Commit",
        "Git Workflow",
        "Prepare commit metadata after diff and gates pass.",
        "commit",
        safety_class="local-only",
        implementation_state="planned",
        enabled=False,
        disabled_reason="local mutation requires dispatch model",
    ),
    _button(
        "finalize-log",
        "Finalize Log",
        "Evidence",
        "Requires a run log and remote evidence path.",
        "finalize",
        safety_class="local-only",
        implementation_state="planned",
        enabled=False,
        disabled_reason="requires run-log and remote-log parameters",
    ),
    _button(
        "release-plan",
        "Release Plan",
        "Release",
        "Review release plan without publishing.",
        "release-plan",
        enabled=False,
        implementation_state="planned",
        disabled_reason="release controls are intentionally deferred",
    ),
    _button(
        "release-verify",
        "Release Verify",
        "Release",
        "Requires a release version parameter.",
        "release-verify",
        enabled=False,
        implementation_state="planned",
        disabled_reason="requires a version parameter",
    ),
    _button(
        "release-publish",
        "Release Publish",
        "Release",
        "Publishing remains disabled in the GUI.",
        "lock",
        safety_class="destructive",
        implementation_state="planned",
        enabled=False,
        disabled_reason="release publication requires maintainer-owned confirmation",
    ),
    _button(
        "work-order-show",
        "Show Work Order",
        "Workflow Automation",
        "Display the fixed next-turn Python work-order file without executing it.",
        "work-order-show",
    ),
    _button(
        "work-order-validate",
        "Validate Work Order",
        "Workflow Automation",
        "Validate the fixed next-turn Python work-order file before execution is allowed.",
        "work-order-validate",
    ),
    _button(
        "agent-next",
        "Agent Next",
        "Workflow Automation",
        "Remote command execution remains disabled until dispatch evidence is GUI-backed.",
        "agent-next",
        safety_class="remote-mutation",
        implementation_state="planned",
        enabled=False,
        disabled_reason="remote command execution disabled in GUI",
    ),
    _button(
        "agent-run",
        "Agent Run",
        "Workflow Automation",
        "Remote command execution remains disabled until dispatch evidence is GUI-backed.",
        "agent-run",
        safety_class="remote-mutation",
        implementation_state="planned",
        enabled=False,
        disabled_reason="remote command execution disabled in GUI",
    ),
)


TOOLBAR_BUTTON_IDS = (
    "branch-status-check",
    "next-turn-status",
    "last-result",
    "handoff-check",
    "doctor",
    "check-docs",
    "docs-audit",
    "workflow-guard-check",
)


def all_gui_buttons() -> tuple[GuiButtonDefinition, ...]:
    return GUI_BUTTON_CATALOG


def toolbar_gui_buttons() -> tuple[GuiButtonDefinition, ...]:
    by_id = {button.command_id: button for button in GUI_BUTTON_CATALOG}
    return tuple(by_id[button_id] for button_id in TOOLBAR_BUTTON_IDS if button_id in by_id)


def gui_buttons_by_category() -> dict[str, tuple[GuiButtonDefinition, ...]]:
    grouped: dict[str, list[GuiButtonDefinition]] = {}
    for button in GUI_BUTTON_CATALOG:
        grouped.setdefault(button.category, []).append(button)
    return {category: tuple(buttons) for category, buttons in grouped.items()}


def get_gui_button(command_id: str) -> GuiButtonDefinition | None:
    for button in GUI_BUTTON_CATALOG:
        if button.command_id == command_id:
            return button
    return None


def enabled_gui_button_ids() -> tuple[str, ...]:
    return tuple(button.command_id for button in GUI_BUTTON_CATALOG if button.enabled)


def disabled_gui_button_ids() -> tuple[str, ...]:
    return tuple(button.command_id for button in GUI_BUTTON_CATALOG if not button.enabled)
