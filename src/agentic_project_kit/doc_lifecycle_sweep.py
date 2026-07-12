from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import json
from pathlib import Path
import shutil
import subprocess
from typing import Any

import yaml

from agentic_project_kit.doc_lifecycle import build_doc_lifecycle_report
from agentic_project_kit.documentation_registry import load_documentation_registry
from agentic_project_kit.project_direction import audit_project_direction_drift
from agentic_project_kit.workspace import load_workspace
from agentic_project_kit.workspace_lock import workspace_mutation_lock

ARCHIVE_CLASS = "historical archive"
ARCHIVE_PREFIX = "docs/archive/"
LIFECYCLE_EXEMPT_PREFIXES = ("docs/archive/", "docs/reports/", "docs/examples/")
REFERENCE_SUFFIXES = {".md", ".py", ".yaml", ".yml"}
REFERENCE_EXCLUDED_PARTS = {".git", ".venv", "node_modules", "__pycache__"}


@dataclass(frozen=True)
class SweepCandidate:
    id: str
    path: str
    finding_code: str
    action: str
    reason: str
    target_path: str | None = None
    superseded_by: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "path": self.path,
            "finding_code": self.finding_code,
            "action": self.action,
            "reason": self.reason,
            "target_path": self.target_path,
            "superseded_by": self.superseded_by,
        }


def build_doc_lifecycle_sweep_payload(
    project_root: Path,
    *,
    execute: bool = False,
    only: str = "",
    until: str | None = None,
    review_after: str | None = None,
    today: date | None = None,
) -> dict[str, Any]:
    root = project_root.resolve()
    run_date = today or date.today()
    candidates = build_doc_lifecycle_sweep_candidates(root, today=run_date)
    selected_ids = _parse_only(only)
    mode = "execute" if execute else "dry-run"
    selected = [candidate for candidate in candidates if not selected_ids or candidate.id in selected_ids]
    unknown_ids = sorted(selected_ids - {candidate.id for candidate in candidates})

    if execute and not selected_ids:
        return _blocked_sweep_payload(mode, candidates, "missing_only", selected_ids, unknown_ids)
    if unknown_ids:
        return _blocked_sweep_payload(mode, candidates, "unknown_finding_id", selected_ids, unknown_ids)
    if execute and any(candidate.action == "defer" for candidate in selected) and not until:
        return _blocked_sweep_payload(mode, candidates, "missing_until_for_defer", selected_ids, unknown_ids)
    if execute and until and not _is_iso_date(until):
        return _blocked_sweep_payload(mode, candidates, "invalid_until_date", selected_ids, unknown_ids)

    applied: list[dict[str, Any]] = []
    if execute:
        with workspace_mutation_lock(root, "docs-lifecycle-sweep"):
            for candidate in selected:
                applied.append(
                    _execute_candidate(
                        root,
                        candidate,
                        today=run_date,
                        until=until,
                        review_after=review_after,
                    )
                )

    return {
        "schema_version": 1,
        "kind": "doc_lifecycle_sweep",
        "mode": mode,
        "result_status": "PASS",
        "summary": _sweep_summary(candidates, selected, applied),
        "actions": [candidate.to_dict() for candidate in candidates],
        "selected_ids": sorted(selected_ids),
        "applied": applied,
        "mutation": "workspace" if applied else "none",
    }


def build_doc_lifecycle_sweep_candidates(project_root: Path, *, today: date | None = None) -> tuple[SweepCandidate, ...]:
    root = project_root.resolve()
    run_date = today or date.today()
    report = build_doc_lifecycle_report(root, now=run_date)
    registry_by_path = _registry_entries_by_path(root)
    candidates: dict[str, SweepCandidate] = {}

    for finding in report.findings:
        action = _action_for_lifecycle_finding(finding.code, finding.path, registry_by_path)
        candidate = SweepCandidate(
            id=_finding_id(finding.path, finding.code),
            path=finding.path,
            finding_code=finding.code,
            action=action,
            reason=finding.message,
            target_path=_archive_target_for(root, finding.path) if action == "archive" else None,
            superseded_by=_superseded_context(root, finding.path, finding.code),
        )
        candidates[candidate.id] = candidate

    try:
        direction_audit = audit_project_direction_drift(root)
    except (OSError, ValueError, yaml.YAMLError):
        direction_audit = None
    if direction_audit is not None:
        for record in direction_audit.records:
            if record.classification != "SOURCE_OF_CLOSED_ITEM_STILL_ACTIVE":
                continue
            code = record.classification
            target = _archive_target_for(root, record.path)
            candidates[_finding_id(record.path, code)] = SweepCandidate(
                id=_finding_id(record.path, code),
                path=record.path,
                finding_code=code,
                action="archive",
                reason=f"source file belongs to closed Direction item {record.item_id}",
                target_path=target,
                superseded_by=f"docs/planning/PROJECT_DIRECTION.yaml#{record.item_id}",
            )

    return tuple(sorted(candidates.values(), key=lambda item: (item.path, item.finding_code)))


