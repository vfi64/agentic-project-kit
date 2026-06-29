from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any


_VERSION_PATTERN = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")


@dataclass(frozen=True)
class ReleaseGuiMessage:
    headline: str
    detail: str
    blockers: tuple[str, ...] = ()
    allow_confirm: bool = False


def normalize_release_version(value: str) -> str | None:
    version = value.strip()
    return version if _VERSION_PATTERN.fullmatch(version) else None


def release_ready_args(version: str) -> tuple[str, ...]:
    return ("release", "ready", "--version", version, "--json")


def release_prepare_args(version: str) -> tuple[str, ...]:
    return ("release", "prepare", "--version", version, "--write", "--json")


def release_preview_signature(*, version: str, state_signature: str) -> str:
    return f"{version}::{state_signature}"


def humanize_release_result(payload: dict[str, Any], *, preview: bool) -> ReleaseGuiMessage:
    status = str(payload.get("result_status", "")).upper()
    blockers = tuple(str(item) for item in payload.get("blockers", ()) if str(item))
    version = str(payload.get("version", "")).strip()
    if status == "PASS" and preview:
        return ReleaseGuiMessage(
            headline="Release readiness passed.",
            detail=f"Version {version} is ready to prepare. Review the preview, then confirm create release.",
            allow_confirm=True,
        )
    if status == "PASS":
        return ReleaseGuiMessage(
            headline="Release prepared.",
            detail=(
                f"Version {version} was prepared by agentic-kit release prepare. "
                "Publishing and tagging remain separate gated steps."
            ),
        )
    return ReleaseGuiMessage(
        headline="Release is not ready.",
        detail="No release files were prepared. Fix the blocked readiness checks first.",
        blockers=blockers or ("release-ready",),
    )

