from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import re

from agentic_project_kit.release import CommandResult, run_command


ReleaseNotesRunner = Callable[[Path, Sequence[str]], CommandResult]

RELEASE_NOTE_CATEGORIES = (
    "Added",
    "Changed",
    "Fixed",
    "Governance",
    "Transfer / Handoff",
    "Docs",
    "Tests / Gates",
    "Release",
    "Breaking",
    "Known Issues",
    "Administrative Handoff Refresh",
    "Unclassified",
)


@dataclass(frozen=True)
class ReleaseNoteItem:
    category: str
    title: str
    pr_number: int | None
    commit_sha: str
    evidence: tuple[dict[str, object], ...]
    confidence: str

    def as_dict(self) -> dict[str, object]:
        return {
            "category": self.category,
            "title": self.title,
            "pr_number": self.pr_number,
            "commit_sha": self.commit_sha,
            "evidence": list(self.evidence),
            "confidence": self.confidence,
        }


@dataclass(frozen=True)
class ReleaseNotesValidation:
    status: str
    reasons: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {"status": self.status, "reasons": list(self.reasons)}


@dataclass(frozen=True)
class ReleaseNotesReport:
    schema_version: int
    kind: str
    version: str
    from_tag: str
    to_ref: str
    generated_at_utc: str
    deterministic_timestamp_source: str
    items: tuple[ReleaseNoteItem, ...]
    administrative_items: tuple[ReleaseNoteItem, ...]
    unclassified_items: tuple[ReleaseNoteItem, ...]
    missing_evidence: tuple[dict[str, object], ...]
    validation: ReleaseNotesValidation

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "kind": self.kind,
            "version": self.version,
            "from_tag": self.from_tag,
            "to_ref": self.to_ref,
            "generated_at_utc": self.generated_at_utc,
            "deterministic_timestamp_source": self.deterministic_timestamp_source,
            "items": [item.as_dict() for item in self.items],
            "administrative_items": [item.as_dict() for item in self.administrative_items],
            "unclassified_items": [item.as_dict() for item in self.unclassified_items],
            "missing_evidence": list(self.missing_evidence),
            "validation": self.validation.as_dict(),
        }


@dataclass(frozen=True)
class _GitCommit:
    sha: str
    subject: str
    committed_at: str


def build_release_notes_report(
    project_root: Path,
    *,
    version: str,
    from_tag: str,
    to_ref: str = "HEAD",
    command_runner: ReleaseNotesRunner | None = None,
) -> ReleaseNotesReport:
    runner = command_runner or run_command
    plain_version = version.removeprefix("v")
    commits, evidence_errors = _collect_commits(project_root, from_tag=from_tag, to_ref=to_ref, runner=runner)
    generated_at = _deterministic_generated_at(project_root, to_ref=to_ref, runner=runner)
    items: list[ReleaseNoteItem] = []
    administrative_items: list[ReleaseNoteItem] = []
    unclassified_items: list[ReleaseNoteItem] = []
    missing_evidence: list[dict[str, object]] = []

    for commit in commits:
        item, item_missing_evidence = _item_from_commit(commit, from_tag=from_tag, to_ref=to_ref)
        if item.category == "Administrative Handoff Refresh":
            administrative_items.append(item)
        else:
            items.append(item)
            if item.category == "Unclassified":
                unclassified_items.append(item)
        missing_evidence.extend(item_missing_evidence)

    missing_evidence.extend(evidence_errors)
    validation = _validate_release_notes(
        items=tuple(items),
        unclassified_items=tuple(unclassified_items),
        missing_evidence=tuple(missing_evidence),
    )
    return ReleaseNotesReport(
        schema_version=1,
        kind="release_notes",
        version=plain_version,
        from_tag=from_tag,
        to_ref=to_ref,
        generated_at_utc=generated_at,
        deterministic_timestamp_source="to_ref_committer_date_utc",
        items=tuple(items),
        administrative_items=tuple(administrative_items),
        unclassified_items=tuple(unclassified_items),
        missing_evidence=tuple(missing_evidence),
        validation=validation,
    )


