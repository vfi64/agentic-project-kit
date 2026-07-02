from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
import json
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
    github_metadata: dict[str, object] | None = None

    def as_dict(self) -> dict[str, object]:
        result: dict[str, object] = {
            "category": self.category,
            "title": self.title,
            "pr_number": self.pr_number,
            "commit_sha": self.commit_sha,
            "evidence": list(self.evidence),
            "confidence": self.confidence,
        }
        if self.github_metadata is not None:
            result["github_metadata"] = self.github_metadata
        return result


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
    github_metadata_requested: bool
    github_metadata_available: bool
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
            "github_metadata_requested": self.github_metadata_requested,
            "github_metadata_available": self.github_metadata_available,
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
    include_github_metadata: bool = False,
) -> ReleaseNotesReport:
    runner = command_runner or run_command
    plain_version = version.removeprefix("v")
    commits, evidence_errors = _collect_commits(project_root, from_tag=from_tag, to_ref=to_ref, runner=runner)
    generated_at = _deterministic_generated_at(project_root, to_ref=to_ref, runner=runner)
    items: list[ReleaseNoteItem] = []
    administrative_items: list[ReleaseNoteItem] = []
    unclassified_items: list[ReleaseNoteItem] = []
    missing_evidence: list[dict[str, object]] = []
    github_metadata_available = include_github_metadata

    for commit in commits:
        pr_number = _pr_number_from_subject(commit.subject)
        github_metadata, github_missing_evidence = _github_metadata_for_pr(
            project_root,
            pr_number=pr_number,
            runner=runner,
            enabled=include_github_metadata,
        )
        if github_missing_evidence:
            github_metadata_available = False
        item, item_missing_evidence = _item_from_commit(
            commit,
            from_tag=from_tag,
            to_ref=to_ref,
            github_metadata=github_metadata,
        )
        if item.category == "Administrative Handoff Refresh":
            administrative_items.append(item)
        else:
            items.append(item)
            if item.category == "Unclassified":
                unclassified_items.append(item)
        missing_evidence.extend(item_missing_evidence)
        missing_evidence.extend(github_missing_evidence)

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
        github_metadata_requested=include_github_metadata,
        github_metadata_available=github_metadata_available,
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
    json_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(report.as_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown_out.write_text(render_release_notes_markdown(report), encoding="utf-8")


def check_release_notes_outputs(report: ReleaseNotesReport, *, json_out: Path, markdown_out: Path) -> dict[str, object]:
    expected_json = json.dumps(report.as_dict(), indent=2, sort_keys=True) + "\n"
    expected_markdown = render_release_notes_markdown(report)
    checked_paths = (json_out.as_posix(), markdown_out.as_posix())
    missing_paths = [path.as_posix() for path in (json_out, markdown_out) if not path.exists()]
    drifted_paths: list[str] = []
    if not missing_paths:
        if json_out.read_text(encoding="utf-8") != expected_json:
            drifted_paths.append(json_out.as_posix())
        if markdown_out.read_text(encoding="utf-8") != expected_markdown:
            drifted_paths.append(markdown_out.as_posix())
    status = "BLOCK" if missing_paths or drifted_paths else "PASS"
    return {
        "status": status,
        "checked_paths": list(checked_paths),
        "missing_paths": missing_paths,
        "drifted_paths": drifted_paths,
    }


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
    github_metadata: dict[str, object] | None,
) -> tuple[ReleaseNoteItem, tuple[dict[str, object], ...]]:
    pr_number = _pr_number_from_subject(commit.subject)
    title = _title_from_subject(commit.subject)
    category = _classify_with_metadata(commit.subject, github_metadata)
    missing_evidence: list[dict[str, object]] = []
    if pr_number is None:
        missing_evidence.append({"type": "missing_pr_number", "commit_sha": commit.sha, "title": title})
    evidence: list[dict[str, object]] = [
        {"type": "commit", "sha": commit.sha, "subject": commit.subject, "committed_at": _to_utc_iso(commit.committed_at)},
        {"type": "tag_diff", "range": f"{from_tag}..{to_ref}"},
    ]
    if pr_number is not None:
        evidence.append({"type": "pull_request", "number": pr_number})
    if github_metadata is not None:
        evidence.append(
            {
                "type": "github_pull_request_metadata",
                "number": pr_number,
                "title": github_metadata.get("title"),
                "labels": github_metadata.get("labels", []),
                "merge_commit_sha": github_metadata.get("merge_commit_sha"),
                "author": github_metadata.get("author"),
                "url": github_metadata.get("url"),
            }
        )
    return (
        ReleaseNoteItem(
            category=category,
            title=title,
            pr_number=pr_number,
            commit_sha=commit.sha,
            evidence=tuple(evidence),
            confidence="high" if pr_number is not None and category != "Unclassified" else "medium",
            github_metadata=github_metadata,
        ),
        tuple(missing_evidence),
    )


