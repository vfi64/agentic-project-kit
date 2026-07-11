from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import json
from pathlib import Path
import re
import subprocess
from typing import Any

import yaml

from agentic_project_kit.documentation_registry import (
    REGISTRY_PATH,
    load_documentation_registry,
    load_documentation_registry_scope,
)
from agentic_project_kit.release import read_project_version
from agentic_project_kit.state_freshness import _version_tuple

REVIEW_AFTER_RE = re.compile(r"^(date|release|direction):(.+)$")
RELEASE_REVIEW_RE = re.compile(r"^(<=|>=|==|<|>)(v?\d+\.\d+\.\d+)$")
TARGET_VERSION_RE = re.compile(r"\b(?:Target|target|for|For)\s+v?(\d+\.\d+\.\d+)\b")
REFERENCE_SCAN_SUFFIXES = {".md", ".py", ".yaml", ".yml"}
ORPHAN_EXEMPT_PREFIXES = ("docs/archive/", "docs/reports/", "docs/examples/")
ROOT_CANONICAL_FILES = ("README.md", "CHANGELOG.md", "CITATION.cff", "SECURITY.md")
PROJECT_DIRECTION_PAIR = (
    "docs/planning/PROJECT_DIRECTION.yaml",
    "docs/planning/PROJECT_DIRECTION.md",
)
REFERENCE_SCAN_EXCLUDED_PARTS = {".git", ".venv", "node_modules", "__pycache__"}


@dataclass(frozen=True)
class LifecycleSignal:
    code: str
    path: str
    message: str
    severity: str = "WARN"
    document_class: str | None = None

    def to_finding_kwargs(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "path": self.path,
            "message": self.message,
            "severity": self.severity,
            "document_class": self.document_class,
        }


@dataclass(frozen=True)
class DocOrphanCandidate:
    path: str
    document_class: str | None
    last_commit_date: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "class": self.document_class,
            "last_commit_date": self.last_commit_date,
        }


@dataclass(frozen=True)
class DocOrphanReport:
    candidates: tuple[DocOrphanCandidate, ...]

    @property
    def ok(self) -> bool:
        return True

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "kind": "doc_orphan_audit",
            "ok": True,
            "candidate_count": len(self.candidates),
            "candidates": [candidate.to_dict() for candidate in self.candidates],
        }


@dataclass(frozen=True)
class ReviewAfterSuggestion:
    path: str
    review_after: str
    matched_text: str

    def to_dict(self) -> dict[str, str]:
        return {
            "path": self.path,
            "review_after": self.review_after,
            "matched_text": self.matched_text,
        }


def build_review_after_findings(
    *,
    path: str,
    review_after: Any,
    now: date,
    current_version: str | None,
    direction_statuses: dict[str, str],
    document_class: str | None,
) -> tuple[LifecycleSignal, ...]:
    if review_after is None:
        return ()
    if not isinstance(review_after, str) or not review_after.strip():
        return (
            LifecycleSignal(
                "REVIEW_AFTER_INVALID",
                path,
                "review_after must be a non-empty string",
                document_class=document_class,
            ),
        )

    value = review_after.strip()
    match = REVIEW_AFTER_RE.fullmatch(value)
    if not match:
        return (
            LifecycleSignal(
                "REVIEW_AFTER_INVALID",
                path,
                f"unsupported review_after value: {value!r}",
                document_class=document_class,
            ),
        )

    kind, payload = match.groups()
    if kind == "date":
        return _date_review_findings(path, payload, now, document_class)
    if kind == "release":
        return _release_review_findings(path, payload, current_version, document_class)
    if kind == "direction":
        return _direction_review_findings(path, payload, direction_statuses, document_class)
    return ()


def load_direction_statuses(project_root: Path) -> dict[str, str]:
    path = project_root / "docs" / "planning" / "PROJECT_DIRECTION.yaml"
    if not path.exists():
        return {}
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return {}
    if not isinstance(data, dict):
        return {}

    statuses: dict[str, str] = {}
    for section in ("strategy", "roadmap", "plans", "ideas", "done", "discarded"):
        items = data.get(section)
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            item_id = item.get("id")
            if not isinstance(item_id, str) or not item_id:
                continue
            if section in {"done", "discarded"}:
                statuses[item_id] = section
            else:
                status = item.get("status")
                if isinstance(status, str) and status:
                    statuses[item_id] = status
    return statuses


