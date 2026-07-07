from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path


PLANNING_ROOTS = (
    "docs/planning",
    "docs/handoff",
)

ACTIVE_MARKERS = (
    "active",
    "current",
    "next",
    "pending",
    "todo",
    "roadmap",
    "slice",
    "gate",
    "pre-gui",
    "gui",
)

STALE_MARKERS = (
    "obsolete",
    "superseded",
    "archived",
    "deprecated",
    "removed",
    "legacy",
    "done",
    "completed",
    "closed",
)

POST_V049_MARKERS = (
    "v0.4.9",
    "0.4.9",
    "post-v0.4.9",
    "release command authority",
    "audit-doc-currency",
    "audit-absolute-path",
    "audit-ns",
    "gui",
    "0.5.0",
)

AUTHORITATIVE_PLANNING_DOCS = {
    "docs/planning/PROJECT_DIRECTION.yaml",
}

PLANNING_VIEW_DOCS = {
    "docs/planning/PROJECT_DIRECTION.md",
}

SCOPED_AUTHORITATIVE_PLANNING_DOCS = {
    "docs/planning/PRE_GUI_HARDENING_TASKS.md",
}

HANDOFF_PROJECTION_DOCS = {
    "docs/handoff/NEXT_CHAT_BOOTSTRAP.md",
    "docs/handoff/START_NEW_CHAT_PROMPT.md",
}

HISTORICAL_PLANNING_DOCS = {
    "docs/handoff/CODEX_NS_COMMAND_MIGRATION_HANDOFF.md",
    "docs/planning/RELEASE_COMMAND_AUTHORITY_SLICE.md",
    "docs/planning/WORKFLOW_REDUCTION_FOCUS.md",
    "docs/planning/GUI_DETERMINISTIC_GATEKEEPER_PLAN.md",
    "docs/planning/POST_V042_STANDARD_ERROR_HARDENING_PLAN.md",
    "docs/planning/V0.4.0_PORTABLE_LLM_COMMUNICATION_BOOTSTRAP_PLAN.md",
    "docs/planning/V0.3.8_SCOPE.md",
}

KNOWN_ACTIVE_PLANNING_DOCS = set()


LEGACY_REVIEW_DOCS = {
    "docs/handoff/CLOSEOUT_BEFORE_CHAT_SWITCH_PROMPT.md",
    "docs/planning/NEXT_TURN_WORK_ORDER_WORKFLOW_PLAN.md",
    "docs/planning/FAILURE_MODE_REVIEW_AUTOMATION_PLAN.md",
    "docs/planning/POST_MERGE_LIFECYCLE_STATE_MODEL.md",
    "docs/planning/RULE_REFRESH_HANDSHAKE_PLAN.md",
    "docs/planning/RULE_REGISTRY_ARCHITECTURE.md",
}



DUPLICATION_TOPICS = {
    "release_command_authority": (
        "release command authority",
        "release metadata",
        "release-prep",
        "release publish",
        "doi closeout",
    ),
    "ns_migration": (
        "./ns",
        "ns-menu",
        "ns migration",
        "legacy ns",
    ),
    "handoff": (
        "handoff",
        "successor",
        "next chat",
        "bootstrap",
    ),
    "gui": (
        "gui",
        "cockpit",
        "tkinter",
    ),
    "docs_currency": (
        "doc currency",
        "documentation currency",
        "current state",
        "status doc",
    ),
}


@dataclass(frozen=True)
class PlanningDocRecord:
    path: str
    title: str | None
    line_count: int
    active_score: int
    stale_score: int
    post_v049_score: int
    topics: tuple[str, ...]
    classification: str
    reason: str

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class PlanningDocsConsolidationAuditResult:
    root: str
    records: tuple[PlanningDocRecord, ...]
    blockers: tuple[PlanningDocRecord, ...]

    @property
    def ok(self) -> bool:
        return not self.blockers

    @property
    def status(self) -> str:
        return "PASS" if self.ok else "FAIL"

    @property
    def returncode(self) -> int:
        return 0 if self.ok else 1

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "kind": "planning_docs_consolidation_audit",
            "root": self.root,
            "status": self.status,
            "record_count": len(self.records),
            "blocker_count": len(self.blockers),
            "records": [item.as_dict() for item in self.records],
            "blockers": [item.as_dict() for item in self.blockers],
        }


def _title(lines: list[str]) -> str | None:
    for line in lines[:40]:
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip() or None
    return None


def _score(text: str, markers: tuple[str, ...]) -> int:
    lowered = text.lower()
    return sum(lowered.count(marker.lower()) for marker in markers)