def render_release_notes_markdown(report: ReleaseNotesReport) -> str:
    lines = [
        f"# Release {report.version}",
        "",
        "## Highlights",
        "",
    ]
    if report.validation.status == "PASS":
        lines.append("- Deterministic release notes generated from local Git tag-diff evidence.")
    else:
        lines.append("- Release notes are blocked until missing evidence or unclassified items are resolved.")
    lines.append("")

    grouped: dict[str, list[ReleaseNoteItem]] = defaultdict(list)
    for item in report.items:
        grouped[item.category].append(item)

    for category in RELEASE_NOTE_CATEGORIES:
        if category in {"Administrative Handoff Refresh", "Known Issues", "Unclassified"}:
            continue
        lines.append(f"## {category}")
        category_items = grouped.get(category, [])
        if category_items:
            lines.extend(_render_item(item) for item in category_items)
        else:
            lines.append("- None.")
        lines.append("")

    lines.append("## Administrative Handoff Refresh")
    if report.administrative_items:
        lines.extend(_render_item(item) for item in report.administrative_items)
    else:
        lines.append("- None.")
    lines.append("")

    lines.append("## Evidence")
    lines.append(f"- Range: `{report.from_tag}..{report.to_ref}`.")
    lines.append(f"- Generated timestamp source: `{report.deterministic_timestamp_source}`.")
    for item in (*report.items, *report.administrative_items):
        pr = f"PR #{item.pr_number}" if item.pr_number is not None else "PR <missing>"
        lines.append(f"- `{item.commit_sha[:8]}` {pr}: {item.title}")
    lines.append("")

    lines.append("## Known Issues")
    if report.validation.status == "PASS":
        lines.append("- None recorded by the deterministic release-notes generator.")
    else:
        for reason in report.validation.reasons:
            lines.append(f"- {reason}")
    lines.append("")
    return "\n".join(lines)


