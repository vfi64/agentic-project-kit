from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal


ActivityActor = Literal["user", "kit"]
ActivityStatus = Literal["PASS", "BLOCKED", "ERROR", "INFO"]


@dataclass(frozen=True)
class ActivityEntry:
    actor: ActivityActor
    label: str
    body: str
    status: ActivityStatus
    created_at_utc: str


def _now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def normalize_activity_status(status: str | None, body: str = "") -> ActivityStatus:
    if status is not None and str(status).strip():
        normalized = str(status).strip().upper().replace("-", "_")
        if normalized in {"PASS", "PASSED", "SUCCESS", "OK"}:
            return "PASS"
        if normalized in {"BLOCK", "BLOCKED", "WAIT", "WAIT_FOR_D2"}:
            return "BLOCKED"
        if normalized in {"FAIL", "FAILED", "ERROR"}:
            return "ERROR"
        return "INFO"

    text = body.upper()
    if "BLOCKED" in text or "RESULT_STATUS=BLOCK" in text or '"RESULT_STATUS": "BLOCK' in text:
        return "BLOCKED"
    if "TRACEBACK" in text or "ERROR" in text or "FAILED" in text or "RETURNCODE=127" in text:
        return "ERROR"
    if "RESULT_STATUS=PASS" in text or "STATE=PASS" in text or '"RESULT_STATUS": "PASS"' in text:
        return "PASS"
    return "INFO"


class ActivityLog:
    def __init__(self) -> None:
        self._entries: list[ActivityEntry] = []

    def log_action(self, label: str) -> ActivityEntry:
        entry = ActivityEntry(
            actor="user",
            label=label.strip() or "Action",
            body=f"You ran: {label.strip() or 'Action'}",
            status="INFO",
            created_at_utc=_now_utc(),
        )
        self._entries.append(entry)
        return entry

    def log_result(self, label: str, status: str | None, body: str) -> ActivityEntry:
        entry = ActivityEntry(
            actor="kit",
            label=label.strip() or "Result",
            body=body,
            status=normalize_activity_status(status, body),
            created_at_utc=_now_utc(),
        )
        self._entries.append(entry)
        return entry

    def entries(self) -> tuple[ActivityEntry, ...]:
        return tuple(self._entries)

    def clear(self) -> None:
        self._entries.clear()
