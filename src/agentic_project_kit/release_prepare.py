from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re


VERSION_RE = r"\d+\.\d+\.\d+"


@dataclass(frozen=True)
class ReleasePrepareResult:
    version: str
    date: str
    changed_paths: list[str]
    dry_run: bool

    @property
    def ok(self) -> bool:
        return True

    def as_dict(self) -> dict[str, object]:
        return {
            "ok": self.ok,
            "version": self.version,
            "date": self.date,
            "changed_paths": self.changed_paths,
            "dry_run": self.dry_run,
        }


def _read(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(path)
    return path.read_text(encoding="utf-8")


def _write_if_changed(path: Path, text: str, *, dry_run: bool, changed: list[str], root: Path) -> None:
    old = _read(path)
    if old == text:
        return
    changed.append(path.relative_to(root).as_posix())
    if not dry_run:
        path.write_text(text, encoding="utf-8")


def _replace_required(pattern: str, repl: str, text: str, *, label: str) -> str:
    new, count = re.subn(pattern, repl, text, count=1, flags=re.MULTILINE)
    if count != 1:
        raise ValueError(f"Could not update {label}; expected exactly one match for {pattern!r}")
    return new


def _prepared_release_line(version: str) -> str:
    return f"Version `{version}` is the current release line prepared"


def _update_pyproject(text: str, version: str) -> str:
    return _replace_required(
        r'^version\s*=\s*"[^"]+"$',
        f'version = "{version}"',
        text,
        label="pyproject.toml project.version",
    )


def _update_package_init(text: str, version: str) -> str:
    return _replace_required(
        r'^__version__\s*=\s*"[^"]+"$',
        f'__version__ = "{version}"',
        text,
        label="package __version__",
    )


def _update_readme(text: str, version: str) -> str:
    line = _prepared_release_line(version)
    if "current release line prepared" in text:
        return re.sub(
            rf"Version `(?:v)?{VERSION_RE}` is the current release line prepared",
            line,
            text,
            count=1,
        )
    raise ValueError("README.md has no current release line prepared marker")


def _update_current_version_doc(text: str, version: str, *, label: str) -> str:
    return _replace_required(
        rf"Current version:\s*{VERSION_RE}",
        f"Current version: {version}",
        text,
        label=label,
    )


def _changelog_section(version: str, date: str) -> str:
    return (
        f"## v{version} - {date}\n\n"
        f"- Release metadata prepared for v{version}; Zenodo DOI verification pending until the GitHub release is created.\n"
        "- Hardened deterministic release preparation/check workflow with guarded metadata updates and no tag or publication side effects.\n"
        "- Recorded release evidence handoff and current-state documentation boundary for successor validation.\n"
    )


def _update_changelog(text: str, version: str, date: str) -> str:
    existing = re.compile(
        rf"^##\s+v{re.escape(version)}\s+-\s+\d{{4}}-\d{{2}}-\d{{2}}.*?(?=^##\s+v|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    section = _changelog_section(version, date)
    if existing.search(text):
        return existing.sub(section.rstrip() + "\n\n", text, count=1)

    first_release = re.search(r"^##\s+v\d+\.\d+\.\d+", text, flags=re.MULTILINE)
    if not first_release:
        raise ValueError("CHANGELOG.md has no versioned release section anchor")
    index = first_release.start()
    return text[:index] + section + "\n" + text[index:]


def prepare_release_state(
    project_root: Path | str = ".",
    *,
    version: str,
    date: str,
    dry_run: bool = False,
) -> ReleasePrepareResult:
    """Prepare release metadata files deterministically.

    This command only edits local repository metadata. It does not create tags,
    GitHub releases, Zenodo records, commits, or PRs.
    """
    if not re.fullmatch(VERSION_RE, version):
        raise ValueError(f"Invalid release version: {version!r}; expected MAJOR.MINOR.PATCH")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
        raise ValueError(f"Invalid release date: {date!r}; expected YYYY-MM-DD")

    root = Path(project_root).resolve()
    changed: list[str] = []

    updates = {
        root / "pyproject.toml": _update_pyproject(_read(root / "pyproject.toml"), version),
        root / "src" / "agentic_project_kit" / "__init__.py": _update_package_init(
            _read(root / "src" / "agentic_project_kit" / "__init__.py"),
            version,
        ),
        root / "README.md": _update_readme(_read(root / "README.md"), version),
        root / "docs" / "STATUS.md": _update_current_version_doc(
            _read(root / "docs" / "STATUS.md"),
            version,
            label="docs/STATUS.md current version",
        ),
        root / "docs" / "handoff" / "CURRENT_HANDOFF.md": _update_current_version_doc(
            _read(root / "docs" / "handoff" / "CURRENT_HANDOFF.md"),
            version,
            label="docs/handoff/CURRENT_HANDOFF.md current version",
        ),
        root / "CHANGELOG.md": _update_changelog(_read(root / "CHANGELOG.md"), version, date),
    }

    for path, text in updates.items():
        _write_if_changed(path, text, dry_run=dry_run, changed=changed, root=root)

    return ReleasePrepareResult(version=version, date=date, changed_paths=sorted(changed), dry_run=dry_run)
