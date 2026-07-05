from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Literal

import yaml

from agentic_project_kit.workspace import KitConfig, load_workspace

_DEFAULT_CONFIG = KitConfig()
PROJECT_DIRECTION_PATH = Path(_DEFAULT_CONFIG.planning_root) / _DEFAULT_CONFIG.project_direction_file
VALID_SECTIONS = ("all", "strategy", "roadmap", "plans", "ideas", "done", "discarded")
VALID_FORMATS = ("text", "markdown", "json")
ALLOWED_TOP_LEVEL_KEYS = frozenset(
    {"schema_version", "meta", "strategy", "roadmap", "plans", "ideas", "done", "discarded"}
)
SECTION_STATUS_VALUES = {
    "strategy": frozenset({"active", "superseded", "done", "discarded"}),
    "roadmap": frozenset({"next", "planned", "blocked", "done", "discarded"}),
    "plans": frozenset({"active", "planned", "blocked", "done", "discarded"}),
    "ideas": frozenset({"candidate", "accepted", "rejected", "superseded"}),
}
ACTIVE_STATUSES = frozenset({"active", "next", "planned", "blocked", "candidate", "accepted"})
PLANNING_SCAN_ROOTS = (
    Path("docs/strategy"),
    Path("docs/planning"),
    Path("docs/plans"),
    Path("docs/ideas"),
    Path("docs/roadmap"),
)
CANONICAL_DIRECTION_FILES = {
    "docs/planning/PROJECT_DIRECTION.yaml",
    "docs/planning/PROJECT_DIRECTION.md",
}


@dataclass(frozen=True)
class ProjectDirection:
    data: dict[str, Any]
    path: Path
    authority_path: str = PROJECT_DIRECTION_PATH.as_posix()

    def validate(self) -> list[str]:
        result = validate_project_direction_data(
            self.data,
            root=self.path.parent.parent.parent,
            authority_path=self.authority_path,
        )
        return [finding.message for finding in result.findings]


@dataclass(frozen=True)
class DirectionFinding:
    code: str
    message: str
    path: str = "docs/planning/PROJECT_DIRECTION.yaml"

    def as_dict(self) -> dict[str, str]:
        return {"code": self.code, "message": self.message, "path": self.path}


@dataclass(frozen=True)
class DirectionValidationResult:
    path: str
    findings: tuple[DirectionFinding, ...]

    @property
    def ok(self) -> bool:
        return not self.findings

    @property
    def status(self) -> str:
        return "PASS" if self.ok else "FAIL"

    @property
    def returncode(self) -> int:
        return 0 if self.ok else 1

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "kind": "project_direction_validation",
            "status": self.status,
            "path": self.path,
            "finding_count": len(self.findings),
            "findings": [finding.as_dict() for finding in self.findings],
        }


@dataclass(frozen=True)
class DirectionDriftRecord:
    path: str
    classification: str
    recommendation: str
    in_source_files: bool
    reference_count: int

    def as_dict(self) -> dict[str, object]:
        return {
            "path": self.path,
            "classification": self.classification,
            "recommendation": self.recommendation,
            "in_source_files": self.in_source_files,
            "reference_count": self.reference_count,
        }


@dataclass(frozen=True)
class DirectionDriftAuditResult:
    root: str
    records: tuple[DirectionDriftRecord, ...]
    missing_source_files: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return True

    @property
    def status(self) -> str:
        return "PASS"

    @property
    def returncode(self) -> int:
        return 0

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "kind": "project_direction_drift_audit",
            "root": self.root,
            "status": self.status,
            "record_count": len(self.records),
            "missing_source_file_count": len(self.missing_source_files),
            "missing_source_files": list(self.missing_source_files),
            "records": [record.as_dict() for record in self.records],
        }


def load_project_direction(root: Path | str = ".") -> ProjectDirection:
    base = Path(root)
    path = load_workspace(base).project_direction_path()
    raw = path.read_text(encoding="utf-8")
    data = yaml.safe_load(raw)
    if not isinstance(data, dict):
        raise ValueError(f"{PROJECT_DIRECTION_PATH.as_posix()} must contain a YAML mapping")
    try:
        authority_path = path.relative_to(base).as_posix()
    except ValueError:
        authority_path = PROJECT_DIRECTION_PATH.as_posix()
    return ProjectDirection(data=data, path=path, authority_path=authority_path)


