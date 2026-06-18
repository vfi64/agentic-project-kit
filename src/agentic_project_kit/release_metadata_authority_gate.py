from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
import subprocess
from typing import Iterable, Sequence


RELEASE_ANCHOR_PATHS: tuple[str, ...] = (
    "pyproject.toml",
    "src/agentic_project_kit/__init__.py",
    "CHANGELOG.md",
    "README.md",
    "CITATION.cff",
    "docs/STATUS.md",
    "docs/handoff/CURRENT_HANDOFF.md",
    "docs/releases/VERIFIED_RELEASES.md",
)

RELEASE_ANCHOR_PREFIXES: tuple[str, ...] = (
    "docs/releases/",
)

AUTHORIZED_ROUTE = "agentic-kit release-prep"


@dataclass(frozen=True)
class ReleaseMetadataAuthorityGateResult:
    ok: bool
    status: str
    version: str | None
    base_ref: str
    changed_release_anchor_paths: list[str]
    evidence_paths: list[str]
    message: str

    def as_dict(self) -> dict[str, object]:
        return {
            "ok": self.ok,
            "status": self.status,
            "version": self.version,
            "base_ref": self.base_ref,
            "changed_release_anchor_paths": self.changed_release_anchor_paths,
            "evidence_paths": self.evidence_paths,
            "message": self.message,
        }


def normalize_version(version: str | None) -> str | None:
    if version is None:
        return None
    plain = version.removeprefix("v")
    if not re.fullmatch(r"\d+\.\d+\.\d+", plain):
        raise ValueError(f"Invalid release version: {version!r}; expected MAJOR.MINOR.PATCH")
    return plain


def is_release_anchor_path(path: str) -> bool:
    normalized = path.strip().replace("\\", "/")
    return normalized in RELEASE_ANCHOR_PATHS or any(
        normalized.startswith(prefix) for prefix in RELEASE_ANCHOR_PREFIXES
    )


def release_anchor_changes(paths: Iterable[str]) -> list[str]:
    return sorted({path for path in paths if is_release_anchor_path(path)})


def changed_paths_from_git(project_root: Path, base_ref: str) -> list[str]:
    completed = subprocess.run(
        ["git", "diff", "--name-only", f"{base_ref}...HEAD"],
        cwd=project_root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stdout.strip() or f"git diff failed for {base_ref}...HEAD")
    return [line.strip() for line in completed.stdout.splitlines() if line.strip()]


def _evidence_text_mentions_authorized_route(text: str) -> bool:
    lowered = text.lower()
    return "release-prep" in lowered and (
        AUTHORIZED_ROUTE in lowered
        or '"release-prep"' in lowered
        or "'release-prep'" in lowered
        or "release metadata" in lowered
    )


def _evidence_text_mentions_version(text: str, version: str | None) -> bool:
    if version is None:
        return True
    return version in text or f"v{version}" in text


def _json_evidence_mentions_changed_paths(data: object, changed_anchor_paths: Sequence[str]) -> bool:
    text = json.dumps(data, sort_keys=True)
    return all(path in text for path in changed_anchor_paths)


def _text_evidence_mentions_changed_paths(text: str, changed_anchor_paths: Sequence[str]) -> bool:
    return all(path in text for path in changed_anchor_paths)


def evidence_is_authoritative(
    evidence_path: Path,
    *,
    version: str | None,
    changed_anchor_paths: Sequence[str],
) -> bool:
    if not evidence_path.exists() or not evidence_path.is_file():
        return False
    text = evidence_path.read_text(encoding="utf-8", errors="replace")
    if not _evidence_text_mentions_authorized_route(text):
        return False
    if not _evidence_text_mentions_version(text, version):
        return False

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return _text_evidence_mentions_changed_paths(text, changed_anchor_paths)
    return _json_evidence_mentions_changed_paths(data, changed_anchor_paths)


def find_default_evidence_paths(project_root: Path) -> list[Path]:
    candidates: list[Path] = []
    for pattern in (
        "tmp/*release-prep*.json",
        "tmp/*release-prep*.log",
        "docs/reports/**/*.json",
        "docs/reports/**/*.log",
        "docs/reports/**/*.md",
    ):
        candidates.extend(project_root.glob(pattern))
    return sorted({path for path in candidates if path.is_file()})


def evaluate_release_metadata_authority_gate(
    project_root: Path | str = ".",
    *,
    base_ref: str = "origin/main",
    version: str | None = None,
    evidence_paths: Sequence[Path | str] = (),
    changed_paths: Sequence[str] | None = None,
) -> ReleaseMetadataAuthorityGateResult:
    root = Path(project_root).resolve()
    normalized_version = normalize_version(version)

    changed = list(changed_paths) if changed_paths is not None else changed_paths_from_git(root, base_ref)
    changed_anchor_paths = release_anchor_changes(changed)
    if not changed_anchor_paths:
        return ReleaseMetadataAuthorityGateResult(
            ok=True,
            status="PASS",
            version=normalized_version,
            base_ref=base_ref,
            changed_release_anchor_paths=[],
            evidence_paths=[],
            message="No release metadata anchor files changed.",
        )

    explicit_evidence = [Path(path) for path in evidence_paths]
    candidates = explicit_evidence if explicit_evidence else find_default_evidence_paths(root)

    authoritative = [
        path
        for path in candidates
        if evidence_is_authoritative(
            path if path.is_absolute() else root / path,
            version=normalized_version,
            changed_anchor_paths=changed_anchor_paths,
        )
    ]

    if authoritative:
        return ReleaseMetadataAuthorityGateResult(
            ok=True,
            status="PASS",
            version=normalized_version,
            base_ref=base_ref,
            changed_release_anchor_paths=changed_anchor_paths,
            evidence_paths=[path.as_posix() for path in authoritative],
            message="Release metadata anchor changes are backed by authoritative release-prep evidence.",
        )

    return ReleaseMetadataAuthorityGateResult(
        ok=False,
        status="BLOCK",
        version=normalized_version,
        base_ref=base_ref,
        changed_release_anchor_paths=changed_anchor_paths,
        evidence_paths=[path.as_posix() for path in candidates],
        message=(
            "Release metadata files changed without authoritative release-prepare evidence. "
            "Use `agentic-kit release-prep --version <version> --json` evidence instead of "
            "manual regex/file patching."
        ),
    )


def render_release_metadata_authority_gate_result(
    result: ReleaseMetadataAuthorityGateResult,
) -> str:
    lines = [
        "RELEASE_METADATA_AUTHORITY_GATE",
        "",
        f"STATUS: {result.status}",
        f"BASE_REF: {result.base_ref}",
        f"VERSION: {result.version or '<unspecified>'}",
        "",
        "CHANGED_RELEASE_ANCHORS:",
    ]
    if result.changed_release_anchor_paths:
        lines.extend(f"- {path}" for path in result.changed_release_anchor_paths)
    else:
        lines.append("- none")

    lines.extend(["", "EVIDENCE_PATHS:"])
    if result.evidence_paths:
        lines.extend(f"- {path}" for path in result.evidence_paths)
    else:
        lines.append("- none")

    lines.extend(["", result.message])
    return "\n".join(lines)