def resolve_current_version(project_root: Path, explicit_version: str | None = None) -> str | None:
    if explicit_version:
        return explicit_version
    try:
        return read_project_version(project_root)
    except (OSError, ValueError):
        return None


def build_doc_orphan_report(project_root: Path) -> DocOrphanReport:
    registry = load_documentation_registry(project_root)
    documents = registry.get("documents", [])
    if not isinstance(documents, list):
        return DocOrphanReport(candidates=())

    candidates: list[DocOrphanCandidate] = []
    reference_texts = _reference_scan_texts(project_root)
    for entry in documents:
        if not isinstance(entry, dict):
            continue
        path = entry.get("path")
        if not isinstance(path, str) or not path:
            continue
        if _is_orphan_exempt(project_root, path):
            continue
        document_path = project_root / path
        if not document_path.exists() or not document_path.is_file():
            continue
        if any(path in text for relative, text in reference_texts.items() if relative != path):
            continue
        candidates.append(
            DocOrphanCandidate(
                path=path,
                document_class=entry.get("class") if isinstance(entry.get("class"), str) else None,
                last_commit_date=_last_commit_date(project_root, path),
            )
        )
    return DocOrphanReport(candidates=tuple(sorted(candidates, key=lambda candidate: candidate.path)))


def render_doc_orphan_report(report: DocOrphanReport) -> str:
    lines = [
        "DOC_ORPHAN_AUDIT",
        "STATUS=PASS",
        f"CANDIDATE_COUNT={len(report.candidates)}",
    ]
    if not report.candidates:
        lines.append("CANDIDATE=none")
    for candidate in report.candidates:
        class_suffix = f"|class={candidate.document_class}" if candidate.document_class else ""
        date_suffix = f"|last_commit_date={candidate.last_commit_date}" if candidate.last_commit_date else ""
        lines.append(f"CANDIDATE={candidate.path}{class_suffix}{date_suffix}")
    return "\n".join(lines) + "\n"


def write_doc_orphan_json_report(report: DocOrphanReport, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def build_review_after_suggestions(project_root: Path) -> tuple[ReviewAfterSuggestion, ...]:
    registry = load_documentation_registry(project_root)
    documents = registry.get("documents", [])
    if not isinstance(documents, list):
        return ()

    suggestions: list[ReviewAfterSuggestion] = []
    for entry in documents:
        if not isinstance(entry, dict) or entry.get("review_after") is not None:
            continue
        path = entry.get("path")
        if not isinstance(path, str) or not path.endswith(".md"):
            continue
        document_path = project_root / path
        if not document_path.exists() or not document_path.is_file():
            continue
        try:
            text = document_path.read_text(encoding="utf-8")
        except OSError:
            continue
        match = TARGET_VERSION_RE.search(text)
        if match:
            suggestions.append(
                ReviewAfterSuggestion(
                    path=path,
                    review_after=f"release:>={match.group(1)}",
                    matched_text=match.group(0),
                )
            )
    return tuple(sorted(suggestions, key=lambda suggestion: suggestion.path))


def render_review_after_suggestions(suggestions: tuple[ReviewAfterSuggestion, ...]) -> str:
    lines = ["REVIEW_AFTER_SUGGESTIONS", f"COUNT={len(suggestions)}"]
    if not suggestions:
        lines.append("SUGGESTION=none")
    for suggestion in suggestions:
        lines.append(f"SUGGESTION={suggestion.path}|{suggestion.review_after}|matched={suggestion.matched_text}")
    return "\n".join(lines) + "\n"


def review_after_suggestions_to_dict(suggestions: tuple[ReviewAfterSuggestion, ...]) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "kind": "review_after_suggestions",
        "count": len(suggestions),
        "suggestions": [suggestion.to_dict() for suggestion in suggestions],
    }


