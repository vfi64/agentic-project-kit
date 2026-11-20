from __future__ import annotations

from dataclasses import dataclass

from .workflow_modes import ROLE_LABELS, modes_for


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


COMMUNICATION_MODE_DEFINITIONS = tuple(
    CommunicationModeDefinition(
        mode_id=mode.mode_id,
        label=mode.label,
        role=ROLE_LABELS[mode.role],
        is_default=mode.gui.is_default,
        safety_note=mode.gui.safety_note,
        explanation=mode.gui.explanation,
        example=mode.gui.example,
        next_step_hint=mode.gui.next_step_hint,
        walkthrough_steps=tuple(step.action for step in mode.flow),
        default_expanded_groups=mode.gui.default_expanded_groups,
    )
    for mode in modes_for("gui") if mode.gui is not None
)

DEFAULT_COMMUNICATION_MODE = next(
    mode.mode_id for mode in COMMUNICATION_MODE_DEFINITIONS if mode.is_default
)


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
