from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from agentic_project_kit.chat_bootloader import MANDATORY_BOOT_SOURCES
from agentic_project_kit.handoff_prompt import MANDATORY_SUCCESSOR_CHAT_SOURCES
from agentic_project_kit.handoff_state import load_handoff_state, validate_handoff_state
from agentic_project_kit.rule_refresh import COMMUNICATION_RULE_SOURCES, HANDOFF_RULE_SOURCES


CANONICAL_YAML_RULE_SOURCES = (
    ".agentic/compiled_agent_context.yaml",
    ".agentic/handoff_state.yaml",
    ".agentic/rule_mechanism_inventory.yaml",
    ".agentic/rule_migrations.yaml",
    ".agentic/rule_preservation.yaml",
)


@dataclass(frozen=True)
class RuleSourceValidationResult:
    source_paths: tuple[str, ...]
    missing_required_paths: tuple[str, ...]
    yaml_parse_error_paths: tuple[str, ...]
    handoff_state_errors: tuple[str, ...]
    blocking_reasons: tuple[str, ...]

    @property
    def sources_total(self) -> int:
        return len(self.source_paths)

    @property
    def is_valid(self) -> bool:
        return not self.blocking_reasons

    @property
    def fail_closed(self) -> bool:
        return bool(self.blocking_reasons)

    def as_json_data(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "sources_total": self.sources_total,
            "is_valid": self.is_valid,
            "fail_closed": self.fail_closed,
            "source_paths": list(self.source_paths),
            "missing_required_paths": list(self.missing_required_paths),
            "yaml_parse_error_paths": list(self.yaml_parse_error_paths),
            "handoff_state_errors": list(self.handoff_state_errors),
            "blocking_reasons": list(self.blocking_reasons),
        }


def canonical_rule_source_paths() -> tuple[str, ...]:
    """Return the de-duplicated canonical rule-source set used for read-only validation."""

    ordered: list[str] = []
    for collection in (
        MANDATORY_BOOT_SOURCES,
        tuple(MANDATORY_SUCCESSOR_CHAT_SOURCES),
        COMMUNICATION_RULE_SOURCES,
        HANDOFF_RULE_SOURCES,
        CANONICAL_YAML_RULE_SOURCES,
    ):
        for source in collection:
            if source == "relevant source files and tests for the requested slice":
                continue
            if source not in ordered:
                ordered.append(source)
    return tuple(ordered)


def validate_rule_sources(root: str | Path = ".") -> RuleSourceValidationResult:
    """Validate canonical rule sources without writing files or generating snapshots."""

    root_path = Path(root)
    source_paths = canonical_rule_source_paths()
    missing_required_paths: list[str] = []
    yaml_parse_error_paths: list[str] = []
    handoff_state_errors: list[str] = []
    blocking_reasons: list[str] = []

    for source in source_paths:
        path = root_path / source
        if not path.exists() or not path.is_file():
            missing_required_paths.append(source)
            blocking_reasons.append(f"missing required rule source: {source}")
            continue

        if path.suffix in {".yaml", ".yml"}:
            try:
                yaml.safe_load(path.read_text(encoding="utf-8"))
            except yaml.YAMLError as exc:
                yaml_parse_error_paths.append(source)
                blocking_reasons.append(f"yaml parse error in rule source: {source}: {exc}")

    handoff_path = root_path / ".agentic/handoff_state.yaml"
    if handoff_path.exists() and handoff_path.is_file():
        try:
            handoff_state_errors.extend(validate_handoff_state(load_handoff_state(handoff_path)))
        except (OSError, ValueError, yaml.YAMLError) as exc:
            handoff_state_errors.append(str(exc))
    for error in handoff_state_errors:
        blocking_reasons.append(f"handoff_state invalid: {error}")

    return RuleSourceValidationResult(
        source_paths=source_paths,
        missing_required_paths=tuple(missing_required_paths),
        yaml_parse_error_paths=tuple(yaml_parse_error_paths),
        handoff_state_errors=tuple(handoff_state_errors),
        blocking_reasons=tuple(blocking_reasons),
    )


def render_rule_source_validation(result: RuleSourceValidationResult) -> str:
    lines = [
        "RULE_SOURCE_VALIDATION",
        f"sources_total={result.sources_total}",
        f"is_valid={result.is_valid}",
        f"fail_closed={result.fail_closed}",
    ]
    for path in result.missing_required_paths:
        lines.append(f"missing_required_path={path}")
    for path in result.yaml_parse_error_paths:
        lines.append(f"yaml_parse_error_path={path}")
    for error in result.handoff_state_errors:
        lines.append(f"handoff_state_error={error}")
    for reason in result.blocking_reasons:
        lines.append(f"blocking_reason={reason}")
    return "\n".join(lines)