def write_release_notes_outputs(report: ReleaseNotesReport, *, json_out: Path, markdown_out: Path) -> None:
    import json

    json_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(report.as_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown_out.write_text(render_release_notes_markdown(report), encoding="utf-8")


def _collect_commits(
    project_root: Path,
    *,
    from_tag: str,
    to_ref: str,
    runner: ReleaseNotesRunner,
) -> tuple[tuple[_GitCommit, ...], tuple[dict[str, object], ...]]:
    missing_evidence: list[dict[str, object]] = []
    if runner(project_root, ["git", "rev-parse", "--verify", from_tag]).returncode != 0:
        missing_evidence.append({"type": "missing_ref", "ref": from_tag})
        return (), tuple(missing_evidence)
    if runner(project_root, ["git", "rev-parse", "--verify", to_ref]).returncode != 0:
        missing_evidence.append({"type": "missing_ref", "ref": to_ref})
        return (), tuple(missing_evidence)
    result = runner(project_root, ["git", "log", "--reverse", "--format=%H%x1f%s%x1f%cI%x1e", f"{from_tag}..{to_ref}"])
    if result.returncode != 0:
        missing_evidence.append({"type": "git_log_failed", "range": f"{from_tag}..{to_ref}", "stderr": result.stderr.strip()})
        return (), tuple(missing_evidence)
    commits: list[_GitCommit] = []
    for record in result.stdout.strip("\x1e\n").split("\x1e"):
        if not record.strip():
            continue
        parts = record.strip("\n").split("\x1f")
        if len(parts) != 3:
            missing_evidence.append({"type": "unparseable_git_log_record", "record": record[:160]})
            continue
        commits.append(_GitCommit(sha=parts[0], subject=parts[1], committed_at=parts[2]))
    return tuple(commits), tuple(missing_evidence)


def _deterministic_generated_at(project_root: Path, *, to_ref: str, runner: ReleaseNotesRunner) -> str:
    result = runner(project_root, ["git", "show", "-s", "--format=%cI", to_ref])
    if result.returncode != 0:
        return "unknown"
    return _to_utc_iso(result.stdout.strip())


def _to_utc_iso(value: str) -> str:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    except ValueError:
        return value


def _item_from_commit(
    commit: _GitCommit,
    *,
    from_tag: str,
    to_ref: str,
) -> tuple[ReleaseNoteItem, tuple[dict[str, object], ...]]:
    pr_number = _pr_number_from_subject(commit.subject)
    title = _title_from_subject(commit.subject)
    category = _classify_subject(commit.subject)
    missing_evidence: list[dict[str, object]] = []
    if pr_number is None:
        missing_evidence.append({"type": "missing_pr_number", "commit_sha": commit.sha, "title": title})
    evidence: list[dict[str, object]] = [
        {"type": "commit", "sha": commit.sha, "subject": commit.subject, "committed_at": _to_utc_iso(commit.committed_at)},
        {"type": "tag_diff", "range": f"{from_tag}..{to_ref}"},
    ]
    if pr_number is not None:
        evidence.append({"type": "pull_request", "number": pr_number})
    return (
        ReleaseNoteItem(
            category=category,
            title=title,
            pr_number=pr_number,
            commit_sha=commit.sha,
            evidence=tuple(evidence),
            confidence="high" if pr_number is not None and category != "Unclassified" else "medium",
        ),
        tuple(missing_evidence),
    )


def _pr_number_from_subject(subject: str) -> int | None:
    match = re.search(r"\(#(\d+)\)\s*$", subject)
    return int(match.group(1)) if match else None


def _title_from_subject(subject: str) -> str:
    return re.sub(r"\s+\(#\d+\)\s*$", "", subject).strip()


def _classify_subject(subject: str) -> str:
    lowered = subject.lower()
    if re.search(r"^refresh handoff state after pr\d+", lowered) or "administrative handoff" in lowered:
        return "Administrative Handoff Refresh"
    if "breaking" in lowered or lowered.startswith("remove "):
        return "Breaking"
    if "release" in lowered or "doi" in lowered:
        return "Release"
    if any(token in lowered for token in ("handoff", "transfer", "patch cycle", "sync-main", "outbox")):
        return "Transfer / Handoff"
    if any(token in lowered for token in ("governance", "policy", "contract", "authority")):
        return "Governance"
    if any(token in lowered for token in ("test", "gate", "audit", "ruff", "pytest")):
        return "Tests / Gates"
    if any(token in lowered for token in ("doc", "documentation", "planning", "concept", "analysis")):
        return "Docs"
    if lowered.startswith(("fix ", "repair ", "harden ")):
        return "Fixed"
    if lowered.startswith(("update ", "change ", "refactor ")):
        return "Changed"
    if lowered.startswith("add "):
        return "Added"
    return "Unclassified"


def _validate_release_notes(
    *,
    items: tuple[ReleaseNoteItem, ...],
    unclassified_items: tuple[ReleaseNoteItem, ...],
    missing_evidence: tuple[dict[str, object], ...],
) -> ReleaseNotesValidation:
    reasons: list[str] = []
    if unclassified_items:
        refs = ", ".join(item.commit_sha[:8] for item in unclassified_items)
        reasons.append(f"Unclassified product release-note items must be classified before release: {refs}")
    product_missing_pr = [
        evidence for evidence in missing_evidence if evidence.get("type") == "missing_pr_number" and _is_product_commit(evidence)
    ]
    if product_missing_pr:
        refs = ", ".join(str(evidence.get("commit_sha", ""))[:8] for evidence in product_missing_pr)
        reasons.append(f"Product release-note items are missing PR evidence: {refs}")
    ref_errors = [evidence for evidence in missing_evidence if evidence.get("type") in {"missing_ref", "git_log_failed", "unparseable_git_log_record"}]
    for evidence in ref_errors:
        reasons.append(f"Missing or invalid git evidence: {evidence}")
    return ReleaseNotesValidation(status="BLOCK" if reasons else "PASS", reasons=tuple(reasons))


def _is_product_commit(evidence: dict[str, object]) -> bool:
    title = str(evidence.get("title", "")).lower()
    return not (re.search(r"^refresh handoff state after pr\d+", title) or "administrative handoff" in title)


def _render_item(item: ReleaseNoteItem) -> str:
    pr = f"PR #{item.pr_number}" if item.pr_number is not None else "PR <missing>"
    return f"- {item.title} ({pr}, `{item.commit_sha[:8]}`)."
