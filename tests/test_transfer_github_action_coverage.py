from pathlib import Path

COVERAGE = Path("docs/planning/TRANSFER_GITHUB_ACTION_COVERAGE.md")
REGISTRY = Path("docs/DOCUMENTATION_REGISTRY.yaml")
RULE_PLAN = Path("docs/planning/RULE_REFRESH_HANDSHAKE_PLAN.md")


CRITICAL_TRANSFER_ACTIONS = [
    "repo-status",
    "repo-log",
    "head-sha",
    "repo-diff",
    "fetch-origin",
    "pull-current",
    "branch-create",
    "branch-switch",
    "commit",
    "push-current",
    "pr-create",
    "pr-status",
    "pr-wait-ci",
    "pr-merge-safe",
    "post-merge-check",
    "admin-refresh-pr",
    "remote-next",
    "run-local",
    "state",
    "status",
    "inspect",
    "apply",
    "closeout",
]


def test_transfer_github_action_coverage_records_critical_actions() -> None:
    text = COVERAGE.read_text(encoding="utf-8")

    for action in CRITICAL_TRANSFER_ACTIONS:
        assert f"`transfer {action}`" in text


def test_transfer_github_action_coverage_classifies_gui_risk() -> None:
    text = COVERAGE.read_text(encoding="utf-8")

    assert "`covered`" in text
    assert "`partial`" in text
    assert "`missing`" in text
    assert "`unsafe-for-gui`" in text
    assert "`transfer apply` | unsafe-for-gui" in text


def test_rule_refresh_plan_points_to_phase_zero_artifact() -> None:
    text = RULE_PLAN.read_text(encoding="utf-8")

    assert "TRANSFER_GITHUB_ACTION_COVERAGE.md" in text
    assert "Phase 0 artifact" in text


def test_documentation_registry_contains_transfer_github_action_coverage() -> None:
    text = REGISTRY.read_text(encoding="utf-8")

    assert "docs/planning/TRANSFER_GITHUB_ACTION_COVERAGE.md" in text
    assert "Phase 0 coverage matrix for transfer GitHub actions" in text