def validate_project_direction(
    root: Path | str = ".",
    *,
    strict_planning_files: bool = False,
) -> DirectionValidationResult:
    direction = load_project_direction(root)
    return validate_project_direction_data(
        direction.data,
        root=Path(root),
        authority_path=direction.authority_path,
        strict_planning_files=strict_planning_files,
    )


def validate_project_direction_data(
    data: dict[str, Any],
    *,
    root: Path,
    authority_path: str = PROJECT_DIRECTION_PATH.as_posix(),
    strict_planning_files: bool = False,
) -> DirectionValidationResult:
    findings: list[DirectionFinding] = []
    root = Path(root)

    for key in data:
        if key not in ALLOWED_TOP_LEVEL_KEYS:
            findings.append(DirectionFinding("unknown-top-level-key", f"unknown top-level key: {key}"))
    for key in ALLOWED_TOP_LEVEL_KEYS:
        if key not in data:
            findings.append(DirectionFinding("missing-required-key", f"missing required key: {key}"))
    if data.get("schema_version") != 1:
        findings.append(DirectionFinding("invalid-schema-version", "schema_version must be 1"))

    meta = data.get("meta")
    if not isinstance(meta, dict):
        findings.append(DirectionFinding("invalid-meta", "meta must be a mapping"))
    else:
        if meta.get("status") != "active":
            findings.append(DirectionFinding("invalid-meta-status", "meta.status must be active"))
        if meta.get("authority") != authority_path:
            findings.append(
                DirectionFinding("invalid-authority", f"meta.authority must be {authority_path}")
            )

    ids_by_section: dict[str, str] = {}
    dependency_checks: list[tuple[str, str]] = []
    source_files = _collect_source_file_entries(data)
    _validate_no_private_absolute_paths(data, findings)

    for section in ("strategy", "roadmap", "plans", "ideas", "done", "discarded"):
        raw_items = data.get(section)
        if not isinstance(raw_items, list):
            findings.append(DirectionFinding("invalid-section", f"{section} must be a list"))
            continue
        for index, item in enumerate(raw_items):
            path = f"{section}[{index}]"
            if not isinstance(item, dict):
                findings.append(DirectionFinding("invalid-item", f"{path} must be a mapping"))
                continue
            item_id = str(item.get("id") or "").strip()
            if not item_id:
                findings.append(DirectionFinding("missing-id", f"{path}.id must not be empty"))
            elif item_id in ids_by_section:
                findings.append(
                    DirectionFinding(
                        "duplicate-id",
                        f"id {item_id!r} appears in both {ids_by_section[item_id]} and {path}",
                    )
                )
            else:
                ids_by_section[item_id] = path
            if section in SECTION_STATUS_VALUES:
                status = str(item.get("status") or "").strip()
                allowed = SECTION_STATUS_VALUES[section]
                if status not in allowed:
                    findings.append(
                        DirectionFinding(
                            "invalid-status",
                            f"{path}.status must be one of {', '.join(sorted(allowed))}",
                        )
                    )
                if status in ACTIVE_STATUSES and not str(item.get("title") or "").strip():
                    findings.append(DirectionFinding("empty-active-title", f"{path}.title must not be empty"))
            if section in {"roadmap", "plans"}:
                for dependency in _string_list(item.get("depends_on"), f"{path}.depends_on", findings):
                    dependency_checks.append((path, dependency))
            if section == "done":
                if item.get("completed_by_pr") is None and not str(item.get("completion_exception") or "").strip():
                    findings.append(
                        DirectionFinding(
                            "done-missing-completion",
                            f"{path} needs completed_by_pr or completion_exception",
                        )
                    )
            if section == "discarded" and not str(item.get("reason") or "").strip():
                findings.append(DirectionFinding("discarded-missing-reason", f"{path}.reason must not be empty"))
            _validate_item_sources(item, path, root, findings)
            _validate_item_evidence(item, path, root, findings)

    for path, dependency in dependency_checks:
        if dependency not in ids_by_section:
            findings.append(
                DirectionFinding("unknown-dependency", f"{path}.depends_on references unknown id {dependency!r}")
            )

    if strict_planning_files:
        referenced = {entry for entry in source_files if isinstance(entry, str)}
        for candidate in _iter_planning_files(root):
            if candidate in CANONICAL_DIRECTION_FILES:
                continue
            if candidate.startswith("docs/planning/") and candidate not in referenced:
                findings.append(
                    DirectionFinding(
                        "forbidden-free-planning-file",
                        f"{candidate} is not a canonical direction file or referenced source",
                    )
                )

    return DirectionValidationResult(path=authority_path, findings=tuple(findings))


