from __future__ import annotations

FAILED_CHECK_CONCLUSIONS = frozenset(
    {
        "ACTION_REQUIRED",
        "CANCELLED",
        "FAILURE",
        "STARTUP_FAILURE",
        "STALE",
        "TIMED_OUT",
    }
)
SUCCESS_CHECK_CONCLUSIONS = frozenset({"SUCCESS", "NEUTRAL"})
OPTIONAL_SKIPPED_CHECK_NAMES = frozenset({"pytest-parallel-shadow"})


def normalize_check_conclusion(value: object) -> str:
    return str(value or "").upper()


def normalize_check_status(value: object) -> str:
    return str(value or "").upper()


def is_successful_check_conclusion(conclusion: str) -> bool:
    return conclusion in SUCCESS_CHECK_CONCLUSIONS


def is_failed_check_conclusion(conclusion: str) -> bool:
    return conclusion in FAILED_CHECK_CONCLUSIONS


def is_optional_skipped_check(
    name: str,
    *,
    status: str,
    conclusion: str,
) -> bool:
    return (
        status == "COMPLETED"
        and conclusion == "SKIPPED"
        and name in OPTIONAL_SKIPPED_CHECK_NAMES
    )
