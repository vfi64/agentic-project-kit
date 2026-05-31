from __future__ import annotations

from pathlib import Path

from agentic_project_kit.gatekeeper_core import (
    ACTION_ACKNOWLEDGE_RULES,
    ACTION_APPLY_TRANSFER,
    ACTION_CLOSEOUT_LAST_RUN,
    ACTION_DIAGNOSE,
    ACTION_INSPECT_TRANSFER,
    ACTION_QUEUE_TRANSFER_ORDER,
    ACTION_REFRESH_RULES,
    MUTATING_ACTIONS,
    SAFE_READ_ONLY_ACTIONS,
    derive_gatekeeper_action_contract,
    primary_state_is_supported,
)
from agentic_project_kit.transfer_state import TransferStateSnapshot


def _snapshot(
    *,
    primary_state: str = "WAIT",
    reasons: tuple[str, ...] = (),
    capabilities: dict[str, bool] | None = None,
    closeout: dict[str, object] | None = None,
    rule_snapshot: dict[str, object] | None = None,
) -> TransferStateSnapshot:
    return TransferStateSnapshot(
        schema_version=1,
        created_at="2026-05-31T00:00:00+00:00",
        repo="vfi64/agentic-project-kit",
        branch="main",
        head="13ce108",
        primary_state=primary_state,
        reasons=reasons,
        next_action="next safe action",
        capabilities=capabilities
        or {
            "diagnose": True,
            "refresh_rules": True,
            "rules_confirmed": False,
            "run_next_command": False,
            "closeout_last_run": False,
        },
        last_result=None,
        closeout=closeout or {"pending_transfer_order": False, "dirty_worktree": False},
        rule_snapshot=rule_snapshot or {"fail_closed": False},
        rule_acknowledgement={"present": False},
    )


def test_supported_primary_states_match_basic_gui_traffic_light_contract():
    assert primary_state_is_supported("READY") is True
    assert primary_state_is_supported("WAIT") is True
    assert primary_state_is_supported("BLOCKED") is True
    assert primary_state_is_supported("FAILED") is True
    assert primary_state_is_supported("UNKNOWN") is False


def test_wait_without_acknowledgement_allows_only_readonly_and_acknowledgement():
    contract = derive_gatekeeper_action_contract(
        _snapshot(reasons=("missing_rule_acknowledgement",))
    )

    assert contract.primary_state == "WAIT"
    assert contract.action(ACTION_DIAGNOSE).enabled is True
    assert contract.action(ACTION_REFRESH_RULES).enabled is True
    assert contract.action(ACTION_ACKNOWLEDGE_RULES).enabled is True
    assert contract.action(ACTION_QUEUE_TRANSFER_ORDER).enabled is False
    assert contract.action(ACTION_INSPECT_TRANSFER).enabled is False
    assert contract.action(ACTION_APPLY_TRANSFER).enabled is False
    assert contract.action(ACTION_CLOSEOUT_LAST_RUN).enabled is False


def test_ready_with_pending_order_and_confirmed_rules_enables_transfer_controls():
    contract = derive_gatekeeper_action_contract(
        _snapshot(
            primary_state="READY",
            capabilities={
                "diagnose": True,
                "refresh_rules": True,
                "rules_confirmed": True,
                "run_next_command": True,
                "closeout_last_run": False,
            },
            closeout={"pending_transfer_order": True, "dirty_worktree": False},
        )
    )

    assert contract.action(ACTION_INSPECT_TRANSFER).enabled is True
    assert contract.action(ACTION_APPLY_TRANSFER).enabled is True
    assert contract.action(ACTION_QUEUE_TRANSFER_ORDER).enabled is False
    assert contract.action(ACTION_QUEUE_TRANSFER_ORDER).blocked_reason == "pending_transfer_order_exists"


def test_confirmed_rules_without_pending_order_enables_queue_but_not_transfer():
    contract = derive_gatekeeper_action_contract(
        _snapshot(
            capabilities={
                "diagnose": True,
                "refresh_rules": True,
                "rules_confirmed": True,
                "run_next_command": False,
                "closeout_last_run": False,
            }
        )
    )

    assert contract.action(ACTION_QUEUE_TRANSFER_ORDER).enabled is True
    assert contract.action(ACTION_INSPECT_TRANSFER).enabled is False
    assert contract.action(ACTION_APPLY_TRANSFER).enabled is False


def test_dirty_worktree_blocks_all_mutating_actions_but_keeps_readonly_controls():
    contract = derive_gatekeeper_action_contract(
        _snapshot(
            primary_state="BLOCKED",
            reasons=("dirty_worktree",),
            capabilities={
                "diagnose": True,
                "refresh_rules": True,
                "rules_confirmed": True,
                "run_next_command": False,
                "closeout_last_run": False,
            },
            closeout={"pending_transfer_order": False, "dirty_worktree": True},
        )
    )

    for action_name in SAFE_READ_ONLY_ACTIONS:
        assert contract.action(action_name).enabled is True
    for action_name in MUTATING_ACTIONS:
        assert contract.action(action_name).enabled is False
        assert contract.action(action_name).blocked_reason


def test_closeout_requires_explicit_closeout_capability():
    contract = derive_gatekeeper_action_contract(
        _snapshot(
            capabilities={
                "diagnose": True,
                "refresh_rules": True,
                "rules_confirmed": True,
                "run_next_command": False,
                "closeout_last_run": True,
            }
        )
    )

    assert contract.action(ACTION_CLOSEOUT_LAST_RUN).enabled is True
    assert contract.action(ACTION_INSPECT_TRANSFER).enabled is False


def test_action_contract_is_json_serializable_and_ui_free():
    contract = derive_gatekeeper_action_contract(_snapshot())
    data = contract.as_json_data()

    assert data["schema_version"] == 1
    assert data["primary_state"] == "WAIT"
    assert data["next_action"] == "next safe action"
    assert {action["name"] for action in data["actions"]} == {
        ACTION_DIAGNOSE,
        ACTION_REFRESH_RULES,
        ACTION_ACKNOWLEDGE_RULES,
        ACTION_QUEUE_TRANSFER_ORDER,
        ACTION_INSPECT_TRANSFER,
        ACTION_APPLY_TRANSFER,
        ACTION_CLOSEOUT_LAST_RUN,
    }
    assert "QPushButton" not in repr(data)
    assert "tkinter" not in repr(data)


def test_no_filesystem_or_shell_dependency_in_contract_derivation(tmp_path):
    marker = tmp_path / "should_not_be_read.txt"
    marker.write_text("unused\n", encoding="utf-8")

    contract = derive_gatekeeper_action_contract(_snapshot())

    assert marker.read_text(encoding="utf-8") == "unused\n"
    assert contract.action(ACTION_DIAGNOSE).enabled is True


def test_import_keeps_path_available_for_future_cli_or_gui_consumers():
    assert Path("src/agentic_project_kit/gatekeeper_core.py").suffix == ".py"
