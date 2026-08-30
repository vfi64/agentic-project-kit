from __future__ import annotations

RULE_ACK_DIRECTORY_PATH = ".agentic/rule_ack"
RULE_ACK_CURRENT_PATH = f"{RULE_ACK_DIRECTORY_PATH}/current.json"

TRANSFER_INBOX_NEXT_COMMAND_PATH = ".agentic/transfer/inbox/next_command.py.txt"
TRANSFER_OUTBOX_DIRECTORY_PATH = ".agentic/transfer/outbox"
TRANSFER_OUTBOX_LAST_RESULT_PATH = f"{TRANSFER_OUTBOX_DIRECTORY_PATH}/last_result.txt"
LEGACY_TRANSFER_HANDOFF_REPORT_DIRECTORY_PATH = (
    "docs/reports/terminal/transfer_handoff_reports"
)
LEGACY_TRANSFER_HANDOFF_REPORT_JSON_PATH = (
    f"{LEGACY_TRANSFER_HANDOFF_REPORT_DIRECTORY_PATH}/latest-transfer-handoff-report.json"
)
LEGACY_TRANSFER_HANDOFF_REPORT_LOG_PATH = (
    f"{LEGACY_TRANSFER_HANDOFF_REPORT_DIRECTORY_PATH}/latest-transfer-handoff-report.log"
)

KNOWN_VOLATILE_TRANSFER_PATHS = (
    TRANSFER_INBOX_NEXT_COMMAND_PATH,
    TRANSFER_OUTBOX_LAST_RESULT_PATH,
    RULE_ACK_CURRENT_PATH,
    LEGACY_TRANSFER_HANDOFF_REPORT_JSON_PATH,
    LEGACY_TRANSFER_HANDOFF_REPORT_LOG_PATH,
)


def normalize_status_path(path: str) -> str:
    return path.strip().strip('"').rstrip("/")


def _is_dir_or_child(path: str, directory: str) -> bool:
    return path == directory or path.startswith(f"{directory}/")


def is_rule_ack_path(path: str) -> bool:
    return _is_dir_or_child(normalize_status_path(path), RULE_ACK_DIRECTORY_PATH)


def is_known_volatile_status_path(path: str) -> bool:
    normalized = normalize_status_path(path)
    if not normalized:
        return False
    return (
        is_rule_ack_path(normalized)
        or _is_dir_or_child(normalized, TRANSFER_OUTBOX_DIRECTORY_PATH)
        or normalized.startswith(f"{LEGACY_TRANSFER_HANDOFF_REPORT_DIRECTORY_PATH}/latest-")
    )
