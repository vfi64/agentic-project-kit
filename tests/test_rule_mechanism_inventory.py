from pathlib import Path

import yaml

INVENTORY = Path(".agentic/rule_mechanism_inventory.yaml")
MIGRATIONS = Path(".agentic/rule_migrations.yaml")
EXPECTED_MECHANISMS = {
    "summary-renderer",
    "execution-mode-switch",
    "rule-preservation-guard",
    "workflow-guard",
    "patch-preflight",
    "chat-communication-rules",
    "chat-bootstrap-drift-rules",
    "portable-execution-rules",
    "evidence-guard",
    "typed-work-order-runner",
    "release-state-validation",
    "post-release-archive-check",
}
EXPECTED_LEGACY_IDS = {
    "structured-summary-must-be-enforced",
    "structured-summary-drift",
    "no-copy-terminal-evidence",
    "local-remote-mode-switching",
    "rules-must-be-test-backed",
    "workflow-guard-diagnostics",
    "patch-artifact-preflight-before-application",
    "chat-acknowledgements-are-not-evidence",
    "remote-log-direct-path-first",
    "successor-chat-mandatory-bootstrap",
    "portable-python-core-first",
    "false-pass-evidence-must-fail",
    "typed-work-orders-must-be-machine-readable",
    "release-state-validation-before-release",
    "post-release-doi-waiting-safety",
}


def test_inventory_is_parseable_and_complete() -> None:
    data = yaml.safe_load(INVENTORY.read_text(encoding="utf-8"))
    assert data["schema_version"] == 1
    assert {item["id"] for item in data["mechanisms"]} == EXPECTED_MECHANISMS


def test_inventory_sources_exist_and_keep_terms() -> None:
    data = yaml.safe_load(INVENTORY.read_text(encoding="utf-8"))
    for mechanism in data["mechanisms"]:
        assert mechanism["status"] == "active"
        assert mechanism["protected_rule_intent"]
        assert len(mechanism["sources"]) >= 2
        for source in mechanism["sources"]:
            path = Path(source["path"])
            assert path.exists(), source["path"]
            text = path.read_text(encoding="utf-8")
            for term in source["required_terms"]:
                assert term in text, f"{term} missing from {path}"


def test_rule_migrations_are_parseable_and_point_to_inventory() -> None:
    inventory = yaml.safe_load(INVENTORY.read_text(encoding="utf-8"))
    migrations = yaml.safe_load(MIGRATIONS.read_text(encoding="utf-8"))
    mechanism_ids = {item["id"] for item in inventory["mechanisms"]}
    legacy_ids = {item["legacy_id"] for item in migrations["migrations"]}
    assert migrations["schema_version"] == 1
    assert set(migrations["known_legacy_rule_ids"]) == EXPECTED_LEGACY_IDS
    assert legacy_ids == EXPECTED_LEGACY_IDS
    for migration in migrations["migrations"]:
        assert migration["status"] == "migrated"
        assert migration["replaced_by"] in mechanism_ids
        assert migration["migration_reason"]
        assert migration["evidence"]
        for evidence in migration["evidence"]:
            assert Path(evidence).exists(), evidence


def test_rule_registry_coverage_expands_beyond_initial_baseline() -> None:
    data = yaml.safe_load(INVENTORY.read_text(encoding="utf-8"))
    assert len(data["mechanisms"]) >= 12
    assert {
        "rule-preservation-guard",
        "workflow-guard",
        "patch-preflight",
        "chat-communication-rules",
        "chat-bootstrap-drift-rules",
        "portable-execution-rules",
        "evidence-guard",
        "typed-work-order-runner",
        "release-state-validation",
        "post-release-archive-check",
    } <= {item["id"] for item in data["mechanisms"]}
