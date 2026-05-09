from pathlib import Path
from typing import Any
import yaml


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