def render_doc_lifecycle_sweep(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "DOC_LIFECYCLE_SWEEP",
        f"STATUS={payload['result_status']}",
        f"MODE={payload['mode']}",
        f"ACTION_COUNT={summary['actions']}",
        f"SELECTED_COUNT={summary['selected']}",
        f"APPLIED_COUNT={summary['applied']}",
    ]
    if payload["result_status"] == "BLOCK":
        lines.append(f"REASON={payload['reason']}")
        if payload.get("unknown_ids"):
            lines.append("UNKNOWN_IDS=" + ",".join(payload["unknown_ids"]))
    actions = payload.get("actions", [])
    if not actions:
        lines.append("ACTION=none")
    for action in actions:
        target = f"|target={action['target_path']}" if action.get("target_path") else ""
        lines.append(
            f"ACTION={action['id']}|{action['action']}|path={action['path']}|finding={action['finding_code']}{target}"
        )
    for applied in payload.get("applied", []):
        lines.append(f"APPLIED={applied['id']}|{applied['action']}|path={applied['path']}")
    return "\n".join(lines) + "\n"


def build_doc_lifecycle_bootstrap_payload(
    project_root: Path,
    *,
    execute: bool = False,
    today: date | None = None,
) -> dict[str, Any]:
    root = project_root.resolve()
    candidates = _bootstrap_candidates(root, today=today or date.today())
    applied: list[dict[str, Any]] = []
    if execute:
        with workspace_mutation_lock(root, "docs-lifecycle-bootstrap"):
            for candidate in candidates:
                path = root / candidate["path"]
                text = path.read_text(encoding="utf-8")
                path.write_text(
                    _insert_or_update_header(
                        text,
                        {
                            "Status": "unreviewed",
                            "Status-date": candidate["status_date"],
                        },
                    ),
                    encoding="utf-8",
                )
                applied.append(candidate)
    return {
        "schema_version": 1,
        "kind": "doc_lifecycle_bootstrap",
        "mode": "execute" if execute else "dry-run",
        "result_status": "PASS",
        "candidate_count": len(candidates),
        "applied_count": len(applied),
        "candidates": candidates,
        "applied": applied,
        "mutation": "workspace" if applied else "none",
    }


def render_doc_lifecycle_bootstrap(payload: dict[str, Any]) -> str:
    lines = [
        "DOC_LIFECYCLE_BOOTSTRAP",
        f"STATUS={payload['result_status']}",
        f"MODE={payload['mode']}",
        f"CANDIDATE_COUNT={payload['candidate_count']}",
        f"APPLIED_COUNT={payload['applied_count']}",
    ]
    if not payload["candidates"]:
        lines.append("CANDIDATE=none")
    for candidate in payload["candidates"]:
        lines.append(f"CANDIDATE={candidate['path']}|status_date={candidate['status_date']}")
    return "\n".join(lines) + "\n"


def build_doc_lifecycle_propose_delete_payload(project_root: Path, *, today: date | None = None) -> dict[str, Any]:
    root = project_root.resolve()
    run_date = today or date.today()
    references = _reference_texts(root)
    candidates: list[dict[str, Any]] = []
    for path in sorted((root / "docs" / "archive").rglob("*.md")):
        relative = path.relative_to(root).as_posix()
        status_date = _first_header_value(path.read_text(encoding="utf-8"), "Status-date")
        age_days = _age_days(status_date, run_date)
        if age_days is None or age_days <= 365:
            continue
        if any(relative in text for source, text in references.items() if source != relative):
            continue
        candidates.append(
            {
                "path": relative,
                "status_date": status_date,
                "age_days": age_days,
                "action": "manual-delete-review",
            }
        )
    return {
        "schema_version": 1,
        "kind": "doc_lifecycle_propose_delete",
        "mode": "report-only",
        "result_status": "PASS",
        "candidate_count": len(candidates),
        "candidates": candidates,
        "mutation": "none",
    }


