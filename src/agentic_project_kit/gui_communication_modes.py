from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CommunicationModeDefinition:
    mode_id: str
    label: str
    role: str
    is_default: bool
    safety_note: str
    explanation: str
    example: str
    next_step_hint: str
    walkthrough_steps: tuple[str, ...]
    default_expanded_groups: tuple[str, ...]


COMMUNICATION_MODE_DEFINITIONS: tuple[CommunicationModeDefinition, ...] = (
    CommunicationModeDefinition(
        mode_id="file_transfer",
        label="File Transfer",
        role="Standard",
        is_default=True,
        safety_note="Normal path: typed transfer files, work orders, reports, evidence, no chat paste required.",
        explanation=(
            "Normal mode. Write the task to the repo-backed transfer task, send g/go in chat, "
            "then read the result. Minimizes copy-and-paste."
        ),
        example=(
            "Example: Send the task, type g/go in the LLM chat, then use Read or "
            "agentic-kit transfer continue --json for the repo-backed reply."
        ),
        next_step_hint="Type your task below, click Send, then write g in chat.",
        walkthrough_steps=(
            "Start new work.",
            "Type your task and Send; it is published to the repo.",
            "Write g in chat; the assistant reads the task and works.",
            "Click Check, then Finish & publish.",
        ),
        default_expanded_groups=("task_editor",),
    ),
    CommunicationModeDefinition(
        mode_id="remote",
        label="Remote",
        role="GitHub/PR/CI",
        is_default=False,
        safety_note="Remote work is visible here but mutations remain strictly wrapper- and gatekeeper-guarded.",
        explanation=(
            "PR/CI/GitHub focused mode. Use safe read-only checks and bounded wrappers; "
            "do not bypass governance."
        ),
        example=(
            "Example: Ask the assistant to work through PR/CI, then inspect "
            "agentic-kit transfer patch-cycle-status --json and evidence links."
        ),
        next_step_hint="Open or check the pull request; CI verifies it before merge.",
        walkthrough_steps=(
            "Start new work.",
            "Make your changes.",
            "Check.",
            "Finish & publish opens a pull request; CI verifies before merge.",
        ),
        default_expanded_groups=(),
    ),
    CommunicationModeDefinition(
        mode_id="copy_paste",
        label="Copy-and-Paste",
        role="Recovery/Fallback",
        is_default=False,
        safety_note=(
            "Fallback only for terminal loss, Python startup issues, filesystem errors, "
            "network trouble before push, broken logs, or hard recovery."
        ),
        explanation=(
            "Recovery fallback only for terminal loss or missing remote access. "
            "Not the normal operating mode."
        ),
        example=(
            "Example: Open a local terminal and paste exactly one complete recovery block "
            "from the LLM, then return only LOG/RC or the requested evidence."
        ),
        next_step_hint="Run the shown command locally and paste the result back.",
        walkthrough_steps=(
            "Start new work.",
            "Copy the assistant's command.",
            "Run it locally.",
            "Paste the result back. Use only when no repo connection works.",
        ),
        default_expanded_groups=("copy_paste_tools",),
    ),
)

DEFAULT_COMMUNICATION_MODE = "file_transfer"


def communication_mode_definitions() -> tuple[CommunicationModeDefinition, ...]:
    return COMMUNICATION_MODE_DEFINITIONS


def communication_mode_ids() -> frozenset[str]:
    return frozenset(definition.mode_id for definition in COMMUNICATION_MODE_DEFINITIONS)


def communication_mode_definition(mode: str) -> CommunicationModeDefinition:
    normalized = mode if mode in communication_mode_ids() else DEFAULT_COMMUNICATION_MODE
    return next(
        definition for definition in COMMUNICATION_MODE_DEFINITIONS if definition.mode_id == normalized
    )


def communication_mode_explanation(mode: str) -> str:
    return communication_mode_definition(mode).explanation


def communication_mode_example(mode: str) -> str:
    return communication_mode_definition(mode).example


def communication_mode_next_step_hint(mode: str) -> str:
    return communication_mode_definition(mode).next_step_hint


def communication_mode_walkthrough_steps(mode: str) -> tuple[str, ...]:
    return communication_mode_definition(mode).walkthrough_steps


def communication_mode_default_expanded_groups(mode: str) -> tuple[str, ...]:
    return communication_mode_definition(mode).default_expanded_groups
