from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


CATALOG_PATH = Path(".agentic/patterns/catalog.yaml")
VALID_KINDS = {"pattern", "anti-pattern"}


class PatternCatalogError(ValueError):
    """Raised when the local pattern catalog is missing or invalid."""


@dataclass(frozen=True)
class PatternEntry:
    id: str
    title: str
    kind: str
    summary: str
    doc: Path


@dataclass(frozen=True)
class PatternCatalog:
    version: int
    patterns: list[PatternEntry]


@dataclass(frozen=True)
class PatternDetail:
    entry: PatternEntry
    markdown: str


def load_pattern_catalog(root: Path) -> PatternCatalog:
    catalog_path = root / CATALOG_PATH
    if not catalog_path.exists():
        raise PatternCatalogError(f"missing pattern catalog: {CATALOG_PATH}")

    data = yaml.safe_load(catalog_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise PatternCatalogError("pattern catalog must be a mapping")

    version = data.get("version")
    if version != 1:
        raise PatternCatalogError(f"unsupported pattern catalog version: {version}")

    raw_patterns = data.get("patterns")
    if not isinstance(raw_patterns, list):
        raise PatternCatalogError("pattern catalog must contain a patterns list")

    seen: set[str] = set()
    entries: list[PatternEntry] = []
    for raw in raw_patterns:
        if not isinstance(raw, dict):
            raise PatternCatalogError("pattern entry must be a mapping")
        entry_id = _required_string(raw, "id")
        if entry_id in seen:
            raise PatternCatalogError(f"duplicate pattern id: {entry_id}")
        seen.add(entry_id)
        kind = _required_string(raw, "kind")
        if kind not in VALID_KINDS:
            raise PatternCatalogError(f"invalid pattern kind: {kind}")
        entries.append(
            PatternEntry(
                id=entry_id,
                title=_required_string(raw, "title"),
                kind=kind,
                summary=_required_string(raw, "summary"),
                doc=Path(_required_string(raw, "doc")),
            )
        )

    return PatternCatalog(version=version, patterns=entries)


def load_pattern_detail(root: Path, entry: PatternEntry) -> PatternDetail:
    doc_path = root / entry.doc
    if not doc_path.exists():
        raise PatternCatalogError(f"missing pattern document: {entry.doc}")
    return PatternDetail(entry=entry, markdown=doc_path.read_text(encoding="utf-8"))


def find_pattern(catalog: PatternCatalog, pattern_id: str) -> PatternEntry:
    for entry in catalog.patterns:
        if entry.id == pattern_id:
            return entry
    raise PatternCatalogError(f"unknown pattern id: {pattern_id}")


def _required_string(raw: dict[str, Any], key: str) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value.strip():
        raise PatternCatalogError(f"missing or invalid pattern field: {key}")
    return value
