from pathlib import Path

PLAN = Path("docs/planning/RULE_REFRESH_HANDSHAKE_PLAN.md")
PRE_GUI = Path("docs/planning/PRE_GUI_HARDENING_TASKS.md")
REGISTRY = Path("docs/DOCUMENTATION_REGISTRY.yaml")


def test_rule_refresh_handshake_plan_records_fail_closed_core() -> None:
    text = PLAN.read_text(encoding="utf-8")

    assert "Fail closed when a mandatory rule source is missing." in text
    assert "WAITING_FOR_LLM_RULE_ACK" in text
    assert "RULES_CONFIRMED" in text


def test_rule_refresh_handshake_plan_registers_phase_zero_transfer_coverage() -> None:
    text = PLAN.read_text(encoding="utf-8")

    assert "Phase 0: Transfer GitHub Action Coverage" in text
    assert "create PR" in text
    assert "safe PR merge with expected head SHA" in text
    assert "unsafe-for-gui" in text


def test_pre_gui_hardening_tasks_records_planning_target_guard() -> None:
    text = PRE_GUI.read_text(encoding="utf-8")

    assert "Authoritative target for pre-GUI hardening planning" in text
    assert "WORKFLOW_REDUCTION_FOCUS.md is superseded" in text
    assert "If the resolver cannot determine a non-superseded target" in text


def test_documentation_registry_contains_rule_refresh_handshake_plan() -> None:
    text = REGISTRY.read_text(encoding="utf-8")

    assert "docs/planning/RULE_REFRESH_HANDSHAKE_PLAN.md" in text
    assert "local-to-LLM and LLM-to-local rule-refresh handshake" in text
