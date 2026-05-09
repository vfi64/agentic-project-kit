from pathlib import Path
from typing import Any
import yaml


STATE_GATE_DOCUMENTS = (
    "docs/STATUS.md",
    "docs/TEST_GATES.md",
    "docs/handoff/CURRENT_HANDOFF.md",
)

STATE_GATE_SECTIONS = {
    "docs/STATUS.md": ("## Current Goal", "## Next Safe Step"),
    "docs/TEST_GATES.md": ("## Gate Matrix", "## Outcome Reporting"),
    "docs/handoff/CURRENT_HANDOFF.md": ("# Current Handoff", "## Current", "## Next"),
}

STALE_HANDOFF_MARKERS = (
    "Create project-level docs",
    "Commit documentation-state files",
    "Run the local gate, inspect the diff, then commit the documentation-state update",
)


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Missing config file: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"YAML root must be a mapping: {path}")
    return data


def count_words(text: str) -> int:
    return len(text.split())


def check_docs(project_root: Path) -> list[str]:
    config = load_yaml(project_root / "sentinel.yaml")
    errors: list[str] = []

    for doc in config.get("documents", []):
        path = project_root / doc["path"]
        if not path.exists():
            errors.append(f"Missing document: {doc['path']}")
            continue

        content = path.read_text(encoding="utf-8")
        for section in doc.get("required_sections", []):
            if section not in content:
                errors.append(f"{doc['path']}: missing required section {section!r}")

        max_words = doc.get("max_words")
        if max_words is not None:
            words = count_words(content)
            if words > int(max_words):
                errors.append(f"{doc['path']}: too long ({words}/{max_words} words)")

        min_words = doc.get("min_words")
        if min_words is not None:
            words = count_words(content)
            if words < int(min_words):
                errors.append(f"{doc['path']}: too short ({words}/{min_words} words)")

    errors.extend(check_state_gate_docs(project_root))
    return errors


def check_state_gate_docs(project_root: Path) -> list[str]:
    errors: list[str] = []

    for relative_path in STATE_GATE_DOCUMENTS:
        path = project_root / relative_path
        if not path.exists():
            errors.append(f"Missing state gate document: {relative_path}")
            continue

        content = path.read_text(encoding="utf-8")
        for section in STATE_GATE_SECTIONS.get(relative_path, ()):  # defensive for future docs
            if section not in content:
                errors.append(f"{relative_path}: missing state gate section {section!r}")

    handoff_path = project_root / "docs/handoff/CURRENT_HANDOFF.md"
    if handoff_path.exists():
        handoff = handoff_path.read_text(encoding="utf-8")
        for marker in STALE_HANDOFF_MARKERS:
            if marker in handoff:
                errors.append(f"docs/handoff/CURRENT_HANDOFF.md: stale handoff marker {marker!r}")

    return errors


def check_todo(project_root: Path) -> list[str]:
    config = load_yaml(project_root / "sentinel.yaml")
    todo_path = project_root / config.get("todo", {}).get("path", ".agentic/todo.yaml")
    data = load_yaml(todo_path)
    errors: list[str] = []

    items = data.get("items", [])
    if not isinstance(items, list):
        return [f"{todo_path}: items must be a list"]

    required = ["id", "title", "owner", "priority", "status", "evidence_required"]
    seen_ids: set[str] = set()

    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            errors.append(f"{todo_path}: item {index} must be a mapping")
            continue

        item_id = str(item.get("id", "")).strip()
        if not item_id:
            errors.append(f"{todo_path}: item {index} has no id")
        elif item_id in seen_ids:
            errors.append(f"{todo_path}: duplicate id {item_id}")
        else:
            seen_ids.add(item_id)

        for field in required:
            if not str(item.get(field, "")).strip():
                errors.append(f"{todo_path}: {item_id or index} missing {field}")

        if str(item.get("status", "")).strip() not in {"open", "done", "blocked"}:
            errors.append(f"{todo_path}: {item_id or index} has invalid status")

    return errors


def check_all(project_root: Path) -> list[str]:
    errors: list[str] = []
    errors.extend(check_docs(project_root))
    errors.extend(check_todo(project_root))
    return errors
