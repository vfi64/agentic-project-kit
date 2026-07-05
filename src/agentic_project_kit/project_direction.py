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


@dataclass(frozen=True)
class ProjectDirection:
    data: dict[str, Any]
    path: Path
    authority_path: str = PROJECT_DIRECTION_PATH.as_posix()

    def validate(self) -> list[str]:
        findings: list[str] = []
        required = (
            "schema_version",
            "meta",
            "strategy",
            "roadmap",
            "plans",
            "ideas",
            "done",
            "discarded",
        )
        for key in required:
            if key not in self.data:
                findings.append(f"missing required key: {key}")
        if self.data.get("schema_version") != 1:
            findings.append("schema_version must be 1")
        meta = self.data.get("meta")
        if not isinstance(meta, dict):
            findings.append("meta must be a mapping")
        else:
            if meta.get("status") != "active":
                findings.append("meta.status must be active")
            if meta.get("authority") != self.authority_path:
                findings.append(f"meta.authority must be {self.authority_path}")
        for section in ("strategy", "roadmap", "plans", "ideas", "done", "discarded"):
            if not isinstance(self.data.get(section), list):
                findings.append(f"{section} must be a list")
        return findings


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