def _date_review_findings(
    path: str,
    payload: str,
    now: date,
    document_class: str | None,
) -> tuple[LifecycleSignal, ...]:
    try:
        target = date.fromisoformat(payload)
    except ValueError:
        return (
            LifecycleSignal(
                "REVIEW_AFTER_INVALID",
                path,
                f"invalid review_after date: {payload!r}",
                document_class=document_class,
            ),
        )
    if now >= target:
        return (
            LifecycleSignal(
                "REVIEW_DUE_DATE",
                path,
                f"review_after date is due: {target.isoformat()}",
                document_class=document_class,
            ),
        )
    return ()


def _release_review_findings(
    path: str,
    payload: str,
    current_version: str | None,
    document_class: str | None,
) -> tuple[LifecycleSignal, ...]:
    match = RELEASE_REVIEW_RE.fullmatch(payload)
    if not match:
        return (
            LifecycleSignal(
                "REVIEW_AFTER_INVALID",
                path,
                f"invalid review_after release selector: {payload!r}",
                document_class=document_class,
            ),
        )
    if current_version is None:
        return (
            LifecycleSignal(
                "REVIEW_AFTER_INVALID",
                path,
                "review_after release selector requires a readable current project version",
                document_class=document_class,
            ),
        )

    operator, target_version = match.groups()
    if _version_due(current_version, operator, target_version):
        return (
            LifecycleSignal(
                "REVIEW_DUE_RELEASE",
                path,
                f"review_after release selector is due: current {current_version} {operator} {target_version}",
                document_class=document_class,
            ),
        )
    return ()


def _direction_review_findings(
    path: str,
    item_id: str,
    direction_statuses: dict[str, str],
    document_class: str | None,
) -> tuple[LifecycleSignal, ...]:
    item_id = item_id.strip()
    if not item_id:
        return (
            LifecycleSignal(
                "REVIEW_AFTER_INVALID",
                path,
                "review_after direction selector requires an item id",
                document_class=document_class,
            ),
        )
    status = direction_statuses.get(item_id)
    if status is None:
        return (
            LifecycleSignal(
                "REVIEW_AFTER_INVALID",
                path,
                f"review_after direction selector references unknown item: {item_id}",
                document_class=document_class,
            ),
        )
    if status in {"done", "discarded"}:
        return (
            LifecycleSignal(
                "REVIEW_DUE_DIRECTION",
                path,
                f"review_after direction selector is due: {item_id} is {status}",
                document_class=document_class,
            ),
        )
    return ()


def _version_due(current_version: str, operator: str, target_version: str) -> bool:
    current = _version_tuple(current_version.removeprefix("v"))
    target = _version_tuple(target_version.removeprefix("v"))
    if current is None or target is None:
        return False
    if operator == "<":
        return current < target
    if operator == "<=":
        return current <= target
    if operator == "==":
        return current == target
    if operator == ">=":
        return current >= target
    if operator == ">":
        return current > target
    return False


def _reference_scan_texts(project_root: Path) -> dict[str, str]:
    texts: dict[str, str] = {}
    for path in project_root.rglob("*"):
        if not path.is_file() or path.suffix not in REFERENCE_SCAN_SUFFIXES:
            continue
        if REFERENCE_SCAN_EXCLUDED_PARTS & set(path.parts):
            continue
        relative = path.relative_to(project_root).as_posix()
        if relative == REGISTRY_PATH.as_posix():
            continue
        try:
            texts[relative] = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
    return texts


def _is_orphan_exempt(project_root: Path, path: str) -> bool:
    if path in ROOT_CANONICAL_FILES or path in PROJECT_DIRECTION_PAIR:
        return True
    if any(path.startswith(prefix) for prefix in ORPHAN_EXEMPT_PREFIXES):
        return True
    scope = load_documentation_registry_scope(project_root)
    if path in scope.required_files:
        return True
    return False


def _last_commit_date(project_root: Path, path: str) -> str | None:
    result = subprocess.run(
        ["git", "log", "-1", "--format=%cI", "--", path],
        cwd=project_root,
        check=False,
        capture_output=True,
        text=True,
    )
    value = result.stdout.strip()
    return value or None