def _github_metadata_for_pr(
    project_root: Path,
    *,
    pr_number: int | None,
    runner: ReleaseNotesRunner,
    enabled: bool,
) -> tuple[dict[str, object] | None, tuple[dict[str, object], ...]]:
    if not enabled:
        return None, ()
    if pr_number is None:
        return None, ()
    result = runner(
        project_root,
        [
            "gh",
            "pr",
            "view",
            str(pr_number),
            "--json",
            "number,title,body,labels,mergeCommit,author,state,url",
        ],
    )
    if result.returncode != 0:
        return None, (
            {
                "type": "github_metadata_unavailable",
                "severity": "WARN",
                "pr_number": pr_number,
                "stderr": result.stderr.strip(),
            },
        )
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        return None, (
            {
                "type": "github_metadata_unparseable",
                "severity": "WARN",
                "pr_number": pr_number,
                "error": str(exc),
            },
        )
    labels = payload.get("labels") or []
    label_names = [str(label.get("name", "")) for label in labels if isinstance(label, dict)]
    merge_commit = payload.get("mergeCommit") if isinstance(payload.get("mergeCommit"), dict) else {}
    author = payload.get("author") if isinstance(payload.get("author"), dict) else {}
    return (
        {
            "number": payload.get("number", pr_number),
            "title": payload.get("title") or "",
            "body": payload.get("body") or "",
            "labels": label_names,
            "merge_commit_sha": merge_commit.get("oid"),
            "author": author.get("login"),
            "state": payload.get("state"),
            "url": payload.get("url"),
        },
        (),
    )


def _pr_number_from_subject(subject: str) -> int | None:
    match = re.search(r"\(#(\d+)\)\s*$", subject)
    return int(match.group(1)) if match else None


def _title_from_subject(subject: str) -> str:
    return re.sub(r"\s+\(#\d+\)\s*$", "", subject).strip()


def _classify_subject(subject: str) -> str:
    lowered = subject.lower()
    if (
        re.search(r"^refresh handoff state after pr\d+", lowered)
        or "administrative handoff" in lowered
        or "publish remote-next transfer report" in lowered
        or "publish final remote-next report projection" in lowered
        or lowered.startswith("refresh successor package")
    ):
        return "Administrative Handoff Refresh"
    if "breaking" in lowered or lowered.startswith("remove "):
        return "Breaking"
    if "release" in lowered or "doi" in lowered:
        return "Release"
    if any(
        token in lowered
        for token in (
            "handoff",
            "transfer",
            "patch cycle",
            "sync-main",
            "outbox",
            "communication",
            "remote-next",
        )
    ):
        return "Transfer / Handoff"
    if any(token in lowered for token in ("governance", "policy", "contract", "authority")):
        return "Governance"
    if any(token in lowered for token in ("test", "gate", "audit", "ruff", "pytest")):
        return "Tests / Gates"
    if any(token in lowered for token in ("doc", "documentation", "planning", "concept", "analysis", "plan ", "roadmap")):
        return "Docs"
    if lowered.startswith(("fix ", "repair ", "harden ", "resolve ", "recheck ", "detect ", "keep ")):
        return "Fixed"
    if lowered.startswith(("add ", "build ")):
        return "Added"
    if lowered.startswith(
        (
            "update ",
            "change ",
            "refactor ",
            "refine ",
            "guide ",
            "extract ",
            "split ",
            "separate ",
            "make ",
            "compact ",
            "simplify ",
            "render ",
        )
    ):
        return "Changed"
    if any(token in lowered for token in ("gui", "cockpit", "tooltip", "layout", "visual hierarchy")):
        return "Changed"
    return "Unclassified"


def _classify_with_metadata(subject: str, github_metadata: dict[str, object] | None) -> str:
    if github_metadata is not None:
        body_category = _category_from_body(str(github_metadata.get("body", "")))
        if body_category:
            return body_category
        label_category = _category_from_labels(github_metadata.get("labels", []))
        if label_category:
            return label_category
    return _classify_subject(subject)


def _category_from_body(body: str) -> str | None:
    for line in body.splitlines()[:40]:
        match = re.match(r"\s*release-note-category\s*:\s*(.+?)\s*$", line, re.I)
        if match:
            return _normalize_category(match.group(1))
    return None


def _category_from_labels(labels: object) -> str | None:
    if not isinstance(labels, list):
        return None
    for raw in labels:
        label = str(raw).strip().lower()
        if label.startswith("release-note:"):
            category = _normalize_category(label.split(":", 1)[1])
            if category:
                return category
        if label in {"type:fix", "bug", "fix"}:
            return "Fixed"
        if label in {"type:docs", "docs", "documentation"}:
            return "Docs"
        if label in {"type:test", "tests", "gates"}:
            return "Tests / Gates"
        if label in {"type:release", "release"}:
            return "Release"
    return None


def _normalize_category(value: str) -> str | None:
    normalized = re.sub(r"\s+", " ", value.strip()).lower()
    aliases = {
        "add": "Added",
        "added": "Added",
        "change": "Changed",
        "changed": "Changed",
        "fix": "Fixed",
        "fixed": "Fixed",
        "governance": "Governance",
        "transfer": "Transfer / Handoff",
        "handoff": "Transfer / Handoff",
        "transfer / handoff": "Transfer / Handoff",
        "docs": "Docs",
        "documentation": "Docs",
        "tests": "Tests / Gates",
        "tests / gates": "Tests / Gates",
        "release": "Release",
        "breaking": "Breaking",
        "known issues": "Known Issues",
    }
    return aliases.get(normalized)


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
    return not (
        re.search(r"^refresh handoff state after pr\d+", title)
        or "administrative handoff" in title
        or "publish remote-next transfer report" in title
        or "publish final remote-next report projection" in title
        or title.startswith("refresh successor package")
    )


def _render_item(item: ReleaseNoteItem) -> str:
    pr = f"PR #{item.pr_number}" if item.pr_number is not None else "PR <missing>"
    return f"- {item.title} ({pr}, `{item.commit_sha[:8]}`)."
