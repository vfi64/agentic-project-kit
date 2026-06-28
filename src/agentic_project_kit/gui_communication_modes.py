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
