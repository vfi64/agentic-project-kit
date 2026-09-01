from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re

from agentic_project_kit.command_manifest import load_manifest
from agentic_project_kit.dpa_current_handoff_lifecycle import evaluate_current_handoff_text_lifecycle
from agentic_project_kit.dpa_readiness import DEFAULT_READINESS_PATH
from agentic_project_kit.instruction_lint import command_manifest_ack_line
from agentic_project_kit.workspace import load_workspace


VERSION_RE = r"\d+\.\d+\.\d+"
CURRENT_HANDOFF_RELATIVE_PATH = "docs/handoff/CURRENT_HANDOFF.md"
DPA_RELEASE_PREP_CONTRACT_ID = "DPA-CURRENT-HANDOFF-RELEASE-PREP-v1"
DPA_RELEASE_PREP_TARGET_SCOPE = "CURRENT_HANDOFF_RELEASE_METADATA"
DPA_RELEASE_PREP_WRITER_ID = "WRT-CH-002"
DPA_RELEASE_PREP_RENDERER_ID = "agentic_project_kit.release_prepare"
DPA_RELEASE_PREP_RENDERER_SEMANTIC_VERSION = "1"
DPA_RELEASE_PREP_SOURCE_PATH = "<agentic-kit-release-prep-inputs>"
DPA_READINESS_ACK_RELATIVE_PATH = DEFAULT_READINESS_PATH.as_posix()


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


def _prepared_release_status_line(version: str) -> str:
    return (
        f"Prepared release: `v{version}`; GitHub Release, tag publication, "
        "PyPI publication, and Zenodo version DOI verification are pending."
    )


def _update_pyproject(text: str, version: str) -> str:
    return _replace_required(
        r'^version\s*=\s*"[^"]+"$',
        f'version = "{version}"',
        text,
        label="pyproject.toml project.version",
    )


def _update_citation(text: str, version: str, date: str) -> str:
    updated = _replace_required(
        r"^version:\s*[\"']?[^\"'\n]+[\"']?$",
        f"version: {version}",
        text,
        label="CITATION.cff version",
    )
    return _replace_required(
        r"^date-released:\s*[\"']?\d{4}-\d{2}-\d{2}[\"']?$",
        f'date-released: "{date}"',
        updated,
        label="CITATION.cff date-released",
    )


def _update_package_init(text: str, version: str) -> str:
    return _replace_required(
        r'^__version__\s*=\s*"[^"]+"$',
        f'__version__ = "{version}"',
        text,
        label="package __version__",
    )


def _update_readme(text: str, version: str) -> str:
    matches = re.findall(rf"^Current version:\s*{VERSION_RE}\s*$", text, flags=re.MULTILINE)
    if len(matches) != 1:
        raise ValueError(f"README.md must contain exactly one Current version marker, found {len(matches)}")
    updated = _replace_required(
        rf"^Current version:\s*{VERSION_RE}\s*$",
        f"Current version: {version}",
        text,
        label="README.md current version",
    )
    line = _prepared_release_line(version)
    if "current release line prepared" in updated:
        updated = re.sub(
            rf"Version `(?:v)?{VERSION_RE}` is the current release line prepared",
            line,
            updated,
            count=1,
        )
    if re.search(r"^Prepared release:\s*`v" + VERSION_RE + r"`;", updated, flags=re.MULTILINE):
        updated = _replace_required(
            r"^Prepared release:\s*`v"
            + VERSION_RE
            + r"`; GitHub Release, tag publication(?:, PyPI publication)?, and Zenodo version DOI verification are [^.]+\.$",
            _prepared_release_status_line(version),
            updated,
            label="README.md prepared release status",
        )
    return updated


def _update_current_version_doc(text: str, version: str, *, label: str) -> str:
    return _replace_required(
        rf"Current version:\s*{VERSION_RE}",
        f"Current version: {version}",
        text,
        label=label,
    )


def _changelog_section(version: str, date: str, *, summary_lines: Sequence[str]) -> str:
    normalized = _with_pending_doi_line(version, _normalize_changelog_summary_lines(summary_lines))
    body = "\n".join(f"- {line}" for line in normalized)
    return f"## v{version} - {date}\n\n{body}\n"


