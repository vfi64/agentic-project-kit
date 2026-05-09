from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


DEFAULT_TODO_PATH = Path(".agentic/todo.yaml")
DEFAULT_RENDER_PATH = Path("docs/TODO.md")


def load_todo(path: Path = DEFAULT_TODO_PATH) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"TODO file not found: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    items = data.get("items")
    if not isinstance(items, list):
        raise ValueError(f"TODO file must contain an 'items' list: {path}")
    return data


def save_todo(data: dict[str, Any], path: Path = DEFAULT_TODO_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(data, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


def list_items(data: dict[str, Any], include_done: bool = False) -> list[dict[str, Any]]:
    items = data.get("items", [])
    if include_done:
        return list(items)
    return [item for item in items if item.get("status", "open") != "done"]


def complete_item(
    item_id: str,
    evidence: str,
    path: Path = DEFAULT_TODO_PATH,
) -> dict[str, Any]:
    data = load_todo(path)
    for item in data["items"]:
        if item.get("id") == item_id:
            item["status"] = "done"
            item["evidence"] = evidence
            item["completed_at"] = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
            save_todo(data, path)
            return item
    raise KeyError(f"TODO item not found: {item_id}")


def render_markdown(
    todo_path: Path = DEFAULT_TODO_PATH,
    output_path: Path = DEFAULT_RENDER_PATH,
) -> str:
    data = load_todo(todo_path)
    lines: list[str] = [
        "# TODO",
        "",
        "This file is generated from `.agentic/todo.yaml`.",
        "",
        "## Items",
        "",
    ]

    for item in data["items"]:
        done = item.get("status") == "done"
        marker = "x" if done else " "
        item_id = item.get("id", "UNKNOWN")
        title = item.get("title", "")
        owner = item.get("owner", "unknown")
        priority = item.get("priority", "normal")
        evidence_required = item.get("evidence_required", "")
        evidence = item.get("evidence", "")
        completed_at = item.get("completed_at", "")

        lines.append(f"- [{marker}] **{item_id}** {title}  ")
        lines.append(f"  Owner: {owner}  ")
        lines.append(f"  Priority: {priority}  ")
        if evidence_required:
            lines.append(f"  Evidence required: `{evidence_required}`  ")
        if evidence:
            lines.append(f"  Evidence: `{evidence}`  ")
        if completed_at:
            lines.append(f"  Completed at: `{completed_at}`  ")
        lines.append("")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    text = "\n".join(lines).rstrip() + "\n"
    output_path.write_text(text, encoding="utf-8")
    return text
