from __future__ import annotations

from agentic_project_kit.volatile_paths import (
    KNOWN_VOLATILE_TRANSFER_PATHS,
    RULE_ACK_CURRENT_PATH,
    is_known_volatile_status_path,
    is_rule_ack_path,
)


def test_known_volatile_transfer_paths_include_rule_ack_current() -> None:
    assert RULE_ACK_CURRENT_PATH in KNOWN_VOLATILE_TRANSFER_PATHS


def test_rule_ack_path_matching_is_directory_scoped() -> None:
    assert is_rule_ack_path(".agentic/rule_ack")
    assert is_rule_ack_path(".agentic/rule_ack/")
    assert is_rule_ack_path(".agentic/rule_ack/current.json")
    assert not is_rule_ack_path(".agentic/rule_acknowledgement/current.json")


def test_known_volatile_status_path_matching_is_allowlisted() -> None:
    assert is_known_volatile_status_path(".agentic/rule_ack/current.json")
    assert is_known_volatile_status_path(".agentic/transfer/outbox/last_result.txt")
    assert is_known_volatile_status_path(
        "docs/reports/terminal/transfer_handoff_reports/latest-transfer-handoff-report.json"
    )
    assert not is_known_volatile_status_path("Config/Comm-SCI-Config.json")
