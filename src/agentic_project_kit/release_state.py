from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import tomllib


PREPARED_RELEASE_LINE = "Version `{version}` is the current release line prepared"
VERIFIED_RELEASE_POINTER = (
    "verified version-specific DOI notes are maintained in `docs/releases/VERIFIED_RELEASES.md`"
)


@dataclass(frozen=True)
class ReleaseStateCheck:
    ok: bool
    version: str
    errors: list[str]
    findings: list[str]

    def as_dict(self) -> dict[str, object]:
        return {
            "ok": self.ok,
            "version": self.version,
            "errors": self.errors,
            "findings": self.findings,
        }


def _read(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(path)
    return path.read_text(encoding="utf-8")


def project_version(project_root: Path) -> str:
    data = tomllib.loads(_read(project_root / "pyproject.toml"))
    return str(data["project"]["version"])


def package_version(project_root: Path) -> str | None:
    init_file = project_root / "src" / "agentic_project_kit" / "__init__.py"
    text = _read(init_file)
    match = re.search(r'__version__\s*=\s*"([^"]+)"', text)
    if not match:
        return None
    return match.group(1)


def check_release_state(project_root: Path | str = ".", expected_version: str | None = None) -> ReleaseStateCheck:
    root = Path(project_root)
    version = expected_version or project_version(root)
    errors: list[str] = []
    findings: list[str] = []

    pyproject_version = project_version(root)
    if pyproject_version != version:
        errors.append(f"pyproject.toml version is {pyproject_version}, expected {version}")
    else:
        findings.append(f"pyproject.toml version={version}")

    pkg_version = package_version(root)
    if pkg_version != version:
        errors.append(f"src/agentic_project_kit/__init__.py __version__ is {pkg_version}, expected {version}")
    else:
        findings.append(f"package __version__={version}")

    readme = _read(root / "README.md")
    prepared_line = PREPARED_RELEASE_LINE.format(version=version)
    if prepared_line not in readme:
        errors.append(f"README.md missing prepared release line for {version}")
    else:
        findings.append("README.md prepared release line present")

    if VERIFIED_RELEASE_POINTER not in readme:
        errors.append("README.md missing verified-release DOI pointer")
    else:
        findings.append("README.md verified-release DOI pointer present")

    status = _read(root / "docs" / "STATUS.md")
    status_line = f"Current version: {version}"
    if status_line not in status:
        errors.append(f"docs/STATUS.md missing '{status_line}'")
    else:
        findings.append("docs/STATUS.md current version present")

    handoff = _read(root / "docs" / "handoff" / "CURRENT_HANDOFF.md")
    if status_line not in handoff:
        errors.append(f"docs/handoff/CURRENT_HANDOFF.md missing '{status_line}'")
    else:
        findings.append("CURRENT_HANDOFF current version present")

    changelog = _read(root / "CHANGELOG.md")
    section_pattern = re.compile(
        rf"^##\s+v{re.escape(version)}\s+-\s+\d{{4}}-\d{{2}}-\d{{2}}.*?(?=^##\s+v|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    match = section_pattern.search(changelog)
    if not match:
        errors.append(f"CHANGELOG.md missing dated section for v{version}")
    else:
        section = match.group(0)
        findings.append(f"CHANGELOG.md section for v{version} present")
        normalized = section.lower()
        if "zenodo" not in normalized or ("doi" not in normalized and "pending" not in normalized):
            errors.append(f"CHANGELOG.md v{version} missing Zenodo DOI or pending verification marker")
        else:
            findings.append("CHANGELOG.md Zenodo pending/DOI marker present")

    return ReleaseStateCheck(ok=not errors, version=version, errors=errors, findings=findings)
