from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Literal

import yaml

PROJECT_DIRECTION_PATH = Path("docs/planning/project_direction.yaml")


@dataclass(frozen=True)
class ProjectDirection:
    data: dict[str, Any]
    path: Path

    def validate(self) -> list[str]:
        findings: list[str] = []
        required = ("schema_version", "status", "updated", "authority", "strategy", "roadmap", "ideas")
        for key in required:
            if key not in self.data:
                findings.append(f"missing required key: {key}")
        if self.data.get("schema_version") != 1:
            findings.append("schema_version must be 1")
        if self.data.get("status") != "active":
            findings.append("status must be active")
        if self.data.get("authority") != PROJECT_DIRECTION_PATH.as_posix():
            findings.append(f"authority must be {PROJECT_DIRECTION_PATH.as_posix()}")
        for section in ("strategy", "roadmap", "ideas"):
            if not isinstance(self.data.get(section), dict):
                findings.append(f"{section} must be a mapping")
        return findings


def load_project_direction(root: Path | str = ".") -> ProjectDirection:
    path = Path(root) / PROJECT_DIRECTION_PATH
    raw = path.read_text(encoding="utf-8")
    data = yaml.safe_load(raw)
    if not isinstance(data, dict):
        raise ValueError(f"{PROJECT_DIRECTION_PATH.as_posix()} must contain a YAML mapping")
    return ProjectDirection(data=data, path=path)


def render_project_direction(
    direction: ProjectDirection,
    *,
    section: Literal["all", "strategy", "roadmap", "ideas"] = "all",
    output_format: Literal["text", "markdown", "json"] = "text",
) -> str:
    findings = direction.validate()
    if findings:
        raise ValueError("; ".join(findings))

    if output_format == "json":
        payload: Any = direction.data if section == "all" else {section: direction.data[section]}
        return json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if output_format == "markdown":
        return _render_markdown(direction.data, section)
    return _render_text(direction.data, section)


def _render_text(data: dict[str, Any], section: str) -> str:
    lines: list[str] = [
        "PROJECT DIRECTION",
        f"Status: {data.get('status')}",
        f"Updated: {data.get('updated')}",
        f"Authority: {data.get('authority')}",
        "",
    ]
    if section in {"all", "strategy"}:
        _append_strategy_text(lines, data["strategy"])
    if section in {"all", "roadmap"}:
        _append_roadmap_text(lines, data["roadmap"])
    if section in {"all", "ideas"}:
        _append_ideas_text(lines, data["ideas"])
    return "\n".join(lines).rstrip() + "\n"


def _render_markdown(data: dict[str, Any], section: str) -> str:
    lines: list[str] = [
        "# Project Direction",
        "",
        f"- Status: `{data.get('status')}`",
        f"- Updated: `{data.get('updated')}`",
        f"- Authority: `{data.get('authority')}`",
        "",
    ]
    if section in {"all", "strategy"}:
        _append_strategy_markdown(lines, data["strategy"])
    if section in {"all", "roadmap"}:
        _append_roadmap_markdown(lines, data["roadmap"])
    if section in {"all", "ideas"}:
        _append_ideas_markdown(lines, data["ideas"])
    return "\n".join(lines).rstrip() + "\n"


def _append_strategy_text(lines: list[str], strategy: dict[str, Any]) -> None:
    lines.append("Strategy")
    summary = strategy.get("summary")
    if summary:
        lines.append(f"- {summary}")
    for item in strategy.get("principles", []):
        lines.append(f"- {item.get('title')}: {item.get('text')}")
    lines.append("")


def _append_roadmap_text(lines: list[str], roadmap: dict[str, Any]) -> None:
    lines.append("Roadmap")
    current = roadmap.get("current_phase", {})
    next_phase = roadmap.get("next_phase", {})
    lines.append(f"- Current: {current.get('id')} {current.get('title')} [{current.get('status')}]")
    lines.append(f"- Next: {next_phase.get('id')} {next_phase.get('title')} [{next_phase.get('status')}]")
    lines.append("- Milestones:")
    for item in roadmap.get("milestones", []):
        lines.append(f"  - {item.get('id')}: {item.get('title')} [{item.get('status')}]")
    lines.append("")


def _append_ideas_text(lines: list[str], ideas: dict[str, Any]) -> None:
    lines.append("Ideas")
    for bucket in ("active", "parked", "rejected"):
        lines.append(f"- {bucket.title()}:")
        for item in ideas.get(bucket, []):
            detail = item.get("reason") or item.get("text") or ""
            lines.append(f"  - {item.get('title')}: {detail}")
    lines.append("")


def _append_strategy_markdown(lines: list[str], strategy: dict[str, Any]) -> None:
    lines.append("## Strategy")
    lines.append("")
    if strategy.get("summary"):
        lines.append(str(strategy["summary"]))
        lines.append("")
    for item in strategy.get("principles", []):
        lines.append(f"- **{item.get('title')}** (`{item.get('status')}`): {item.get('text')}")
    lines.append("")


def _append_roadmap_markdown(lines: list[str], roadmap: dict[str, Any]) -> None:
    lines.append("## Roadmap")
    lines.append("")
    current = roadmap.get("current_phase", {})
    next_phase = roadmap.get("next_phase", {})
    lines.append(f"- **Current:** `{current.get('id')}` — {current.get('title')} (`{current.get('status')}`)")
    lines.append(f"- **Next:** `{next_phase.get('id')}` — {next_phase.get('title')} (`{next_phase.get('status')}`)")
    lines.append("")
    lines.append("### Milestones")
    for item in roadmap.get("milestones", []):
        lines.append(f"- `{item.get('id')}` — {item.get('title')} (`{item.get('status')}`)")
    lines.append("")


def _append_ideas_markdown(lines: list[str], ideas: dict[str, Any]) -> None:
    lines.append("## Ideas")
    for bucket in ("active", "parked", "rejected"):
        lines.append("")
        lines.append(f"### {bucket.title()}")
        for item in ideas.get(bucket, []):
            detail = item.get("reason") or item.get("text") or ""
            lines.append(f"- **{item.get('title')}** (`{item.get('status')}`): {detail}")
    lines.append("")
