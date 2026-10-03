"""Release version anchors of a workspace (KIT-GF-032, slice A).

The Kit's own release files (``src/agentic_project_kit/__init__.py``,
``CITATION.cff``, ``docs/STATUS.md``, ``docs/handoff/CURRENT_HANDOFF.md`` and
the README version marker) are anchors only in the Kit's self-hosting layout.
An external workspace (a workspace manifest and no Kit package) derives its
anchors from its own files:

* ``pyproject.toml`` ``version`` (always required);
* the package ``__version__`` only where the package declares a literal one
  (``__version__ = "x"``); an indirect assignment leaves pyproject as authority;
* ``CHANGELOG.md`` when it exists;
* ``CITATION.cff`` when it exists or the publication policy uses Zenodo;
* ``docs/STATUS.md`` / ``docs/handoff/CURRENT_HANDOFF.md`` only when they carry
  a ``Current version:`` line.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

KIT_PACKAGE_INIT = "src/agentic_project_kit/__init__.py"
WORKSPACE_MANIFEST = ".agentic/config.yaml"
LITERAL_VERSION_RE = re.compile(r'^__version__\s*=\s*["\']([^"\']+)["\']', re.MULTILINE)
PROJECT_NAME_RE = re.compile(r'^name\s*=\s*["\']([^"\']+)["\']', re.MULTILINE)


@dataclass(frozen=True)
class VersionAnchor:
    """One file that must name the release version."""

    path: str
    label: str
    needle: str | None   # substring check (release-check); None: use ``pattern``
    pattern: str         # regular expression (release commit integrity)

    def matches(self, text: str) -> bool:
        if self.needle is not None:
            return self.needle in text
        return re.search(self.pattern, text, re.MULTILINE) is not None


def is_kit_self_hosting(root: Path) -> bool:
    """The Kit's own layout, or a legacy root without a workspace manifest."""
    root = Path(root)
    return (root / KIT_PACKAGE_INIT).is_file() or not (root / WORKSPACE_MANIFEST).is_file()


def _kit_anchors(version: str) -> tuple[VersionAnchor, ...]:
    v = re.escape(version)
    return (
        VersionAnchor("pyproject.toml", "pyproject version", f'version = "{version}"',
                      rf'version\s*=\s*["\']{v}["\']'),
        VersionAnchor(KIT_PACKAGE_INIT, "package __version__", f'__version__ = "{version}"',
                      rf'__version__\s*=\s*["\']{v}["\']'),
        VersionAnchor("CHANGELOG.md", "CHANGELOG version", f"v{version}", rf"^##\s+v{v}\s+-"),
        VersionAnchor("README.md", "README version", f"Version `{version}`", rf"Version\s+`{v}`"),
        VersionAnchor("CITATION.cff", "CITATION version", f"version: {version}", rf"^version:\s+{v}$"),
        VersionAnchor("docs/STATUS.md", "STATUS version", f"Current version: {version}",
                      rf"^Current version:\s+{v}$"),
        VersionAnchor("docs/handoff/CURRENT_HANDOFF.md", "CURRENT_HANDOFF version",
                      f"Current version: {version}", rf"Current version:\s+{v}"),
    )


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def package_version_file(root: Path) -> str | None:
    """Relative path of the package file with a literal ``__version__``, if any."""
    root = Path(root)
    match = PROJECT_NAME_RE.search(_read(root / "pyproject.toml"))
    if not match:
        return None
    package = match.group(1).strip().replace("-", "_").replace(".", "_").lower()
    for base in ("src", "."):
        for name in ("__init__.py", "version.py", "_version.py"):
            candidate = root / base / package / name
            if LITERAL_VERSION_RE.search(_read(candidate)):
                return candidate.relative_to(root).as_posix()
    return None


def release_version_anchors(root: Path, version: str, *, uses_zenodo: bool | None = None) -> tuple[VersionAnchor, ...]:
    """The files that must name ``version`` before a release of this workspace."""
    root = Path(root)
    if is_kit_self_hosting(root):
        return _kit_anchors(version)
    if uses_zenodo is None:
        from agentic_project_kit.publication_policy import publication_policy_for
        uses_zenodo = publication_policy_for(root).uses_zenodo
    by_path = {anchor.path: anchor for anchor in _kit_anchors(version)}
    anchors = [by_path["pyproject.toml"]]
    package_file = package_version_file(root)
    if package_file:
        v = re.escape(version)
        anchors.append(VersionAnchor(package_file, "package __version__", f'__version__ = "{version}"',
                                     rf'__version__\s*=\s*["\']{v}["\']'))
    if (root / "CHANGELOG.md").is_file():
        # Keep-a-Changelog headings ("## [1.2.3]") as well as the Kit's "## v1.2.3 - date".
        anchors.append(VersionAnchor("CHANGELOG.md", "CHANGELOG version", None,
                                     rf"^##\s+\[?v?{re.escape(version)}\]?(?:\s|$)"))
    if (root / "CITATION.cff").is_file() or uses_zenodo:
        anchors.append(by_path["CITATION.cff"])
    for relative in ("docs/STATUS.md", "docs/handoff/CURRENT_HANDOFF.md"):
        if "Current version:" in _read(root / relative):
            anchors.append(by_path[relative])
    return tuple(anchors)
