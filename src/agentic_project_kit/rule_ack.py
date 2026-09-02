from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess
from typing import Any

from agentic_project_kit.rule_snapshot import DerivedRuleSnapshot
from agentic_project_kit.volatile_paths import RULE_ACK_DIRECTORY_PATH


RULE_ACK_LOCAL_EXCLUDE_PATTERN = f"{RULE_ACK_DIRECTORY_PATH}/"


@dataclass(frozen=True)
class RuleAcknowledgement:
    schema_version: int
    snapshot_id: str
    repo_head: str
    sources_total: int
    missing_sources_total: int
    declared_next_allowed_action: str

    def as_json_data(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "snapshot_id": self.snapshot_id,
            "repo_head": self.repo_head,
            "sources_total": self.sources_total,
            "missing_sources_total": self.missing_sources_total,
            "declared_next_allowed_action": self.declared_next_allowed_action,
        }


@dataclass(frozen=True)
class RuleAcknowledgementDecision:
    schema_version: int
    is_confirmed: bool
    fail_closed: bool
    blocking_reasons: tuple[str, ...]
    warnings: tuple[str, ...] = ()

    def as_json_data(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "is_confirmed": self.is_confirmed,
            "fail_closed": self.fail_closed,
            "blocking_reasons": list(self.blocking_reasons),
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True)
class RuleAckLocalExclude:
    path: str
    updated: bool
    patterns: tuple[str, ...]
    error: str = ""

    def as_json_data(self) -> dict[str, object]:
        return {
            "path": self.path,
            "updated": self.updated,
            "patterns": list(self.patterns),
            "error": self.error,
        }


def acknowledgement_from_json_data(data: dict[str, Any]) -> RuleAcknowledgement:
    return RuleAcknowledgement(
        schema_version=int(data.get("schema_version", 0)),
        snapshot_id=str(data.get("snapshot_id", "")),
        repo_head=str(data.get("repo_head", "")),
        sources_total=int(data.get("sources_total", -1)),
        missing_sources_total=int(data.get("missing_sources_total", -1)),
        declared_next_allowed_action=str(data.get("declared_next_allowed_action", "")),
    )


def ensure_rule_ack_local_exclude(root: Path) -> RuleAckLocalExclude:
    completed = subprocess.run(
        ["git", "rev-parse", "--git-path", "info/exclude"],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        return RuleAckLocalExclude(path="", updated=False, patterns=(), error=completed.stderr.strip())

    raw_path = completed.stdout.strip()
    if not raw_path:
        return RuleAckLocalExclude(path="", updated=False, patterns=(), error="empty git exclude path")

    exclude_path = Path(raw_path)
    if not exclude_path.is_absolute():
        exclude_path = root / exclude_path

    try:
        existing = exclude_path.read_text(encoding="utf-8") if exclude_path.exists() else ""
        existing_patterns = {line.strip() for line in existing.splitlines()}
        if RULE_ACK_LOCAL_EXCLUDE_PATTERN in existing_patterns:
            return RuleAckLocalExclude(path=str(exclude_path), updated=False, patterns=())

        exclude_path.parent.mkdir(parents=True, exist_ok=True)
        separator = "" if not existing or existing.endswith("\n") else "\n"
        addition = (
            f"{separator}"
            "# Agentic Project Kit local runtime state\n"
            f"{RULE_ACK_LOCAL_EXCLUDE_PATTERN}\n"
        )
        exclude_path.write_text(existing + addition, encoding="utf-8")
    except OSError as exc:
        return RuleAckLocalExclude(path=str(exclude_path), updated=False, patterns=(), error=str(exc))

    return RuleAckLocalExclude(
        path=str(exclude_path),
        updated=True,
        patterns=(RULE_ACK_LOCAL_EXCLUDE_PATTERN,),
    )


def build_rule_acknowledgement(
    snapshot: DerivedRuleSnapshot,
    *,
    repo_head: str,
    declared_next_allowed_action: str,
) -> RuleAcknowledgement:
    return RuleAcknowledgement(
        schema_version=1,
        snapshot_id=snapshot.snapshot_id,
        repo_head=repo_head,
        sources_total=snapshot.sources_total,
        missing_sources_total=len(snapshot.validation.missing_required_paths),
        declared_next_allowed_action=declared_next_allowed_action,
    )


def validate_rule_acknowledgement(
    snapshot: DerivedRuleSnapshot,
    acknowledgement: RuleAcknowledgement | None,
    *,
    repo_head: str,
    required_next_allowed_action: str,
) -> RuleAcknowledgementDecision:
    blocking_reasons: list[str] = []
    warnings: list[str] = []

    if snapshot.fail_closed:
        blocking_reasons.append("rule_snapshot_fail_closed")

    if acknowledgement is None:
        blocking_reasons.append("missing_rule_acknowledgement")
    else:
        if acknowledgement.schema_version != 1:
            blocking_reasons.append("unsupported_rule_acknowledgement_schema_version")
        if acknowledgement.snapshot_id != snapshot.snapshot_id:
            blocking_reasons.append("snapshot_id_mismatch")
        if acknowledgement.repo_head != repo_head:
            warnings.append("repo_head_mismatch")
        if acknowledgement.sources_total != snapshot.sources_total:
            blocking_reasons.append("sources_total_mismatch")
        if acknowledgement.missing_sources_total != len(snapshot.validation.missing_required_paths):
            blocking_reasons.append("missing_sources_total_mismatch")
        if acknowledgement.declared_next_allowed_action != required_next_allowed_action:
            blocking_reasons.append("declared_next_allowed_action_mismatch")

    return RuleAcknowledgementDecision(
        schema_version=1,
        is_confirmed=not blocking_reasons,
        fail_closed=bool(blocking_reasons),
        blocking_reasons=tuple(blocking_reasons),
        warnings=tuple(warnings),
    )
