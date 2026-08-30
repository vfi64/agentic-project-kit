from __future__ import annotations

from agentic_project_kit.volatile_paths import (
    KNOWN_VOLATILE_TRANSFER_PATHS,
    RULE_ACK_CURRENT_PATH,
    split_known_volatile_status,
    status_path_from_short_line,
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
    assert is_known_volatile_status_path(".agentic/transfer/inbox/next_command.py.txt")
    assert is_known_volatile_status_path(
        "docs/reports/terminal/transfer_handoff_reports/latest-transfer-handoff-report.json"
    )
    assert is_known_volatile_status_path(
        ".agentic/state/handoff/transfer_handoff_reports/latest-transfer-handoff-report.json"
    )
    assert is_known_volatile_status_path("tmp/local-gc-last.json")
    assert is_known_volatile_status_path(".agentic/tmp/local-gc-last.json")
    assert is_known_volatile_status_path("tmp/local-command-stack-state.json")
    assert is_known_volatile_status_path(".agentic/tmp/workspace.lock")
    assert not is_known_volatile_status_path("Config/Comm-SCI-Config.json")


def test_status_path_from_short_line_handles_renames() -> None:
    assert status_path_from_short_line("?? .agentic/rule_ack/current.json") == ".agentic/rule_ack/current.json"
    assert status_path_from_short_line("R  old.py -> src/new.py") == "src/new.py"


def test_split_known_volatile_status_keeps_product_changes() -> None:
    status = "\n".join(
        [
            "?? .agentic/rule_ack/current.json",
            "?? .agentic/transfer/outbox/last_result.txt",
            "?? .agentic/state/handoff/transfer_handoff_reports/latest-transfer-handoff-report.json",
            "?? tmp/local-gc-last.json",
            " M Config/Comm-SCI-Config.json",
        ]
    )

    kept, ignored = split_known_volatile_status(status)

    assert kept == " M Config/Comm-SCI-Config.json"
    assert ignored == [
        "?? .agentic/rule_ack/current.json",
        "?? .agentic/transfer/outbox/last_result.txt",
        "?? .agentic/state/handoff/transfer_handoff_reports/latest-transfer-handoff-report.json",
        "?? tmp/local-gc-last.json",
    ]
