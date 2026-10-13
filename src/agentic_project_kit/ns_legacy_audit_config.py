"""Validated, explicit evidence contexts for external legacy-reference audits."""
from __future__ import annotations

from fnmatch import fnmatchcase
from pathlib import PurePosixPath


def parse_evidence_paths(audit: object) -> tuple[str, ...]:
    if audit is None:
        return ()
    if not isinstance(audit, dict) or set(audit) - {"ns_legacy"}:
        raise ValueError("audit: expected mapping with only ns_legacy")
    legacy = audit.get("ns_legacy", {})
    if not isinstance(legacy, dict) or set(legacy) - {"evidence_paths"}:
        raise ValueError("audit.ns_legacy: expected mapping with only evidence_paths")
    paths = legacy.get("evidence_paths", [])
    if not isinstance(paths, list):
        raise ValueError("audit.ns_legacy.evidence_paths: expected list of root-relative POSIX globs")
    for path in paths:
        if (
            not isinstance(path, str)
            or not path
            or path != path.strip()
            or path.startswith("/")
            or "\\" in path
            or ":" in path
            or "\0" in path
            or any(part in {"", ".", ".."} for part in path.split("/"))
            or PurePosixPath(path).is_absolute()
        ):
            raise ValueError("audit.ns_legacy.evidence_paths: invalid root-relative POSIX glob")
    return tuple(sorted(set(paths)))


def is_declared_evidence(relative_path: str, patterns: tuple[str, ...]) -> bool:
    """Match the whole root-relative POSIX path, case-sensitively (fnmatchcase)."""
    return any(fnmatchcase(relative_path, pattern) for pattern in patterns)
