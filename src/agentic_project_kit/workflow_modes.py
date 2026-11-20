"""Shared definitions for website paths and GUI communication modes."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


Actor = Literal["you", "assistant", "kit"]
Role = Literal["primary", "cost_saving", "emergency", "optional"]
Surface = Literal["site", "gui"]

ROLE_LABELS: dict[Role, str] = {
    "primary": "Primary",
    "cost_saving": "Cost-saving",
    "emergency": "Emergency only",
    "optional": "Optional",
}


@dataclass(frozen=True)
class WorkflowStep:
    actor_from: Actor
    actor_to: Actor
    action: str
    command: str | None = None


@dataclass(frozen=True)
class GuiPresentation:
    transport_label: str
    safety_note: str
    explanation: str
    example: str
    next_step_hint: str
    default_expanded_groups: tuple[str, ...] = ()
    is_default: bool = False


@dataclass(frozen=True)
class WorkflowMode:
    mode_id: str
    label: str
    role: Role
    surfaces: tuple[Surface, ...]
    best_for: str
    summary: str
    commands: tuple[str, ...]
    flow: tuple[WorkflowStep, ...]
    gui: GuiPresentation | None = None


# Keep the GUI order and persisted IDs. The website sorts by role.
WORKFLOW_MODES = (
    WorkflowMode(
        mode_id="file_transfer",
        label="File Transfer",
        role="cost_saving",
        surfaces=("site", "gui"),
        best_for="Browser chats without direct terminal access.",
        summary="Use a browser chat with no API or CLI usage costs for the chat workflow. Your chat subscription may still apply.",
        commands=(
            "agentic-kit transfer submit-user-task",
            "agentic-kit transfer read-user-task",
            "agentic-kit transfer remote-next",
            "agentic-kit transfer chat-switch-complete",
        ),
        flow=(
            WorkflowStep("you", "kit", "Start new work."),
            WorkflowStep("you", "kit", "Send your task so the Kit publishes it to the repository.",
                         "agentic-kit transfer submit-user-task"),
            WorkflowStep("you", "assistant", "Write g in the chat."),
            WorkflowStep("assistant", "kit", "Read the published task before working.",
                         "agentic-kit transfer read-user-task"),
            WorkflowStep("you", "kit", "Run Check, then use Finish & publish after review."),
        ),
        gui=GuiPresentation(
            transport_label="File Transfer: Transfer files",
            safety_note="Uses repository-backed tasks, work orders and evidence.",
            explanation="Normal mode. Send the task, write g/go in the chat, and read the repository-backed reply.",
            example="Example: After the assistant responds, use Read or agentic-kit transfer continue --json.",
            next_step_hint="Type your task below, click Send, then write g in chat.",
            default_expanded_groups=("task_editor",),
            is_default=True,
        ),
    ),
    WorkflowMode(
        mode_id="remote",
        label="Remote",
        role="optional",
        surfaces=("gui",),
        best_for="GitHub pull requests and CI.",
        summary="Use the GUI to inspect GitHub status and run guarded pull request closeout.",
        commands=("agentic-kit transfer patch-cycle-status",),
        flow=(
            WorkflowStep("you", "kit", "Start new work."),
            WorkflowStep("you", "you", "Make your changes."),
            WorkflowStep("you", "kit", "Run Check."),
            WorkflowStep("you", "kit", "Review the change and use Finish & publish."),
        ),
        gui=GuiPresentation(
            transport_label="Remote: GitHub/PR/CI",
            safety_note="GitHub changes use the guarded Kit workflows.",
            explanation="PR/CI/GitHub mode. Inspect status and use bounded wrappers for review and publication.",
            example="Example: Use agentic-kit transfer patch-cycle-status --json to inspect PR and CI evidence.",
            next_step_hint="Open or check the pull request. CI verifies it before merge.",
        ),
    ),
    WorkflowMode(
        mode_id="copy_paste",
        label="Copy and Paste",
        role="emergency",
        surfaces=("site", "gui"),
        best_for="Emergency path when other paths fail.",
        summary="Review an assistant's terminal block before running it locally, then send back the relevant output.",
        commands=(
            "agentic-kit workflow request",
            "agentic-kit workflow run",
            "agentic-kit transfer log-header",
            "agentic-kit transfer chat-switch-complete",
        ),
        flow=(
            WorkflowStep("assistant", "you", "Proposes a recovery block for review."),
            WorkflowStep("you", "kit", "Runs the approved block locally."),
            WorkflowStep("kit", "you", "Provides a log header for the output.",
                         "agentic-kit transfer log-header"),
            WorkflowStep("you", "assistant", "Pastes the relevant output into the chat."),
        ),
        gui=GuiPresentation(
            transport_label="Copy-and-Paste: Recovery/Fallback",
            safety_note="Use for recovery when direct execution and repository transfer are unavailable.",
            explanation="Recovery fallback only. Not the normal operating mode.",
            example="Example: Run one complete recovery block and return the relevant log and return code.",
            next_step_hint="Run the shown command locally and paste the result back.",
            default_expanded_groups=("copy_paste_tools",),
        ),
    ),
    WorkflowMode(
        mode_id="agent_direct",
        label="Agent Direct",
        role="primary",
        surfaces=("site",),
        best_for="Assistants with repository and terminal access, such as Codex CLI or Claude Code.",
        summary=(
            "The assistant runs Kit commands in the repository and you review the result. "
            "In the GUI, this path appears as Remote. Remote covers the GitHub pull request and CI steps."
        ),
        commands=(
            "agentic-kit work start",
            "agentic-kit check",
            "agentic-kit doctor",
            "agentic-kit work finish",
            "agentic-kit transfer chat-switch-complete",
        ),
        flow=(
            WorkflowStep("you", "assistant", "States the task and its limits."),
            WorkflowStep("assistant", "kit", "Starts work on a branch.", "agentic-kit work start"),
            WorkflowStep("assistant", "assistant", "Makes the change and runs the project tests."),
            WorkflowStep("assistant", "kit", "Runs the repository checks.", "agentic-kit check"),
            WorkflowStep("kit", "assistant", "Reports success or a failure that stops the flow."),
            WorkflowStep("assistant", "kit", "Checks project health.", "agentic-kit doctor"),
            WorkflowStep("assistant", "you", "Presents the change and check results for review."),
            WorkflowStep("you", "assistant", "Approves or rejects the change."),
            WorkflowStep("assistant", "kit", "After approval, asks the Kit to commit, open the PR, wait for CI and merge.",
                         "agentic-kit work finish"),
            WorkflowStep("kit", "assistant", "Reports the completed merge or blocks on failure."),
            WorkflowStep("assistant", "kit", "Requests a validated handoff.", "agentic-kit transfer chat-switch-complete"),
        ),
    ),
    WorkflowMode(
        mode_id="gui",
        label="GUI",
        role="optional",
        surfaces=("site",),
        best_for="Local access to Kit actions and readiness checks.",
        summary="Use the local window for the Kit actions available there. See the command reference for the full CLI.",
        commands=(
            "agentic-kit gui-readiness-gate",
            "agentic-kit cockpit run",
            "agentic-kit cockpit select",
        ),
        flow=(
            WorkflowStep("you", "kit", "Selects a Kit action.", "agentic-kit cockpit select"),
            WorkflowStep("kit", "you", "Reports the safety and working-tree checks.",
                         "agentic-kit cockpit run"),
        ),
    ),
)


def modes_for(surface: Surface) -> tuple[WorkflowMode, ...]:
    modes = tuple(mode for mode in WORKFLOW_MODES if surface in mode.surfaces)
    if surface == "site":
        order = tuple(ROLE_LABELS)
        return tuple(sorted(modes, key=lambda mode: order.index(mode.role)))
    return modes