def render_project_direction(
    direction: ProjectDirection,
    *,
    section: Literal["all", "strategy", "roadmap", "plans", "ideas", "done", "discarded"] = "all",
    output_format: Literal["text", "markdown", "json"] = "text",
) -> str:
    findings = direction.validate()
    if findings:
        raise ValueError("; ".join(findings))

    if output_format == "json":
        if section == "all":
            payload: Any = direction.data
        else:
            payload = {section: direction.data[section]}
        return json.dumps(payload, default=str, indent=2, sort_keys=True) + "\n"

    if output_format == "markdown":
        return _render_markdown(direction.data, section)

    return _render_text(direction.data, section)


def audit_project_direction_drift(root: Path | str = ".") -> DirectionDriftAuditResult:
    root_path = Path(root)
    direction = load_project_direction(root_path)
    source_files = {
        entry
        for entry in _collect_source_file_entries(direction.data)
        if isinstance(entry, str) and entry not in CANONICAL_DIRECTION_FILES
    }
    existing_sources = {entry for entry in source_files if (root_path / entry).exists()}
    missing_sources = tuple(sorted(entry for entry in source_files if not (root_path / entry).exists()))

    records: list[DirectionDriftRecord] = []
    reference_counts = _reference_counts(root_path, set(_iter_planning_files(root_path)) | source_files)
    for relative in _iter_planning_files(root_path):
        if relative in CANONICAL_DIRECTION_FILES:
            classification = "canonical_direction"
            recommendation = "keep"
        elif relative in existing_sources:
            classification = "listed_source"
            recommendation = "migrate_or_retain_until_slice_cleanup"
        elif reference_counts.get(relative, 0):
            classification = "unlisted_referenced_file"
            recommendation = "migrate_or_reference_clean_before_delete"
        else:
            classification = "unlisted_unreferenced_file"
            recommendation = "safe_delete_candidate_after_review"
        records.append(
            DirectionDriftRecord(
                path=relative,
                classification=classification,
                recommendation=recommendation,
                in_source_files=relative in source_files,
                reference_count=reference_counts.get(relative, 0),
            )
        )
    return DirectionDriftAuditResult(
        root=root_path.resolve().as_posix(),
        records=tuple(sorted(records, key=lambda record: record.path)),
        missing_source_files=missing_sources,
    )


def render_direction_validation(result: DirectionValidationResult) -> str:
    lines = [
        "PROJECT_DIRECTION_VALIDATE",
        f"STATUS={result.status}",
        f"FINDING_COUNT={len(result.findings)}",
    ]
    for finding in result.findings:
        lines.append(f"FINDING={finding.code}|{finding.path}|{finding.message}")
    return "\n".join(lines) + "\n"


def render_direction_drift_audit(result: DirectionDriftAuditResult) -> str:
    lines = [
        "PROJECT_DIRECTION_DRIFT_AUDIT",
        f"STATUS={result.status}",
        f"RECORD_COUNT={len(result.records)}",
        f"MISSING_SOURCE_FILE_COUNT={len(result.missing_source_files)}",
    ]
    for missing in result.missing_source_files:
        lines.append(f"MISSING_SOURCE={missing}")
    for record in result.records:
        lines.append(
            "RECORD="
            f"{record.classification}|{record.recommendation}|{record.path}|"
            f"source={record.in_source_files}|refs={record.reference_count}"
        )
    return "\n".join(lines) + "\n"


