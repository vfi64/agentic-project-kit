"""Guardrails for recurring release/process standard errors.

The functions here are deliberately small and pure. They make release and
handoff orchestration failures testable before they reach a live PR.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


VOLATILE_HANDOFF_REPORTS = {
    "docs/reports/terminal/transfer_handoff_reports/latest-transfer-handoff-report.json",
    "docs/reports/terminal/transfer_handoff_reports/latest-transfer-handoff-report.log",
}

HANDOFF_PREFIXES = (
    "docs/handoff/",
    "docs/reports/handoff-packages/",
    "docs/reports/terminal/",
    "docs/reports/transfer_runs/",
)

RELEASE_METADATA_PATHS = {
    "CHANGELOG.md",
    "CITATION.cff",
    "README.md",
    "docs/STATUS.md",
    "pyproject.toml",
    "src/agentic_project_kit/__init__.py",
}

BLOCKED_STATUSES = {"BLOCKED", "MISS", "STALE", "PENDING"}
FAILED_STATUSES = {"FAIL", "FAILED", "ERROR"}


@dataclass(frozen=True)
class GitStatusEntry:
    index: str
    worktree: str
    path: str
    original_path: str | None = None

    @property
    def is_dirty(self) -> bool:
        return self.index != " " or self.worktree != " "


def parse_git_status_short(output: str) -> list[GitStatusEntry]:
    """Parse `git status --short` without dropping the first path character.

    The short format uses two status columns, then a separating space, then
    the path. A common bug is `line[3:]` on strings copied from logs where
    leading spaces may already be visually collapsed or where rename syntax
    must be preserved.
    """

    entries: list[GitStatusEntry] = []
    for raw_line in output.splitlines():
        if not raw_line.strip():
            continue
        if len(raw_line) < 3:
            raise ValueError(f"invalid git status --short line: {raw_line!r}")

        index = raw_line[0]
        worktree = raw_line[1]
        separator = raw_line[2]
        if separator != " ":
            raise ValueError(f"invalid git status --short separator in line: {raw_line!r}")

        path_text = raw_line[3:]
        if not path_text:
            raise ValueError(f"missing path in git status --short line: {raw_line!r}")

        original_path: str | None = None
        path = path_text
        if " -> " in path_text:
            original_path, path = path_text.split(" -> ", 1)

        entries.append(
            GitStatusEntry(
                index=index,
                worktree=worktree,
                path=path,
                original_path=original_path,
            )
        )
    return entries


def git_status_paths(output: str) -> list[str]:
    return [entry.path for entry in parse_git_status_short(output)]


def split_known_volatile_paths(paths: list[str]) -> tuple[list[str], list[str]]:
    volatile = [path for path in paths if path in VOLATILE_HANDOFF_REPORTS]
    unexpected = [path for path in paths if path not in VOLATILE_HANDOFF_REPORTS]
    return volatile, unexpected


def load_structured_text(text: str, *, path: str = "") -> Any:
    """Load JSON/YAML by content, not by file suffix.

    Some generated files intentionally use a historic `.yaml` name while the
    payload is JSON. JSON is tried first because JSON is valid YAML but the
    reverse is not generally true.
    """

    stripped = text.lstrip()
    if stripped.startswith(("{", "[")):
        return json.loads(text)

    try:
        import yaml  # type: ignore[import-untyped]
    except Exception as exc:  # pragma: no cover - dependency guard
        raise ValueError(f"cannot parse structured file without PyYAML: {path}") from exc

    return yaml.safe_load(text)


def dump_structured_like_existing(data: Any, *, existing_text: str) -> str:
    stripped = existing_text.lstrip()
    if stripped.startswith(("{", "[")):
        return json.dumps(data, indent=2, sort_keys=True) + "\n"

    try:
        import yaml  # type: ignore[import-untyped]
    except Exception as exc:  # pragma: no cover - dependency guard
        raise ValueError("cannot dump YAML-like structured text without PyYAML") from exc

    return yaml.safe_dump(data, sort_keys=True, allow_unicode=True)


def reject_invalid_pr_complete_args(argv: list[str]) -> None:
    """Block the human-standard-error `pr-complete --post-merge-complete`."""

    if "pr-complete" in argv and "--post-merge-complete" in argv:
        raise ValueError(
            "--post-merge-complete is a pr-create-complete lifecycle option; "
            "for an existing PR run pr-complete first and post-merge-complete separately."
        )


def require_release_notes_from_tag(version: str, from_tag: str | None) -> None:
    if not from_tag or not from_tag.strip():
        raise ValueError("release-notes-generate requires --from-tag for release-prep evidence.")
    if from_tag.strip() in {version, f"v{version}"}:
        raise ValueError("--from-tag must point to the previous release, not the release being prepared.")



def is_transfer_result_payload(payload: dict[str, Any]) -> bool:
    """Return true only for structured transfer wrapper result payloads.

    GitHub/gh command outputs and unrelated JSON snippets may contain fields such
    as `state` or `status`; those must not be interpreted as transfer blockers.
    """

    kind = str(payload.get("kind", ""))
    action = str(payload.get("action", ""))
    if kind.startswith("transfer_"):
        return True
    if action.startswith(("pr-", "post-merge", "repo-", "sync-", "transfer")) and (
        "result_status" in payload or "blockers" in payload or "failed_step" in payload
    ):
        return True
    return False


def rc_from_result_payload(payload: dict[str, Any]) -> int:
    status = str(payload.get("result_status", payload.get("status", ""))).upper()
    if status == "PASS":
        return 0
    if status in BLOCKED_STATUSES:
        return 2
    if status in FAILED_STATUSES:
        return 1

    blockers = payload.get("blockers")
    if isinstance(blockers, list) and blockers:
        return 2
    failed_step = payload.get("failed_step")
    if failed_step:
        return 2
    return 1


def command_reference_paths_are_current(paths: list[str]) -> bool:
    required = {
        "docs/reference/AGENTIC_KIT_COMMANDS.md",
        "docs/reference/agentic-kit-commands.json",
    }
    return required.issubset(set(paths))


def release_and_handoff_paths_are_mixed(paths: list[str]) -> bool:
    has_release = any(path in RELEASE_METADATA_PATHS for path in paths)
    has_handoff = any(path.startswith(HANDOFF_PREFIXES) for path in paths)
    return has_release and has_handoff


def require_no_release_handoff_mix(paths: list[str]) -> None:
    if release_and_handoff_paths_are_mixed(paths):
        raise ValueError(
            "release metadata and generated handoff/report carriers must not be committed in one release-prep PR"
        )


def require_successor_package_mentions_version(texts: list[str], version: str) -> None:
    combined = "\n".join(texts)
    if version not in combined:
        raise ValueError(f"successor handoff package does not mention current release version {version}")


def require_pending_doi_marker(changelog_section: str, *, version: str, verified_version: str | None) -> None:
    if verified_version == version:
        return
    if "Zenodo DOI verification pending" not in changelog_section:
        raise ValueError(f"CHANGELOG section for {version} needs a Zenodo DOI verification pending marker.")


def citation_release_date(citation_text: str) -> str | None:
    match = re.search(r'^date-released:\s*["\']?(\d{4}-\d{2}-\d{2})["\']?$', citation_text, re.M)
    return match.group(1) if match else None


def require_release_date_contract(citation_text: str, expected_date: str) -> None:
    actual = citation_release_date(citation_text)
    if actual != expected_date:
        raise ValueError(f"CITATION date-released drift: expected {expected_date}, got {actual or 'missing'}")


def safe_compact_findings(findings: dict[str, list[str]], *, per_term: int = 12, max_line: int = 500) -> dict[str, list[str]]:
    compact: dict[str, list[str]] = {}
    for term, lines in findings.items():
        compact[term] = [line[:max_line] for line in lines[:per_term]]
    return compact


def assert_uploadable_artifact(path: Path, *, max_bytes: int = 2_000_000) -> None:
    size = path.stat().st_size
    if size > max_bytes:
        raise ValueError(f"artifact too large for chat upload: {path} has {size} bytes")
