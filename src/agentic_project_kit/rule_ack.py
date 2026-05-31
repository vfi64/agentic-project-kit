from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from agentic_project_kit.rule_snapshot import DerivedRuleSnapshot


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

    def as_json_data(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "is_confirmed": self.is_confirmed,
            "fail_closed": self.fail_closed,
            "blocking_reasons": list(self.blocking_reasons),
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


def validate_rule_acknowledgement(
    snapshot: DerivedRuleSnapshot,
    acknowledgement: RuleAcknowledgement | None,
    *,
    repo_head: str,
    required_next_allowed_action: str,
) -> RuleAcknowledgementDecision:
    blocking_reasons: list[str] = []

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
            blocking_reasons.append("repo_head_mismatch")
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
    )
