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
    wrapper_command: tuple[str, ...] = ()
    gui_gate: str = "read_only_gate"
    requires_parameters: bool = False
    structured_explanation: str | None = None


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
    wrapper_command: tuple[str, ...] = (),
    gui_gate: str = "read_only_gate",
    requires_parameters: bool = False,
    structured_explanation: str | None = None,
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
        wrapper_command=wrapper_command,
        gui_gate=gui_gate,
        requires_parameters=requires_parameters,
        structured_explanation=structured_explanation,
    )


GUI_BUTTON_CATALOG: tuple[GuiButtonDefinition, ...] = (
    _button(
        "status-refresh",
        "Status",
        "Basic",
        "Refresh the deterministic cockpit and gatekeeper status.",
        "status",
        wrapper_command=("agentic-kit", "cockpit", "gatekeeper-status"),
        structured_explanation=(
            "PURPOSE: Refresh deterministic cockpit and gatekeeper state.\n"
            "EFFECT: Reads state only; does not mutate repo files.\n"
            "WHEN: Use before choosing the next GUI action.\n"
            "BLOCKED WHEN: The cockpit command itself cannot run.\n"
            "AFTER PASS: Continue with the enabled safe action.\n"
            "AFTER FAIL: Open diagnostics and preserve evidence."
        ),
    ),
    _button(
        "restore-volatile",
        "Restore Volatile",
        "Basic",
        "Restore only known volatile transfer artifacts; never reset product files.",
        "restore",
        safety_class="bounded-mutation",
        wrapper_command=("agentic-kit", "transfer", "restore-known-volatile", "--json"),
        gui_gate="known_volatile_restore_gate",
        structured_explanation=(
            "PURPOSE: Restore the canonical known volatile transfer files.\n"
            "EFFECT: Runs only agentic-kit transfer restore-known-volatile --json.\n"
            "WHEN: Use when the worktree is blocked by generated transfer or handoff artifacts.\n"
            "BLOCKED WHEN: A workflow is failed, d2 is pending, or real product changes remain.\n"
            "AFTER PASS: Refresh status; if dirty paths remain, review them manually.\n"
            "AFTER FAIL: Inspect restore-known-volatile output before retrying."
        ),
    ),
    _button(
        "communication-rules-refresh",
        "Refresh Rules",
        "Basic",
        "Publish the communication rule capsule and require d2 acknowledgement before mutation.",
        "rules",
        safety_class="bounded-mutation",
        enabled=False,
        disabled_reason="requires guarded d2 rule-capsule dispatcher before Basic Mode execution",
        wrapper_command=("agentic-kit", "rules", "communication-refresh", "--publish", "--json"),
        gui_gate="local_mutation_gate",
        structured_explanation=(
            "PURPOSE: Publish the current communication rule capsule.\n"
            "EFFECT: Writes the generated communication-rules report and a local d2 pending state.\n"
            "WHEN: Use when chat communication rules must be refreshed before more mutation.\n"
            "BLOCKED WHEN: Worktree or gatekeeper state is not safe for bounded local mutation.\n"
            "AFTER PASS: Send d2; the assistant must read the remote capsule and ACK it.\n"
            "AFTER FAIL: Diagnose the rule-refresh gate before retrying."
        ),
    ),
    _button(
        "run-next-work-order",
        "Run Work Order",
        "Basic",
        "Run the validated file-transfer work order through the existing work-order wrapper.",
        "work-order",
        safety_class="local-only",
        enabled=False,
        disabled_reason="requires validated work order and clean READY gatekeeper state",
        wrapper_command=("agentic-kit", "work-order", "run"),
        gui_gate="local_mutation_gate",
        structured_explanation=(
            "PURPOSE: Run the next validated file-transfer work order.\n"
            "EFFECT: Runs only through the registered work-order wrapper.\n"
            "WHEN: Use after a valid work order is present and the gatekeeper is READY.\n"
            "BLOCKED WHEN: d2 is pending, the worktree is dirty, or no guarded dispatcher exists.\n"
            "AFTER PASS: Read the generated result/evidence.\n"
            "AFTER FAIL: Preserve output and inspect diagnostics."
        ),
    ),
    _button(
        "close-out-last-run",
        "Close Out Run",
        "Basic",
        "Close out the last run through the fixed-path work-order upload wrapper.",
        "closeout",
        safety_class="bounded-mutation",
        enabled=False,
        disabled_reason="requires fixed-path evidence and clean READY gatekeeper state",
        wrapper_command=("agentic-kit", "work-order", "upload"),
        gui_gate="fixed_path_upload_gate",
        structured_explanation=(
            "PURPOSE: Close out the last run through the fixed-path upload wrapper.\n"
            "EFFECT: Publishes expected evidence paths through a bounded closeout path.\n"
            "WHEN: Use only after the previous run produced valid fixed-path evidence.\n"
            "BLOCKED WHEN: Evidence is missing, dirty, or not gatekeeper-approved.\n"
            "AFTER PASS: Continue with handoff or next work order.\n"
            "AFTER FAIL: Inspect closeout evidence before retrying."
        ),
    ),
    _button(
        "diagnose",
        "Diagnose",
        "Basic",
        "Run compact read-only diagnostics through the project doctor.",
        "diagnose",
        wrapper_command=("agentic-kit", "doctor"),
        structured_explanation=(
            "PURPOSE: Run compact project health diagnostics.\n"
            "EFFECT: Reads repo health and reports findings.\n"
            "WHEN: Use after a FAIL/BLOCK or before risky work.\n"
            "BLOCKED WHEN: The doctor command cannot run.\n"
            "AFTER PASS: Continue with the next safe action.\n"
            "AFTER FAIL: Fix or diagnose the reported blockers."
        ),
    ),
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
        "successor-handoff-prompt",
        "Successor Handoff Package",
        "Session",
        "Render the successor chat prompt through chat-switch-complete --render-prompt.",
        "handoff-prompt",
        safety_class="bounded-mutation",
        implementation_state="planned",
        enabled=False,
        disabled_reason="requires guarded GUI dispatch for transfer output mutation",
        wrapper_command=("agentic-kit", "transfer", "chat-switch-complete"),
        gui_gate="transfer_output_mutation_gate",
        requires_parameters=True,
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
        "instruction-lint-clipboard",
        "Lint Clipboard",
        "Quality Gates",
        "Lint the current clipboard through agentic-kit instruction lint --stdin without executing it.",
        "lint",
        wrapper_command=("agentic-kit", "instruction", "lint", "--stdin"),
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
        wrapper_command=("agentic-kit", "transfer", "protected-diff-plan"),
        gui_gate="parameterized_read_only_gate",
        requires_parameters=True,
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
        wrapper_command=("agentic-kit", "transfer", "pr-status"),
        gui_gate="parameterized_read_only_gate",
        requires_parameters=True,
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
        wrapper_command=("agentic-kit", "transfer", "pr-create-complete"),
        gui_gate="remote_mutation_gate",
        requires_parameters=True,
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
        wrapper_command=("agentic-kit", "transfer", "pr-complete"),
        gui_gate="remote_mutation_gate",
        requires_parameters=True,
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
        wrapper_command=("agentic-kit", "transfer", "push-current"),
        gui_gate="remote_mutation_gate",
        requires_parameters=True,
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
        wrapper_command=("agentic-kit", "transfer", "commit"),
        gui_gate="local_mutation_gate",
        requires_parameters=True,
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
        wrapper_command=("agentic-kit", "transfer", "evidence-finalize-current-transfer"),
        gui_gate="evidence_mutation_gate",
        requires_parameters=True,
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
        "work-order-run",
        "Run Validated Work Order",
        "Workflow Automation",
        "Run the fixed next-turn Python work-order only after validation passes; writes the local result log without dirtying repo evidence paths.",
        "work-order-run",
    ),
    _button(
        "work-order-upload",
        "Upload Result Log",
        "Workflow Automation",
        "Promote the local next-turn result log, then commit and push only docs/reports/terminal/next-turn-latest.log.",
        "work-order-upload",
        safety_class="bounded-mutation",
        wrapper_command=("agentic-kit", "work-order", "upload"),
        gui_gate="fixed_path_upload_gate",
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

BASIC_BUTTON_IDS = (
    "status-refresh",
    "restore-volatile",
    "communication-rules-refresh",
    "run-next-work-order",
    "close-out-last-run",
    "diagnose",
)


def all_gui_buttons() -> tuple[GuiButtonDefinition, ...]:
    return GUI_BUTTON_CATALOG


def toolbar_gui_buttons() -> tuple[GuiButtonDefinition, ...]:
    by_id = {button.command_id: button for button in GUI_BUTTON_CATALOG}
    return tuple(by_id[button_id] for button_id in TOOLBAR_BUTTON_IDS if button_id in by_id)


def basic_gui_buttons() -> tuple[GuiButtonDefinition, ...]:
    by_id = {button.command_id: button for button in GUI_BUTTON_CATALOG}
    return tuple(by_id[button_id] for button_id in BASIC_BUTTON_IDS if button_id in by_id)


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
