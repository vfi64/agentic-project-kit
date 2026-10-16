"""Bind a transfer order's freshness anchor to the commit it was written on (WOTB-07, WOTB-08).

An order names the HEAD it was written on (``expected_current_head``, ``expected_head`` or
``created_for_head``). A committed order cannot contain its own commit hash, so the anchor is
checked against the commit the order was written on (owner decision 2026-10-16):

- if the order file has uncommitted changes or is untracked, the anchor must equal ``HEAD``;
- otherwise the anchor must equal the first parent of the commit that last changed the file.

The anchor must be a full 40-character commit hash. A prefix, however long, is refused.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ANCHOR_KEYS = ("expected_current_head", "expected_head", "created_for_head")
_FULL_SHA = re.compile(r"^[0-9a-f]{40}$")


@dataclass(frozen=True)
class AnchorCheck:
    ok: bool
    anchor: str
    expected: str
    basis: str
    reason: str = ""


def order_anchor(data: dict[str, Any]) -> str:
    for key in ANCHOR_KEYS:
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _git(root: Path, *args: str) -> tuple[int, str]:
    completed = subprocess.run(["git", *args], cwd=root, text=True, capture_output=True, check=False)
    return completed.returncode, completed.stdout.strip()


def expected_order_anchor(root: Path, order_path: Path) -> tuple[str, str]:
    """Return ``(expected_commit, basis)``; ``expected_commit`` is empty when it cannot be derived."""
    root_path = Path(root)
    candidate = order_path if order_path.is_absolute() else root_path / order_path
    try:
        rel = candidate.resolve().relative_to(root_path.resolve()).as_posix()
    except ValueError:
        return "", "order_outside_repository"
    code, status = _git(root_path, "status", "--porcelain=v1", "--", rel)
    if code != 0:
        return "", "git_status_failed"
    if status:
        code, head = _git(root_path, "rev-parse", "HEAD")
        return (head, "uncommitted_order_on_head") if code == 0 else ("", "head_unresolved")
    code, last = _git(root_path, "log", "-1", "--format=%H", "--", rel)
    if code != 0 or not last:
        return "", "order_commit_not_found"
    code, parent = _git(root_path, "rev-parse", "--verify", "--quiet", f"{last}^1")
    if code != 0 or not parent:
        return "", "order_commit_has_no_parent"
    return parent, "order_commit_parent"


def check_order_anchor(root: Path, order_path: Path, data: dict[str, Any]) -> AnchorCheck:
    anchor = order_anchor(data)
    if not anchor:
        return AnchorCheck(False, "", "", "", "stale_order_missing_freshness_anchor")
    if not _FULL_SHA.match(anchor):
        return AnchorCheck(False, anchor, "", "", "freshness_anchor_not_full_commit_hash")
    expected, basis = expected_order_anchor(root, order_path)
    if not expected:
        return AnchorCheck(False, anchor, "", basis, f"freshness_anchor_unverifiable:{basis}")
    if anchor != expected:
        return AnchorCheck(False, anchor, expected, basis, "stale_transfer_order_head_mismatch")
    return AnchorCheck(True, anchor, expected, basis)