def render_doc_lifecycle_propose_delete(payload: dict[str, Any]) -> str:
    lines = [
        "DOC_LIFECYCLE_PROPOSE_DELETE",
        f"STATUS={payload['result_status']}",
        f"CANDIDATE_COUNT={payload['candidate_count']}",
    ]
    if not payload["candidates"]:
        lines.append("CANDIDATE=none")
    for candidate in payload["candidates"]:
        lines.append(
            f"CANDIDATE={candidate['path']}|age_days={candidate['age_days']}|status_date={candidate['status_date']}"
        )
    return "\n".join(lines) + "\n"


def lifecycle_badge_from_audit_payload(payload: dict[str, Any]) -> str:
    findings = payload.get("findings", [])
    warn = len(findings) if isinstance(findings, list) else 0
    due_codes = {"REVIEW_DUE_RELEASE", "REVIEW_DUE_DIRECTION", "REVIEW_DUE_DATE", "SOURCE_OF_CLOSED_ITEM_STILL_ACTIVE"}
    due = 0
    if isinstance(findings, list):
        due = sum(1 for finding in findings if isinstance(finding, dict) and finding.get("code") in due_codes)
    return f"lifecycle: {warn} warn / {due} due"


def _blocked_sweep_payload(
    mode: str,
    candidates: tuple[SweepCandidate, ...],
    reason: str,
    selected_ids: set[str],
    unknown_ids: list[str],
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "kind": "doc_lifecycle_sweep",
        "mode": mode,
        "result_status": "BLOCK",
        "reason": reason,
        "summary": _sweep_summary(candidates, (), ()),
        "actions": [candidate.to_dict() for candidate in candidates],
        "selected_ids": sorted(selected_ids),
        "unknown_ids": unknown_ids,
        "applied": [],
        "mutation": "none",
    }


def _sweep_summary(
    candidates: tuple[SweepCandidate, ...],
    selected: list[SweepCandidate] | tuple[SweepCandidate, ...],
    applied: list[dict[str, Any]] | tuple[dict[str, Any], ...],
) -> dict[str, int]:
    return {
        "actions": len(candidates),
        "selected": len(selected),
        "applied": len(applied),
        "archive": sum(1 for item in candidates if item.action == "archive"),
        "confirm_current": sum(1 for item in candidates if item.action == "confirm-current"),
        "defer": sum(1 for item in candidates if item.action == "defer"),
    }


def _execute_candidate(
    root: Path,
    candidate: SweepCandidate,
    *,
    today: date,
    until: str | None,
    review_after: str | None,
) -> dict[str, Any]:
    if candidate.action == "archive":
        return _execute_archive(root, candidate, today=today)
    if candidate.action == "confirm-current":
        return _execute_confirm_current(root, candidate, today=today, review_after=review_after)
    if candidate.action == "defer":
        assert until is not None
        return _execute_defer(root, candidate, until=until)
    raise ValueError(f"unsupported sweep action: {candidate.action}")


def _execute_archive(root: Path, candidate: SweepCandidate, *, today: date) -> dict[str, Any]:
    if candidate.target_path is None:
        raise ValueError("archive candidate missing target_path")
    source = root / candidate.path
    target = root / candidate.target_path
    target.parent.mkdir(parents=True, exist_ok=True)
    moved_with_git = _git_mv_or_rename(root, source, target)
    text = target.read_text(encoding="utf-8")
    target.write_text(
        _insert_or_update_header(
            text,
            {
                "Status": "superseded",
                "Status-date": today.isoformat(),
                "Superseded-by": candidate.superseded_by or "manual-maintainer-review",
            },
        ),
        encoding="utf-8",
    )
    _update_registry_path(root, candidate.path, candidate.target_path, archived=True)
    _replace_direction_source_file(root, candidate.path, candidate.target_path)
    return {
        "id": candidate.id,
        "path": candidate.path,
        "target_path": candidate.target_path,
        "action": "archive",
        "moved_with_git": moved_with_git,
        "header_updated": True,
        "registry_updated": True,
        "direction_updated": True,
    }


