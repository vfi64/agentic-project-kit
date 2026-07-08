from pathlib import Path

CONTRACT = Path("docs/governance/RULE_REFRESH_HANDSHAKE_CONTRACT.md")
ARCHIVE = Path("docs/archive/RULE_REFRESH_HANDSHAKE_PLAN.md")
PRE_GUI = Path("docs/planning/PRE_GUI_HARDENING_TASKS.md")
REGISTRY = Path("docs/DOCUMENTATION_REGISTRY.yaml")


def test_rule_refresh_handshake_contract_records_fail_closed_core() -> None:
    text = CONTRACT.read_text(encoding="utf-8")

    assert "Fail closed when a mandatory rule source is missing." in text
    assert "Fail closed when the LLM has not acknowledged the exact snapshot identity." in text
    assert "Keep GUI behavior downstream of the machine-checked state." in text


def test_archived_rule_refresh_plan_records_transfer_state_names() -> None:
    text = ARCHIVE.read_text(encoding="utf-8")

    assert "WAITING_FOR_LLM_RULE_ACK" in text
    assert "RULES_CONFIRMED" in text


def test_archived_rule_refresh_plan_registers_phase_zero_transfer_coverage() -> None:
    text = ARCHIVE.read_text(encoding="utf-8")

    assert "Phase 0: Transfer GitHub Action Coverage" in text
    assert "create PR" in text
    assert "safe PR merge with expected head SHA" in text
    assert "unsafe-for-gui" in text


def test_pre_gui_hardening_tasks_records_planning_target_guard() -> None:
    text = PRE_GUI.read_text(encoding="utf-8")

    assert "Authoritative target for pre-GUI hardening planning" in text
    assert "WORKFLOW_REDUCTION_FOCUS.md is superseded" in text
    assert "If the resolver cannot determine a non-superseded target" in text


def test_documentation_registry_contains_rule_refresh_contract_and_archive() -> None:
    text = REGISTRY.read_text(encoding="utf-8")

    assert "docs/governance/RULE_REFRESH_HANDSHAKE_CONTRACT.md" in text
    assert "docs/archive/RULE_REFRESH_HANDSHAKE_PLAN.md" in text
    assert "local-to-LLM and LLM-to-local" in text or "rule-refresh handshake" in text