def _topics(text: str) -> tuple[str, ...]:
    lowered = text.lower()
    found: list[str] = []
    for topic, markers in DUPLICATION_TOPICS.items():
        if any(marker.lower() in lowered for marker in markers):
            found.append(topic)
    return tuple(found)


def _classify(relative: str, text: str, active_score: int, stale_score: int, post_v049_score: int, topics: tuple[str, ...]) -> tuple[str, str]:
    lowered = text.lower()

    if relative.endswith("CURRENT_HANDOFF.md"):
        return "authoritative_current_handoff", "current handoff is an authoritative state carrier"

    if relative in AUTHORITATIVE_PLANNING_DOCS:
        return "authoritative_planning_anchor", "explicit current planning authority"

    if relative in PLANNING_VIEW_DOCS:
        return "planning_authority_view", "human-readable view of the current planning authority"

    if relative in SCOPED_AUTHORITATIVE_PLANNING_DOCS:
        return "authoritative_scoped_planning_anchor", "explicit scoped planning authority"

    if relative in HANDOFF_PROJECTION_DOCS:
        return "handoff_projection", "generated handoff prompt projection, not planning authority"

    if relative in HISTORICAL_PLANNING_DOCS:
        return "historical_planning_doc", "known historical planning/handoff artifact"

    if relative in LEGACY_REVIEW_DOCS:
        return "legacy_review_candidate", "known follow-up review candidate, not current authority"

    if relative in KNOWN_ACTIVE_PLANNING_DOCS:
        return "active_planning_candidate", "known active planning document, not current overall authority"

    if "current source of truth" in lowered or "source of truth" in lowered:
        return "possible_authoritative_plan", "document claims source-of-truth status"

    if stale_score > active_score and post_v049_score == 0:
        return "stale_or_archival_candidate", "stale markers dominate and no current release marker was found"

    if post_v049_score > 0 and active_score > 0:
        return "active_planning_candidate", "current release and active planning markers found"

    if len(topics) >= 3 and active_score > 0:
        return "consolidation_candidate", "multiple active planning topics in one document"

    if active_score > 0:
        return "active_but_needs_review", "active markers found but no current release anchor"

    return "low_priority_reference", "no strong active or stale signal"


def _iter_docs(root: Path) -> list[Path]:
    docs: list[Path] = []
    for planning_root in PLANNING_ROOTS:
        base = root / planning_root
        if not base.exists():
            continue
        docs.extend(path for path in base.rglob("*") if path.is_file() and path.suffix in {".md", ".yaml", ".yml"})
    return sorted(docs)


def audit_planning_docs_consolidation(root: Path = Path(".")) -> PlanningDocsConsolidationAuditResult:
    root = root.resolve()
    records: list[PlanningDocRecord] = []

    for path in _iter_docs(root):
        relative = path.relative_to(root).as_posix()
        text = path.read_text(encoding="utf-8", errors="replace")
        lines = text.splitlines()
        active_score = _score(text, ACTIVE_MARKERS)
        stale_score = _score(text, STALE_MARKERS)
        post_v049_score = _score(text, POST_V049_MARKERS)
        topics = _topics(text)
        classification, reason = _classify(
            relative,
            text,
            active_score,
            stale_score,
            post_v049_score,
            topics,
        )
        records.append(
            PlanningDocRecord(
                path=relative,
                title=_title(lines),
                line_count=len(lines),
                active_score=active_score,
                stale_score=stale_score,
                post_v049_score=post_v049_score,
                topics=topics,
                classification=classification,
                reason=reason,
            )
        )

    blockers = tuple(
        record
        for record in records
        if record.classification in {
            "possible_authoritative_plan",
            "consolidation_candidate",
            "active_but_needs_review",
        }
    )

    return PlanningDocsConsolidationAuditResult(
        root=root.as_posix(),
        records=tuple(records),
        blockers=blockers,
    )


def render_planning_docs_consolidation_audit(result: PlanningDocsConsolidationAuditResult) -> str:
    lines = [
        "PLANNING_DOCS_CONSOLIDATION_AUDIT",
        f"STATUS={result.status}",
        f"RECORD_COUNT={len(result.records)}",
        f"BLOCKER_COUNT={len(result.blockers)}",
    ]
    for item in result.blockers:
        lines.append(
            "BLOCKER="
            f"{item.classification}|{item.path}|topics={','.join(item.topics)}|"
            f"active={item.active_score}|stale={item.stale_score}|post_v049={item.post_v049_score}|{item.title}"
        )
    for item in result.records:
        lines.append(
            "RECORD="
            f"{item.classification}|{item.path}|topics={','.join(item.topics)}|"
            f"active={item.active_score}|stale={item.stale_score}|post_v049={item.post_v049_score}|{item.title}"
        )
    return "\n".join(lines) + "\n"