def _render_text(data: dict[str, Any], section: str) -> str:
    meta = data.get("meta", {})
    lines: list[str] = [
        "PROJECT DIRECTION",
        f"Status: {meta.get('status')}",
        f"Updated after PR: {meta.get('updated_after_pr')}",
        f"Authority: {meta.get('authority')}",
        "",
    ]
    if section in {"all", "strategy"}:
        _append_strategy_text(lines, data["strategy"])
    if section in {"all", "roadmap"}:
        _append_roadmap_text(lines, data["roadmap"])
    if section in {"all", "plans"}:
        _append_items_text(lines, "Plans", data["plans"])
    if section in {"all", "ideas"}:
        _append_items_text(lines, "Ideas", data["ideas"])
    if section in {"all", "done"}:
        _append_items_text(lines, "Done", data["done"])
    if section in {"all", "discarded"}:
        _append_items_text(lines, "Discarded", data["discarded"])
    return "\n".join(lines).rstrip() + "\n"


def _render_markdown(data: dict[str, Any], section: str) -> str:
    meta = data.get("meta", {})
    lines: list[str] = [
        "# Project Direction",
        "",
        f"- Status: `{meta.get('status')}`",
        f"- Updated after PR: `{meta.get('updated_after_pr')}`",
        f"- Authority: `{meta.get('authority')}`",
        "",
    ]
    if section in {"all", "strategy"}:
        _append_strategy_markdown(lines, data["strategy"])
    if section in {"all", "roadmap"}:
        _append_roadmap_markdown(lines, data["roadmap"])
    if section in {"all", "plans"}:
        _append_items_markdown(lines, "Plans", data["plans"])
    if section in {"all", "ideas"}:
        _append_items_markdown(lines, "Ideas", data["ideas"])
    if section in {"all", "done"}:
        _append_items_markdown(lines, "Done", data["done"])
    if section in {"all", "discarded"}:
        _append_items_markdown(lines, "Discarded", data["discarded"])
    return "\n".join(lines).rstrip() + "\n"


def _append_strategy_text(lines: list[str], strategy: list[dict[str, Any]]) -> None:
    lines.append("Strategy")
    for item in strategy:
        lines.append(f"- {item.get('id')}: {item.get('title')} [{item.get('status')}]")
        rationale = item.get("rationale")
        if rationale:
            lines.append(f"  {rationale}")
    lines.append("")


def _append_roadmap_text(lines: list[str], roadmap: list[dict[str, Any]]) -> None:
    lines.append("Roadmap")
    for item in roadmap:
        lines.append(
            f"- {item.get('id')}: {item.get('title')} "
            f"[{item.get('phase')}/{item.get('status')}]"
        )
    lines.append("")


def _append_items_text(lines: list[str], title: str, items: list[dict[str, Any]]) -> None:
    lines.append(title)
    for item in items:
        detail = item.get("rationale") or item.get("reason") or item.get("title") or ""
        lines.append(f"- {item.get('id')}: {item.get('title')} [{item.get('status', item.get('completed_by_pr'))}]")
        if detail and detail != item.get("title"):
            lines.append(f"  {detail}")
    lines.append("")


def _append_strategy_markdown(lines: list[str], strategy: list[dict[str, Any]]) -> None:
    lines.append("## Strategy")
    lines.append("")
    for item in strategy:
        lines.append(f"- `{item.get('id')}` - **{item.get('title')}** (`{item.get('status')}`)")
        if item.get("rationale"):
            lines.append(f"  {item.get('rationale')}")
    lines.append("")


def _append_roadmap_markdown(lines: list[str], roadmap: list[dict[str, Any]]) -> None:
    lines.append("## Roadmap")
    lines.append("")
    for item in roadmap:
        lines.append(
            f"- `{item.get('id')}` - **{item.get('title')}** "
            f"(`{item.get('phase')}`, `{item.get('status')}`)"
        )
    lines.append("")


def _append_items_markdown(lines: list[str], title: str, items: list[dict[str, Any]]) -> None:
    lines.append(f"## {title}")
    lines.append("")
    for item in items:
        status = item.get("status", item.get("completed_by_pr"))
        detail = item.get("rationale") or item.get("reason") or ""
        lines.append(f"- `{item.get('id')}` - **{item.get('title')}** (`{status}`)")
        if detail:
            lines.append(f"  {detail}")
    lines.append("")