def _execute_confirm_current(
    root: Path,
    candidate: SweepCandidate,
    *,
    today: date,
    review_after: str | None,
) -> dict[str, Any]:
    path = root / candidate.path
    text = path.read_text(encoding="utf-8")
    updates = {"Status-date": today.isoformat()}
    if _first_header_value(text, "Status") is None:
        registry_status = _registry_entries_by_path(root).get(candidate.path, {}).get("status")
        if isinstance(registry_status, str) and registry_status:
            updates = {"Status": registry_status, **updates}
    path.write_text(_insert_or_update_header(text, updates), encoding="utf-8")
    if review_after:
        _set_registry_field(root, candidate.path, "review_after", review_after)
    return {
        "id": candidate.id,
        "path": candidate.path,
        "action": "confirm-current",
        "header_updated": True,
        "registry_review_after": review_after,
    }


def _execute_defer(root: Path, candidate: SweepCandidate, *, until: str) -> dict[str, Any]:
    date.fromisoformat(until)
    _set_registry_field(root, candidate.path, "deferred_until", until)
    return {
        "id": candidate.id,
        "path": candidate.path,
        "action": "defer",
        "deferred_until": until,
        "registry_updated": True,
    }


def _action_for_lifecycle_finding(code: str, path: str, registry_by_path: dict[str, dict[str, Any]]) -> str:
    if code in {"STALE_BY_BUDGET", "REVIEW_DUE_DATE", "REVIEW_DUE_RELEASE", "REVIEW_DUE_DIRECTION"}:
        return "confirm-current"
    if code == "HEADER_MISSING":
        text_status = str(registry_by_path.get(path, {}).get("status") or "")
        return "confirm-current" if text_status in {"active", "accepted", "implemented"} else "defer"
    if code in {"HEADER_REGISTRY_MISMATCH", "SUPERSEDED_TARGET_MISSING"}:
        status = str(registry_by_path.get(path, {}).get("status") or "")
        return "archive" if status in {"superseded", "archived", "rejected"} else "defer"
    return "defer"


def _finding_id(path: str, code: str) -> str:
    return f"{path}:{code}"


def _parse_only(value: str) -> set[str]:
    if not value:
        return set()
    return {item.strip() for item in value.split(",") if item.strip()}


def _is_iso_date(value: str) -> bool:
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def _registry_entries_by_path(project_root: Path) -> dict[str, dict[str, Any]]:
    try:
        registry = load_documentation_registry(project_root)
    except (OSError, ValueError, yaml.YAMLError):
        return {}
    documents = registry.get("documents", [])
    if not isinstance(documents, list):
        return {}
    return {
        entry["path"]: entry
        for entry in documents
        if isinstance(entry, dict) and isinstance(entry.get("path"), str)
    }


