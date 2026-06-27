from __future__ import annotations

from typing import Literal

AccessLevel = Literal["basic", "advanced", "maintainer"]

ACCESS_LEVEL_ORDER: tuple[AccessLevel, ...] = ("basic", "advanced", "maintainer")
DEFAULT_ACCESS_LEVEL: AccessLevel = "basic"


def access_level_rank(level: AccessLevel) -> int:
    return ACCESS_LEVEL_ORDER.index(level)


def meets_min_access(current: AccessLevel, required: AccessLevel) -> bool:
    return access_level_rank(current) >= access_level_rank(required)


def normalize_access_level(value: str | None) -> AccessLevel:
    if value in ACCESS_LEVEL_ORDER:
        return value
    return DEFAULT_ACCESS_LEVEL
