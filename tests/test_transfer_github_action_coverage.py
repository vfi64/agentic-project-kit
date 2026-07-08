from pathlib import Path

DIRECTION = Path("docs/planning/PROJECT_DIRECTION.yaml")
RULE_PLAN = Path("docs/archive/RULE_REFRESH_HANDSHAKE_PLAN.md")
REGISTRY = Path("docs/DOCUMENTATION_REGISTRY.yaml")

CRITICAL_TRANSFER_ACTIONS = (
    "repo-status",
    "remote-work-start",
    "push-current",
    "pr-create-complete",
    "pr-complete",
    "post-merge-complete",
    "post-merge-check",
)


def test_transfer_github_action_coverage_is_centralized_in_project_direction() -> None:
    text = DIRECTION.read_text(encoding="utf-8")

    assert "workflow-kernel-and-transfer-hardening" in text
    assert "TRANSFER_GITHUB_ACTION_COVERAGE.md" in text
    assert "status: removed_source" in text
    assert "covered_or_governed_action_families:" in text


def test_transfer_github_action_coverage_records_critical_actions() -> None:
    text = DIRECTION.read_text(encoding="utf-8")

    for action in CRITICAL_TRANSFER_ACTIONS:
        assert action in text


def test_transfer_github_action_coverage_classifies_gui_risk() -> None:
    text = DIRECTION.read_text(encoding="utf-8")

    assert "covered_by_transfer_wrappers" in text
    assert "covered_or_wrapper_required_before_mutation" in text
    assert "not_raw_github_action_authority" in text
    assert "connector or GUI bypass" in text
    assert "future_rule:" in text


def test_rule_refresh_plan_points_to_centralized_phase_zero_artifact() -> None:
    text = RULE_PLAN.read_text(encoding="utf-8")

    assert "docs/planning/PROJECT_DIRECTION.yaml" in text
    assert "workflow-kernel-and-transfer-hardening" in text
    assert "transfer GitHub action coverage" in text


def test_documentation_registry_no_longer_registers_removed_transfer_coverage_doc() -> None:
    text = REGISTRY.read_text(encoding="utf-8")

    removed_path = "docs/planning/" + "TRANSFER_GITHUB_ACTION_COVERAGE.md"
    assert f"- path: {removed_path}" not in text
    assert "Phase 0 coverage matrix for transfer GitHub actions" not in text
