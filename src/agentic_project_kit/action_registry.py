"""Static action metadata for local workflow and cockpit readiness.

This module is intentionally read-only: it describes known local actions but
does not execute shell commands, mutate git state, call GitHub, or publish releases.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class SafetyClass(str, Enum):
    """Coarse safety class for a local action."""

    READ_ONLY = "read-only"
    LOCAL_ONLY = "local-only"
    REMOTE_MUTATION = "remote-mutation"
    RELEASE_TAG_PUBLISH = "release-tag-publish"
    MERGE_DELETE_CLOSE = "merge-delete-close"


@dataclass(frozen=True)
class ActionMetadata:
    """Static metadata for one repo-local action."""

    name: str
    safety_class: SafetyClass
    mutation_scope: str
    dry_run_supported: bool
    outcome_contract: tuple[str, ...]
    summary: str


ACTIONS: tuple[ActionMetadata, ...] = (
    ActionMetadata(
        name="dev",
        safety_class=SafetyClass.READ_ONLY,
        mutation_scope="none",
        dry_run_supported=True,
        outcome_contract=("PASS", "FAIL"),
        summary="Run local deterministic development gates.",
    ),
    ActionMetadata(
        name="pr-cleanup",
        safety_class=SafetyClass.READ_ONLY,
        mutation_scope="none",
        dry_run_supported=True,
        outcome_contract=("PASS", "FAIL"),
        summary="Classify open pull requests without mutating them.",
    ),
    ActionMetadata(
        name="release-verify",
        safety_class=SafetyClass.READ_ONLY,
        mutation_scope="none",
        dry_run_supported=True,
        outcome_contract=("PASS", "FAIL"),
        summary="Verify an existing release and metadata state.",
    ),
    ActionMetadata(
        name="clean-evidence",
        safety_class=SafetyClass.LOCAL_ONLY,
        mutation_scope="working-tree-files",
        dry_run_supported=False,
        outcome_contract=("PASS", "FAIL"),
        summary="Clean local evidence or generated files according to repo policy.",
    ),
    ActionMetadata(
        name="release-prep",
        safety_class=SafetyClass.LOCAL_ONLY,
        mutation_scope="version-and-release-metadata-files",
        dry_run_supported=False,
        outcome_contract=("PASS", "FAIL"),
        summary="Prepare local release metadata before a release PR.",
    ),
    ActionMetadata(
        name="release-gate",
        safety_class=SafetyClass.READ_ONLY,
        mutation_scope="none",
        dry_run_supported=True,
        outcome_contract=("PASS", "FAIL"),
        summary="Verify release readiness without tagging or publishing.",
    ),
    ActionMetadata(
        name="finalize-guard",
        safety_class=SafetyClass.READ_ONLY,
        mutation_scope="none",
        dry_run_supported=True,
        outcome_contract=("PASS_ALREADY_ON_MAIN", "PASS_NOOP_BRANCH", "PASS_SUPERSEDED", "PASS_NEEDS_PR", "FAIL_CONFLICT_RELEVANT", "FAIL_NEEDS_HUMAN_REVIEW"),
        summary="Classify branch finalization state without merging or deleting.",
    ),
    ActionMetadata(
        name="cockpit-readiness",
        safety_class=SafetyClass.READ_ONLY,
        mutation_scope="none",
        dry_run_supported=True,
        outcome_contract=("PASS", "FAIL"),
        summary="Render static cockpit readiness metadata without executing actions.",
    ),

    ActionMetadata(
        name="agent-next",
        safety_class=SafetyClass.REMOTE_MUTATION,
        mutation_scope="docs/reports/command_runs and docs/reports/terminal",
        dry_run_supported=False,
        outcome_contract=(
            "PASS_EXECUTED",
            "FAIL_NO_COMMAND",
            "FAIL_AMBIGUOUS_COMMANDS",
            "FAIL_PULL",
            "FAIL_ALREADY_EXECUTED",
            "FAIL_INVALID_COMMAND",
            "FAIL_SHELL_SYNTAX",
            "FAIL_COMMAND",
            "FAIL_UPLOAD",
            "FAIL_POSTCONDITION",
        ),
        summary="Pull and execute exactly one pending repo-backed agent command.",
    ),

    ActionMetadata(
        name="agent-run",
        safety_class=SafetyClass.REMOTE_MUTATION,
        mutation_scope="docs/reports/command_runs and docs/reports/terminal",
        dry_run_supported=False,
        outcome_contract=("PASS_EXECUTED", "FAIL_NO_COMMAND", "FAIL_ALREADY_EXECUTED", "FAIL_INVALID_COMMAND", "FAIL_SHELL_SYNTAX", "FAIL_COMMAND", "FAIL_UPLOAD"),
        summary="Pull-safe repo command runner for agent handoff without copy-and-paste terminal blocks.",
    ),
    ActionMetadata(
        name="run-logged",
        safety_class=SafetyClass.LOCAL_ONLY,
        mutation_scope="docs/reports/terminal",
        dry_run_supported=False,
        outcome_contract=("PASS", "FAIL", "FAIL_NO_COMMAND", "FAIL_MISSING_SEPARATOR"),
        summary="Run a local command while teeing output to a terminal log.",
    ),
    ActionMetadata(
        name="terminal-status",
        safety_class=SafetyClass.READ_ONLY,
        mutation_scope="none",
        dry_run_supported=True,
        outcome_contract=("PASS_LOG_READY", "PASS_NO_LOG", "FAIL_INVALID_POINTER"),
        summary="Inspect the latest terminal log pointer without mutating state.",
    ),
    ActionMetadata(
        name="terminal-clean-check",
        safety_class=SafetyClass.READ_ONLY,
        mutation_scope="none",
        dry_run_supported=True,
        outcome_contract=("PASS_CLEAN", "PASS_ONLY_TERMINAL_LOG_DIRTY", "FAIL_DIRTY_NON_LOG_FILES"),
        summary="Check whether only terminal-log artifacts are dirty during logged runs.",
    ),
    ActionMetadata(
        name="terminal-upload",
        safety_class=SafetyClass.REMOTE_MUTATION,
        mutation_scope="docs/reports/terminal only",
        dry_run_supported=False,
        outcome_contract=("PASS_UPLOADED", "PASS_ALREADY_UPLOADED", "FAIL_NO_LOG", "FAIL_DIRTY_NON_LOG_FILES", "FAIL_PUSH_FAILED"),
        summary="Commit and push only terminal-log artifacts for failure handoff.",
    ),

)


def list_actions() -> tuple[ActionMetadata, ...]:
    """Return all known action metadata entries."""

    return ACTIONS


def get_action(name: str) -> ActionMetadata | None:
    """Return metadata for one action name, if known."""

    for action in ACTIONS:
        if action.name == name:
            return action
    return None
