from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from agentic_project_kit.transfer_state import (
    PRIMARY_BLOCKED,
    PRIMARY_FAILED,
    PRIMARY_READY,
    PRIMARY_WAIT,
    TransferStateSnapshot,
)

ACTION_DIAGNOSE = "diagnose"
ACTION_REFRESH_RULES = "refresh_rules"
ACTION_ACKNOWLEDGE_RULES = "acknowledge_rules"
ACTION_INSPECT_TRANSFER = "inspect_transfer"
ACTION_APPLY_TRANSFER = "apply_transfer"
ACTION_CLOSEOUT_LAST_RUN = "closeout_last_run"
ACTION_QUEUE_TRANSFER_ORDER = "queue_transfer_order"

SAFE_READ_ONLY_ACTIONS = frozenset({ACTION_DIAGNOSE, ACTION_REFRESH_RULES})
MUTATING_ACTIONS = frozenset(
    {
        ACTION_ACKNOWLEDGE_RULES,
        ACTION_INSPECT_TRANSFER,
        ACTION_APPLY_TRANSFER,
        ACTION_CLOSEOUT_LAST_RUN,
        ACTION_QUEUE_TRANSFER_ORDER,
    }
)


@dataclass(frozen=True)
class GatekeeperAction:
    """Machine-readable action decision for a future GUI control."""

    name: str
    label: str
    enabled: bool
    category: str
    required_capability: str | None = None
    blocked_reason: str = ""
    next_action: str = ""

    def as_json_data(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "label": self.label,
            "enabled": self.enabled,
            "category": self.category,
            "required_capability": self.required_capability,
            "blocked_reason": self.blocked_reason,
            "next_action": self.next_action,
        }


@dataclass(frozen=True)
class GatekeeperActionContract:
    """State/action contract consumed by CLI, tests, and later GUI code."""

    schema_version: int
    primary_state: str
    next_action: str
    reasons: tuple[str, ...]
    actions: tuple[GatekeeperAction, ...]

    def action(self, name: str) -> GatekeeperAction:
        for candidate in self.actions:
            if candidate.name == name:
                return candidate
        raise KeyError(name)

    def as_json_data(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "primary_state": self.primary_state,
            "next_action": self.next_action,
            "reasons": list(self.reasons),
            "actions": [action.as_json_data() for action in self.actions],
        }


def _blocked_reason(snapshot: TransferStateSnapshot, capability: str) -> str:
    if snapshot.capabilities.get(capability, False):
        return ""
    if snapshot.reasons:
        return ",".join(snapshot.reasons)
    if capability == "rules_confirmed":
        return "rules_not_confirmed"
    if capability == "run_next_command":
        return "transfer_not_ready"
    if capability == "closeout_last_run":
        return "closeout_not_ready"
    return "capability_disabled"


def _capability_action(
    snapshot: TransferStateSnapshot,
    *,
    name: str,
    label: str,
    category: str,
    capability: str,
) -> GatekeeperAction:
    enabled = snapshot.capabilities.get(capability, False)
    return GatekeeperAction(
        name=name,
        label=label,
        enabled=enabled,
        category=category,
        required_capability=capability,
        blocked_reason=_blocked_reason(snapshot, capability),
        next_action=snapshot.next_action,
    )


def _acknowledge_rules_action(snapshot: TransferStateSnapshot) -> GatekeeperAction:
    rule_snapshot = snapshot.rule_snapshot
    fail_closed = bool(rule_snapshot.get("fail_closed", False)) if isinstance(rule_snapshot, dict) else False
    rules_confirmed = snapshot.capabilities.get("rules_confirmed", False)
    enabled = not fail_closed and not rules_confirmed and snapshot.primary_state != PRIMARY_FAILED
    if enabled:
        blocked_reason = ""
    elif fail_closed:
        blocked_reason = "rule_snapshot_fail_closed"
    elif rules_confirmed:
        blocked_reason = "rules_already_confirmed"
    else:
        blocked_reason = _blocked_reason(snapshot, "rules_confirmed")
    return GatekeeperAction(
        name=ACTION_ACKNOWLEDGE_RULES,
        label="Acknowledge current rule snapshot",
        enabled=enabled,
        category="mutating",
        required_capability="rules_confirmed",
        blocked_reason=blocked_reason,
        next_action=snapshot.next_action,
    )


def _queue_transfer_order_action(snapshot: TransferStateSnapshot) -> GatekeeperAction:
    pending_order = bool(snapshot.closeout.get("pending_transfer_order", False))
    dirty = bool(snapshot.closeout.get("dirty_worktree", False))
    rules_confirmed = snapshot.capabilities.get("rules_confirmed", False)
    enabled = rules_confirmed and not dirty and not pending_order
    if enabled:
        blocked_reason = ""
    elif dirty:
        blocked_reason = "dirty_worktree"
    elif pending_order:
        blocked_reason = "pending_transfer_order_exists"
    elif not rules_confirmed:
        blocked_reason = _blocked_reason(snapshot, "rules_confirmed")
    else:
        blocked_reason = "queue_not_ready"
    return GatekeeperAction(
        name=ACTION_QUEUE_TRANSFER_ORDER,
        label="Queue transfer order",
        enabled=enabled,
        category="mutating",
        required_capability="rules_confirmed",
        blocked_reason=blocked_reason,
        next_action=snapshot.next_action,
    )


def derive_gatekeeper_action_contract(
    snapshot: TransferStateSnapshot,
) -> GatekeeperActionContract:
    """Derive the deterministic B11 state/action contract from a transfer snapshot.

    The contract is deliberately UI-free. A later GUI may render these actions as buttons,
    but must not invent additional enable/disable rules outside this core contract.
    """

    actions = (
        _capability_action(
            snapshot,
            name=ACTION_DIAGNOSE,
            label="Diagnose state",
            category="read_only",
            capability="diagnose",
        ),
        _capability_action(
            snapshot,
            name=ACTION_REFRESH_RULES,
            label="Refresh rule snapshot",
            category="read_only",
            capability="refresh_rules",
        ),
        _acknowledge_rules_action(snapshot),
        _queue_transfer_order_action(snapshot),
        _capability_action(
            snapshot,
            name=ACTION_INSPECT_TRANSFER,
            label="Inspect transfer order",
            category="mutating",
            capability="run_next_command",
        ),
        _capability_action(
            snapshot,
            name=ACTION_APPLY_TRANSFER,
            label="Apply inspected transfer order",
            category="mutating",
            capability="run_next_command",
        ),
        _capability_action(
            snapshot,
            name=ACTION_CLOSEOUT_LAST_RUN,
            label="Close out last run",
            category="mutating",
            capability="closeout_last_run",
        ),
    )
    return GatekeeperActionContract(
        schema_version=1,
        primary_state=snapshot.primary_state,
        next_action=snapshot.next_action,
        reasons=snapshot.reasons,
        actions=actions,
    )


def derive_gatekeeper_action_contract_json_data(
    snapshot: TransferStateSnapshot,
) -> dict[str, Any]:
    return derive_gatekeeper_action_contract(snapshot).as_json_data()


def primary_state_is_supported(primary_state: str) -> bool:
    return primary_state in {PRIMARY_READY, PRIMARY_WAIT, PRIMARY_BLOCKED, PRIMARY_FAILED}
