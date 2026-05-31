from pathlib import Path

PLAN = Path("docs/planning/RULE_REFRESH_HANDSHAKE_PLAN.md")
WORKFLOW = Path("docs/planning/WORKFLOW_REDUCTION_FOCUS.md")
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


def test_workflow_focus_links_rule_refresh_handshake_plan() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")

    assert "RULE_REFRESH_HANDSHAKE_PLAN.md" in text
    assert "machine-checkable, fail-closed" in text


def test_documentation_registry_contains_rule_refresh_handshake_plan() -> None:
    text = REGISTRY.read_text(encoding="utf-8")

    assert "docs/planning/RULE_REFRESH_HANDSHAKE_PLAN.md" in text
    assert "local-to-LLM and LLM-to-local rule-refresh handshake" in text