def _write_registry(project_root: Path, registry: dict[str, Any]) -> None:
    path = load_workspace(project_root).doc_registry_path()
    path.write_text(yaml.safe_dump(registry, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _update_registry_path(project_root: Path, old_path: str, new_path: str, *, archived: bool) -> None:
    registry = load_documentation_registry(project_root)
    documents = registry.get("documents", [])
    if not isinstance(documents, list):
        return
    for entry in documents:
        if isinstance(entry, dict) and entry.get("path") == old_path:
            entry["path"] = new_path
            if archived:
                entry["class"] = ARCHIVE_CLASS
                entry["status"] = "superseded"
                entry["archived_from"] = old_path
            break
    _write_registry(project_root, registry)


def _set_registry_field(project_root: Path, path: str, key: str, value: str) -> None:
    registry = load_documentation_registry(project_root)
    documents = registry.get("documents", [])
    if not isinstance(documents, list):
        return
    for entry in documents:
        if isinstance(entry, dict) and entry.get("path") == path:
            entry[key] = value
            break
    _write_registry(project_root, registry)


def _replace_direction_source_file(project_root: Path, old_path: str, new_path: str) -> None:
    path = load_workspace(project_root).project_direction_path()
    if not path.exists():
        return
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    changed = _replace_source_file_entries(data, old_path, new_path)
    if changed:
        path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _replace_source_file_entries(value: Any, old_path: str, new_path: str) -> bool:
    changed = False
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "source_files" and isinstance(item, list):
                for index, source in enumerate(item):
                    if source == old_path:
                        item[index] = new_path
                        changed = True
            else:
                changed = _replace_source_file_entries(item, old_path, new_path) or changed
    elif isinstance(value, list):
        for item in value:
            changed = _replace_source_file_entries(item, old_path, new_path) or changed
    return changed


def _git_mv_or_rename(root: Path, source: Path, target: Path) -> bool:
    completed = subprocess.run(
        ["git", "mv", source.relative_to(root).as_posix(), target.relative_to(root).as_posix()],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode == 0:
        return True
    shutil.move(str(source), str(target))
    return False


def _archive_target_for(root: Path, path: str) -> str:
    source = Path(path)
    stem = source.stem
    suffix = source.suffix or ".md"
    candidate = Path(ARCHIVE_PREFIX) / f"{stem}{suffix}"
    index = 2
    while (root / candidate).exists():
        candidate = Path(ARCHIVE_PREFIX) / f"{stem}-{index}{suffix}"
        index += 1
    return candidate.as_posix()


def _superseded_context(root: Path, path: str, code: str) -> str:
    try:
        text = (root / path).read_text(encoding="utf-8")
    except OSError:
        return "manual-maintainer-review"
    existing = _first_header_value(text, "Superseded-by")
    if existing:
        return existing
    if code == "HEADER_REGISTRY_MISMATCH":
        return "registry-status-mismatch"
    return "manual-maintainer-review"


def _insert_or_update_header(text: str, updates: dict[str, str]) -> str:
    lines = text.splitlines()
    positions: dict[str, int] = {}
    for index, line in enumerate(lines):
        for key in updates:
            if line.startswith(f"{key}:"):
                positions[key] = index
    for key, value in updates.items():
        if key in positions:
            lines[positions[key]] = f"{key}: {value}"
    missing = [(key, value) for key, value in updates.items() if key not in positions]
    if missing:
        insert_at = 1 if lines and lines[0].startswith("#") else 0
        header_lines = [f"{key}: {value}" for key, value in missing]
        if insert_at == 1 and len(lines) > 1 and lines[1].strip():
            header_lines.append("")
        lines[insert_at:insert_at] = header_lines
    return "\n".join(lines) + "\n"


def _first_header_value(text: str, key: str) -> str | None:
    prefix = f"{key}:"
    for line in text.splitlines():
        if line.startswith(prefix):
            return line.removeprefix(prefix).strip() or None
    return None


def _bootstrap_candidates(project_root: Path, *, today: date) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for path in sorted((project_root / "docs").rglob("*.md")):
        relative = path.relative_to(project_root).as_posix()
        if _is_lifecycle_exempt(relative):
            continue
        text = path.read_text(encoding="utf-8")
        if _first_header_value(text, "Status") is not None:
            continue
        candidates.append(
            {
                "path": relative,
                "status_date": _last_commit_date(project_root, relative) or today.isoformat(),
            }
        )
    return candidates


def _is_lifecycle_exempt(path: str) -> bool:
    return any(path.startswith(prefix) for prefix in LIFECYCLE_EXEMPT_PREFIXES)


def _last_commit_date(project_root: Path, path: str) -> str | None:
    completed = subprocess.run(
        ["git", "log", "-1", "--format=%cs", "--", path],
        cwd=project_root,
        text=True,
        capture_output=True,
        check=False,
    )
    value = completed.stdout.strip()
    return value or None


def _reference_texts(project_root: Path) -> dict[str, str]:
    texts: dict[str, str] = {}
    for path in project_root.rglob("*"):
        if not path.is_file() or path.suffix not in REFERENCE_SUFFIXES:
            continue
        if REFERENCE_EXCLUDED_PARTS & set(path.parts):
            continue
        relative = path.relative_to(project_root).as_posix()
        try:
            texts[relative] = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
    return texts


def _age_days(status_date: str | None, today: date) -> int | None:
    if not status_date:
        return None
    try:
        parsed = date.fromisoformat(status_date)
    except ValueError:
        return None
    return (today - parsed).days


def json_dumps(data: dict[str, Any]) -> str:
    return json.dumps(data, indent=2, sort_keys=True) + "\n"
