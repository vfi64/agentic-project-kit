"""Lower bound of a release: the previous v* tag, or the root commit of the first release (KIT-GF-118).

Owner decision 2026-11-15: a project without a previous release tag makes its first release. Its
release notes start at the root commit, product commits without a PR number are listed as direct
commits instead of blocking (only in the first release), and the B4 gate of ``release run`` carries
the field ``first_release``, which its approval signature binds. ``init`` creates no tag.

A first release is only derived when no ``v*`` tag exists locally and the origin lists none: a clone
that has not fetched its tags must not restart the notes at the root commit.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import subprocess

RELEASE_TAG = re.compile(r"^v")  # same rule as the former _latest_release_tag
FIRST_RELEASE_RANGE = "root"


@dataclass(frozen=True)
class ReleaseRange:
    from_tag: str  # "" for the first release
    first_release: bool
    blockers: tuple[str, ...] = ()

    def notes_args(self) -> list[str]:
        return ["--first-release"] if self.first_release else ["--from-tag", self.from_tag]

    def label(self) -> str:
        return FIRST_RELEASE_RANGE if self.first_release else self.from_tag


def _git(root: Path, *argv: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *argv], cwd=root, text=True, capture_output=True, check=False)


def local_release_tags(root: Path) -> list[str]:
    """Local v* tags, newest first (same order as the previous derivation)."""
    done = _git(root, "tag", "--sort=-creatordate")
    if done.returncode != 0:
        return []
    return [tag for tag in (line.strip() for line in done.stdout.splitlines()) if RELEASE_TAG.match(tag)]


def origin_release_tags(root: Path) -> tuple[list[str], str]:
    """v* tags the origin lists; the second value is an error text when the origin cannot be read."""
    done = _git(root, "ls-remote", "--tags", "--refs", "origin", "refs/tags/v*")
    if done.returncode != 0:
        return [], (done.stderr or done.stdout).strip() or f"git ls-remote returned {done.returncode}"
    tags = [line.split("refs/tags/", 1)[1] for line in done.stdout.splitlines() if "refs/tags/" in line]
    return [tag for tag in tags if RELEASE_TAG.match(tag)], ""


def root_commit(root: Path, ref: str = "HEAD") -> str:
    done = _git(root, "rev-list", "--max-parents=0", ref)
    roots = done.stdout.split() if done.returncode == 0 else []
    return roots[-1] if roots else ""


def resolve(root: Path, from_tag: str = "") -> ReleaseRange:
    """The explicit tag, else the newest local v* tag, else the first release."""
    if from_tag.strip():
        return ReleaseRange(from_tag=from_tag.strip(), first_release=False)
    tags = local_release_tags(root)
    if tags:
        return ReleaseRange(from_tag=tags[0], first_release=False)
    remote, error = origin_release_tags(root)
    if error:
        return ReleaseRange("", True, (f"first-release-origin-tags-unreadable: {error[-300:]}",))
    if remote:
        return ReleaseRange("", True, (
            f"release-tags-not-fetched: origin lists {', '.join(sorted(remote)[:5])}; run git fetch --tags origin",))
    return ReleaseRange(from_tag="", first_release=True)


def first_release_gate(root: Path, target_commit: str) -> dict[str, object] | None:
    """The ``first_release`` field of the B4 gate, or None when a previous v* tag exists (KIT-GF-118).

    The approval signature of B4 covers the gate, so the owner approves explicitly that the notes
    start at the root commit and which commits enter the release as direct commits.
    """
    if local_release_tags(root):
        return None
    from agentic_project_kit.release_notes import build_release_notes_report

    report = build_release_notes_report(root, version="0.0.0", from_tag="", to_ref=target_commit or "HEAD",
                                        first_release=True, private_unclassified_fallback=False)
    direct = [item.commit_sha for item in (*report.items, *report.administrative_items)
              if any(evidence.get("type") == "direct_commit" for evidence in item.evidence)]
    return {"range": FIRST_RELEASE_RANGE, "root_commit": root_commit(root, target_commit or "HEAD"),
            "direct_commits": direct}
