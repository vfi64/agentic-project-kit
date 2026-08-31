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
STATE_TRANSFER_HANDOFF_REPORT_DIRECTORY_PATH = (
    ".agentic/state/handoff/transfer_handoff_reports"
)
STATE_TRANSFER_HANDOFF_REPORT_JSON_PATH = (
    f"{STATE_TRANSFER_HANDOFF_REPORT_DIRECTORY_PATH}/latest-transfer-handoff-report.json"
)
STATE_TRANSFER_HANDOFF_REPORT_LOG_PATH = (
    f"{STATE_TRANSFER_HANDOFF_REPORT_DIRECTORY_PATH}/latest-transfer-handoff-report.log"
)
LEGACY_LOCAL_GC_REPORT_PATH = "tmp/local-gc-last.json"
LEGACY_LOCAL_GC_RUN_MARKER_PATH = "tmp/local-gc-last-run-id.txt"
LEGACY_LOCAL_COMMAND_STACK_STATE_PATH = "tmp/local-command-stack-state.json"
STATE_LOCAL_GC_REPORT_PATH = ".agentic/tmp/local-gc-last.json"
STATE_LOCAL_GC_RUN_MARKER_PATH = ".agentic/tmp/local-gc-last-run-id.txt"
STATE_LOCAL_COMMAND_STACK_STATE_PATH = ".agentic/tmp/local-command-stack-state.json"
STATE_WORKSPACE_LOCK_PATH = ".agentic/tmp/workspace.lock"
LEGACY_TRANSFER_RUN_DIRECTORY_PATH = "docs/reports/transfer_runs"
STATE_TRANSFER_RUN_DIRECTORY_PATH = ".agentic/state/handoff/transfer_runs"

KNOWN_RUNTIME_STATUS_PATHS = (
    LEGACY_LOCAL_GC_REPORT_PATH,
    LEGACY_LOCAL_GC_RUN_MARKER_PATH,
    LEGACY_LOCAL_COMMAND_STACK_STATE_PATH,
    STATE_LOCAL_GC_REPORT_PATH,
    STATE_LOCAL_GC_RUN_MARKER_PATH,
    STATE_LOCAL_COMMAND_STACK_STATE_PATH,
    STATE_WORKSPACE_LOCK_PATH,
)

KNOWN_VOLATILE_TRANSFER_PATHS = (
    TRANSFER_INBOX_NEXT_COMMAND_PATH,
    TRANSFER_OUTBOX_LAST_RESULT_PATH,
    RULE_ACK_CURRENT_PATH,
    LEGACY_TRANSFER_HANDOFF_REPORT_JSON_PATH,
    LEGACY_TRANSFER_HANDOFF_REPORT_LOG_PATH,
    STATE_TRANSFER_HANDOFF_REPORT_JSON_PATH,
    STATE_TRANSFER_HANDOFF_REPORT_LOG_PATH,
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
        normalized in KNOWN_RUNTIME_STATUS_PATHS
        or is_rule_ack_path(normalized)
        or normalized == TRANSFER_INBOX_NEXT_COMMAND_PATH
        or _is_dir_or_child(normalized, TRANSFER_OUTBOX_DIRECTORY_PATH)
        or _is_transfer_run_report_path(normalized)
        or _is_transfer_handoff_report_path(normalized)
    )


def _is_transfer_run_report_path(path: str) -> bool:
    if not (
        _is_dir_or_child(path, LEGACY_TRANSFER_RUN_DIRECTORY_PATH)
        or _is_dir_or_child(path, STATE_TRANSFER_RUN_DIRECTORY_PATH)
    ):
        return False
    return path.endswith((".json", ".log"))


def _is_transfer_handoff_report_path(path: str) -> bool:
    if not (
        _is_dir_or_child(path, LEGACY_TRANSFER_HANDOFF_REPORT_DIRECTORY_PATH)
        or _is_dir_or_child(path, STATE_TRANSFER_HANDOFF_REPORT_DIRECTORY_PATH)
    ):
        return False
    return path.endswith((".json", ".log"))


def status_path_from_short_line(line: str) -> str:
    raw = line.rstrip()
    if len(raw) >= 3 and raw[2] == " ":
        path_text = raw[3:]
    else:
        path_text = raw.strip()
    if " -> " in path_text:
        path_text = path_text.split(" -> ", 1)[1]
    return normalize_status_path(path_text)


def split_known_volatile_status(
    status_text: str,
    *,
    extra_known_paths: tuple[str, ...] | list[str] = (),
) -> tuple[str, list[str]]:
    extra = {normalize_status_path(path) for path in extra_known_paths}
    kept_lines: list[str] = []
    ignored_lines: list[str] = []
    for line in status_text.splitlines():
        if not line.strip():
            continue
        path = status_path_from_short_line(line)
        if path in extra or is_known_volatile_status_path(path):
            ignored_lines.append(line)
            continue
        kept_lines.append(line)
    return "\n".join(kept_lines), ignored_lines
