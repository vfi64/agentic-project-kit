"""Read-only release-count deadline gate for self-hosted Kit findings."""

from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess

from packaging.version import Version

from agentic_project_kit.greenfield_status import CATALOG
from agentic_project_kit.project_direction import PROJECT_DIRECTION_PATH, load_project_direction
from agentic_project_kit.release_version_sources import is_kit_self_hosting


_RELEASE_TAG = re.compile(r"^v(\d+\.\d+\.\d+)$")


def _tags(root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "tag", "--list", "v*"], cwd=root, text=True, capture_output=True, check=False,
    )
    if result.returncode != 0:
        raise ValueError(f"release deadline: cannot read release tags: {result.stderr.strip()}")
    return result.stdout.splitlines()


def deadline_blockers(
    root: Path, target_version: str, *, release_tags: list[str] | None = None,
) -> list[str]:
    """Return due OPEN findings; malformed release authority fails closed."""
    root = Path(root).resolve()
    direction_path = root / PROJECT_DIRECTION_PATH
    catalog_path = root / CATALOG
    if not is_kit_self_hosting(root) or (not direction_path.exists() and not catalog_path.exists()):
        return []
    if not direction_path.is_file() or not catalog_path.is_file():
        raise ValueError("release deadline: planning authority or finding catalog missing")
    try:
        direction = load_project_direction(root).data
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        target = Version(target_version)
        findings = {item["id"]: item for item in catalog["findings"]}
        plans = direction["plans"]
        if not isinstance(plans, list):
            raise TypeError("plans must be a list")
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise ValueError(f"release deadline: invalid planning authority or catalog: {exc}") from exc
    blockers: list[str] = []
    for plan in plans:
        if not isinstance(plan, dict) or "deadline" not in plan:
            continue
        try:
            spec = plan["deadline"]
            if not isinstance(spec, dict) or spec["kind"] != "release_count_after":
                raise ValueError("unsupported deadline kind")
            anchor_text = spec["anchor_release"]
            anchor = Version(anchor_text)
            count = spec["max_releases"]
            if not isinstance(anchor_text, str) or not _RELEASE_TAG.fullmatch("v" + anchor_text):
                raise ValueError("invalid anchor release")
            if isinstance(count, bool) or not isinstance(count, int) or count < 1:
                raise ValueError("invalid max_releases")
            finding_id = plan["finding"]
            finding = findings[finding_id]
            state = finding["kit_state"]
            if state not in {"OPEN", "PARTIAL", "CLOSED"}:
                raise ValueError("invalid finding state")
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"release deadline: invalid plan {plan.get('id', '?')}: {exc}") from exc
        if state != "OPEN" or target <= anchor:
            continue
        tags = release_tags if release_tags is not None else _tags(root)
        releases = {Version(match.group(1)) for tag in tags if (match := _RELEASE_TAG.fullmatch(tag))}
        if anchor not in releases:
            raise ValueError(f"release deadline: anchor tag v{anchor} missing")
        number = len({version for version in releases if anchor < version < target}) + 1
        if number >= count:
            ordinal = "second" if count == 2 else f"number {count}"
            blockers.append(
                f"{finding_id}: release deadline reached at {target} "
                f"({ordinal} release after {anchor})"
            )
    return blockers