def _string_list(value: object, path: str, findings: list[DirectionFinding]) -> list[str]:
    if value in (None, []):
        return []
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        findings.append(DirectionFinding("invalid-string-list", f"{path} must be a list of strings"))
        return []
    return [item for item in value if item]


def _collect_source_file_entries(data: object) -> list[object]:
    entries: list[object] = []
    if isinstance(data, dict):
        source_files = data.get("source_files")
        if isinstance(source_files, list):
            entries.extend(source_files)
        for value in data.values():
            entries.extend(_collect_source_file_entries(value))
    elif isinstance(data, list):
        for item in data:
            entries.extend(_collect_source_file_entries(item))
    return entries


def _validate_item_sources(
    item: dict[str, Any],
    path: str,
    root: Path,
    findings: list[DirectionFinding],
) -> None:
    source_files = item.get("source_files")
    if not isinstance(source_files, list) or not source_files:
        findings.append(DirectionFinding("missing-source-files", f"{path}.source_files must not be empty"))
        return
    for index, source in enumerate(source_files):
        source_path = f"{path}.source_files[{index}]"
        if isinstance(source, str):
            if _is_private_absolute_path(source):
                findings.append(DirectionFinding("private-absolute-path", f"{source_path} is private/absolute"))
            elif not (root / source).exists():
                findings.append(DirectionFinding("missing-source-file", f"{source_path} does not exist: {source}"))
            continue
        if isinstance(source, dict) and source.get("deleted_source") is True:
            deleted_path = source.get("path")
            if not isinstance(deleted_path, str) or not deleted_path.strip():
                findings.append(DirectionFinding("invalid-deleted-source", f"{source_path}.path must be set"))
            continue
        findings.append(
            DirectionFinding(
                "invalid-source-file",
                f"{source_path} must be a repo path or a deleted_source mapping",
            )
        )


def _validate_item_evidence(
    item: dict[str, Any],
    path: str,
    root: Path,
    findings: list[DirectionFinding],
) -> None:
    evidence = item.get("evidence")
    if evidence in (None, []):
        return
    if not isinstance(evidence, list):
        findings.append(DirectionFinding("invalid-evidence", f"{path}.evidence must be a list"))
        return
    for index, entry in enumerate(evidence):
        if not isinstance(entry, str):
            findings.append(DirectionFinding("invalid-evidence", f"{path}.evidence[{index}] must be a string"))
            continue
        if _looks_like_repo_file(entry) and not (root / entry).exists():
            findings.append(DirectionFinding("missing-evidence-file", f"{path}.evidence[{index}] missing: {entry}"))


def _validate_no_private_absolute_paths(data: object, findings: list[DirectionFinding]) -> None:
    if isinstance(data, dict):
        for value in data.values():
            _validate_no_private_absolute_paths(value, findings)
    elif isinstance(data, list):
        for item in data:
            _validate_no_private_absolute_paths(item, findings)
    elif isinstance(data, str) and _is_private_absolute_path(data):
        findings.append(DirectionFinding("private-absolute-path", f"private absolute path is not allowed: {data}"))


def _is_private_absolute_path(value: str) -> bool:
    return value.startswith(("/Users/", "/home/", "/private/", "C:\\", "D:\\"))


def _looks_like_repo_file(value: str) -> bool:
    return value.startswith((".agentic/", "docs/", "src/", "tests/", "artifacts/"))


def _iter_planning_files(root: Path) -> list[str]:
    files: list[str] = []
    for base in PLANNING_SCAN_ROOTS:
        absolute = root / base
        if not absolute.exists():
            continue
        files.extend(
            path.relative_to(root).as_posix()
            for path in absolute.rglob("*")
            if path.is_file() and path.suffix in {".md", ".yaml", ".yml"}
        )
    return sorted(files)


def _reference_counts(root: Path, targets: set[str]) -> dict[str, int]:
    counts = {target: 0 for target in targets}
    ignored_parts = {".git", ".venv", "node_modules", "__pycache__"}
    for path in root.rglob("*"):
        if not path.is_file() or ignored_parts & set(path.parts):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        except OSError:
            continue
        relative = path.relative_to(root).as_posix()
        for target in targets:
            if target != relative and target in text:
                counts[target] += 1
    return counts