def _normalize_changelog_summary_lines(summary_lines: Sequence[str]) -> tuple[str, ...]:
    normalized = tuple(line.strip().removeprefix("-").strip() for line in summary_lines if line.strip())
    if not normalized:
        raise ValueError("Release changelog summary_lines are required; refusing to reuse an old release body")
    removed_route_refs = [line for line in normalized if "./ns" in line or "ns release-prep" in line]
    if removed_route_refs:
        raise ValueError("Release changelog summary_lines must not reference removed ./ns release routes")
    return normalized


def _with_pending_doi_line(version: str, summary_lines: Sequence[str]) -> tuple[str, ...]:
    if any("Zenodo DOI verification pending" in line for line in summary_lines):
        return tuple(summary_lines)
    return (f"Zenodo DOI verification pending for v{version}.", *summary_lines)


def _update_changelog(text: str, version: str, date: str, *, summary_lines: Sequence[str]) -> str:
    existing = re.compile(
        rf"^##\s+v{re.escape(version)}\s+-\s+\d{{4}}-\d{{2}}-\d{{2}}.*?(?=^##\s+v|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    section = _changelog_section(version, date, summary_lines=summary_lines)
    if existing.search(text):
        return existing.sub(section.rstrip() + "\n\n", text, count=1)

    first_release = re.search(r"^##\s+v\d+\.\d+\.\d+", text, flags=re.MULTILINE)
    if not first_release:
        raise ValueError("CHANGELOG.md has no versioned release section anchor")
    index = first_release.start()
    return text[:index] + section + "\n" + text[index:]


def _release_prep_source_fingerprint(*, version: str, date: str, summary_lines: Sequence[str]) -> str:
    payload = {
        "schema_version": 1,
        "kind": "release_prep_current_handoff_inputs",
        "version": version,
        "date": date,
        "summary_lines": list(summary_lines),
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _dpa_current_handoff_lifecycle_enabled(root: Path) -> bool:
    workspace = load_workspace(root)
    return (root / DEFAULT_READINESS_PATH).exists() or workspace.dpa_current_handoff_acceptance_state_path().exists()


def refresh_dpa_readiness_command_manifest_ack(
    project_root: Path | str = ".",
    *,
    dry_run: bool = False,
) -> dict[str, object]:
    """Keep the DPA readiness ACK aligned with the synchronized command manifest."""
    root = Path(project_root).resolve()
    path = root / DEFAULT_READINESS_PATH
    relative = DPA_READINESS_ACK_RELATIVE_PATH
    if not path.exists():
        return {
            "ok": True,
            "status": "SKIPPED",
            "reason": "readiness-record-missing",
            "path": relative,
            "changed": False,
            "changed_paths": [],
            "dry_run": dry_run,
        }

    data = json.loads(path.read_text(encoding="utf-8"))
    expected_ack = command_manifest_ack_line(load_manifest(root))
    old_ack = data.get("command_manifest_ack")
    if old_ack == expected_ack:
        return {
            "ok": True,
            "status": "CURRENT",
            "path": relative,
            "changed": False,
            "changed_paths": [],
            "command_manifest_ack": expected_ack,
            "dry_run": dry_run,
        }

    data["command_manifest_ack"] = expected_ack
    if not dry_run:
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return {
        "ok": True,
        "status": "UPDATED",
        "path": relative,
        "changed": True,
        "changed_paths": [relative],
        "old_command_manifest_ack": old_ack,
        "command_manifest_ack": expected_ack,
        "dry_run": dry_run,
    }


def _evaluate_release_prep_current_handoff_lifecycle(
    root: Path,
    *,
    target_path: Path,
    projected_text: str,
    version: str,
    date: str,
    summary_lines: Sequence[str],
    execute: bool,
):
    return evaluate_current_handoff_text_lifecycle(
        root,
        target_path=target_path,
        projected_text=projected_text,
        source_path=DPA_RELEASE_PREP_SOURCE_PATH,
        source_fingerprint=_release_prep_source_fingerprint(
            version=version,
            date=date,
            summary_lines=summary_lines,
        ),
        writer_id=DPA_RELEASE_PREP_WRITER_ID,
        renderer_id=DPA_RELEASE_PREP_RENDERER_ID,
        renderer_semantic_version=DPA_RELEASE_PREP_RENDERER_SEMANTIC_VERSION,
        contract_id=DPA_RELEASE_PREP_CONTRACT_ID,
        target_scope=DPA_RELEASE_PREP_TARGET_SCOPE,
        execute=execute,
        initialize_acceptance=False,
        require_dp2_authorized=(root / DEFAULT_READINESS_PATH).exists(),
        lock_command="agentic-kit release-prep current-handoff",
    )


def _require_dpa_current_handoff_preflight(
    root: Path,
    *,
    target_path: Path,
    projected_text: str,
    version: str,
    date: str,
    summary_lines: Sequence[str],
) -> None:
    if not _dpa_current_handoff_lifecycle_enabled(root):
        return
    result = _evaluate_release_prep_current_handoff_lifecycle(
        root,
        target_path=target_path,
        projected_text=projected_text,
        version=version,
        date=date,
        summary_lines=summary_lines,
        execute=False,
    )
    if result.ok:
        return
    details = "; ".join(f"{finding.code}: {finding.message}" for finding in result.findings)
    raise ValueError(f"DPA CURRENT_HANDOFF lifecycle blocked release-prep preflight: {details}")


def _write_current_handoff_if_changed(
    path: Path,
    text: str,
    *,
    dry_run: bool,
    changed: list[str],
    root: Path,
    version: str,
    date: str,
    summary_lines: Sequence[str],
) -> None:
    old = _read(path)
    if old == text:
        return
    changed.append(path.relative_to(root).as_posix())
    if dry_run:
        return
    if not _dpa_current_handoff_lifecycle_enabled(root):
        path.write_text(text, encoding="utf-8")
        return
    result = _evaluate_release_prep_current_handoff_lifecycle(
        root,
        target_path=path,
        projected_text=text,
        version=version,
        date=date,
        summary_lines=summary_lines,
        execute=True,
    )
    if result.ok:
        return
    details = "; ".join(f"{finding.code}: {finding.message}" for finding in result.findings)
    raise ValueError(f"DPA CURRENT_HANDOFF lifecycle blocked release-prep write: {details}")


def prepare_release_state(
    project_root: Path | str = ".",
    *,
    version: str,
    date: str,
    summary_lines: Sequence[str],
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
    normalized_summary_lines = _normalize_changelog_summary_lines(summary_lines)
    handoff_path = root / CURRENT_HANDOFF_RELATIVE_PATH

    updates = {
        root / "pyproject.toml": _update_pyproject(_read(root / "pyproject.toml"), version),
        root / "src" / "agentic_project_kit" / "__init__.py": _update_package_init(
            _read(root / "src" / "agentic_project_kit" / "__init__.py"),
            version,
        ),
        root / "README.md": _update_readme(_read(root / "README.md"), version),
        root / "CITATION.cff": _update_citation(_read(root / "CITATION.cff"), version, date),
        root / "docs" / "STATUS.md": _update_current_version_doc(
            _read(root / "docs" / "STATUS.md"),
            version,
            label="docs/STATUS.md current version",
        ),
        handoff_path: _update_current_version_doc(
            _read(handoff_path),
            version,
            label="docs/handoff/CURRENT_HANDOFF.md current version",
        ),
        root / "CHANGELOG.md": _update_changelog(
            _read(root / "CHANGELOG.md"),
            version,
            date,
            summary_lines=normalized_summary_lines,
        ),
    }

    if _read(handoff_path) != updates[handoff_path]:
        _require_dpa_current_handoff_preflight(
            root,
            target_path=handoff_path,
            projected_text=updates[handoff_path],
            version=version,
            date=date,
            summary_lines=normalized_summary_lines,
        )

    _write_current_handoff_if_changed(
        handoff_path,
        updates[handoff_path],
        dry_run=dry_run,
        changed=changed,
        root=root,
        version=version,
        date=date,
        summary_lines=normalized_summary_lines,
    )
    for path, text in updates.items():
        if path == handoff_path:
            continue
        _write_if_changed(path, text, dry_run=dry_run, changed=changed, root=root)

    return ReleasePrepareResult(version=version, date=date, changed_paths=sorted(changed), dry_run=dry_run)
