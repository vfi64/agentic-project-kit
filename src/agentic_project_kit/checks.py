from pathlib import Path
from typing import Any
import re
import yaml


STATE_GATE_DOCUMENTS = (
    "docs/STATUS.md",
    "docs/TEST_GATES.md",
    "docs/handoff/CURRENT_HANDOFF.md",
    "docs/architecture/ARCHITECTURE_CONTRACT.md",
    "docs/DOCUMENTATION_COVERAGE.yaml",
)

STATE_GATE_SECTIONS = {
    "docs/STATUS.md": ("## Current Goal", "## Next Safe Step"),
    "docs/TEST_GATES.md": ("## Gate Matrix", "## Outcome Reporting"),
    "docs/handoff/CURRENT_HANDOFF.md": ("# Current Handoff", "## Current", "## Next"),
    "docs/architecture/ARCHITECTURE_CONTRACT.md": (
        "## 1. Executive Summary",
        "## 2. How to Use This Document",
        "## 4. Decision Rules",
        "## 7. Architectural Contract",
        "## 17. Acceptance Criteria for Future Work",
    ),
}

STALE_HANDOFF_MARKERS = (
    "Create project-level docs",
    "Commit documentation-state files",
    "Run the local gate, inspect the diff, then commit the documentation-state update",
)

QUALITY_PLACEHOLDER_PATTERNS = {
    "TODO": re.compile(r"(^|[\s\[{(<])TODO([\s\]}>)?:-]|$)"),
    "TBD": re.compile(r"(^|[\s\[{(<])TBD([\s\]}>)?:-]|$)"),
    "FIXME": re.compile(r"(^|[\s\[{(<])FIXME([\s\]}>)?:-]|$)"),
    "Lorem ipsum": re.compile(r"Lorem ipsum", re.IGNORECASE),
    "coming soon": re.compile(r"coming soon", re.IGNORECASE),
    "to be written": re.compile(r"to be written", re.IGNORECASE),
    "to be defined": re.compile(r"to be defined", re.IGNORECASE),
    "placeholder marker": re.compile(r"placeholder\s+(text|section|content|value)", re.IGNORECASE),
}


SEMANTIC_QUALITY_BOUNDARY = (
    "Deterministic checks can detect placeholders, stale markers, coverage gaps, "
    "and structural drift. They cannot prove semantic perfection. LLM review, "
    "if added later, must remain advisory and separate from hard doctor gates."
)


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Missing config file: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"YAML root must be a mapping: {path}")
    return data


def load_optional_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return load_yaml(path)


def count_words(text: str) -> int:
    return len(text.split())


def check_docs(project_root: Path) -> list[str]:
    config = load_optional_yaml(project_root / "sentinel.yaml")
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

        if bool(doc.get("quality_checks", True)):
            errors.extend(check_document_quality(doc["path"], content))

    errors.extend(check_state_gate_docs(project_root))
    errors.extend(check_documentation_coverage(project_root))
    return errors


def check_document_quality(relative_path: str, content: str) -> list[str]:
    """Return deterministic document-quality findings.

    These checks intentionally cover only machine-checkable quality signals.
    They are not a claim of semantic perfection.
    """
    errors: list[str] = []
    for marker, pattern in QUALITY_PLACEHOLDER_PATTERNS.items():
        if pattern.search(content):
            errors.append(f"{relative_path}: unresolved placeholder marker {marker!r}")
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


def check_documentation_coverage(project_root: Path) -> list[str]:
    matrix_path = project_root / "docs/DOCUMENTATION_COVERAGE.yaml"
    if not matrix_path.exists():
        return ["Missing state gate document: docs/DOCUMENTATION_COVERAGE.yaml"]

    try:
        matrix = load_yaml(matrix_path)
    except (FileNotFoundError, ValueError, yaml.YAMLError) as exc:
        return [f"docs/DOCUMENTATION_COVERAGE.yaml: invalid coverage matrix ({exc})"]

    errors: list[str] = []
    rules = matrix.get("rules", [])
    if not isinstance(rules, list) or not rules:
        return ["docs/DOCUMENTATION_COVERAGE.yaml: rules must be a non-empty list"]

    for rule_index, rule in enumerate(rules, start=1):
        if not isinstance(rule, dict):
            errors.append(f"docs/DOCUMENTATION_COVERAGE.yaml: rule {rule_index} must be a mapping")
            continue
        rule_id = str(rule.get("id") or f"rule-{rule_index}")
        documents = rule.get("documents", [])
        if not isinstance(documents, list) or not documents:
            errors.append(f"docs/DOCUMENTATION_COVERAGE.yaml: {rule_id} documents must be a non-empty list")
            continue

        for doc_index, doc in enumerate(documents, start=1):
            if not isinstance(doc, dict):
                errors.append(f"docs/DOCUMENTATION_COVERAGE.yaml: {rule_id} document {doc_index} must be a mapping")
                continue
            relative_path = str(doc.get("path") or "").strip()
            if not relative_path:
                errors.append(f"docs/DOCUMENTATION_COVERAGE.yaml: {rule_id} document {doc_index} missing path")
                continue
            path = project_root / relative_path
            if not path.exists():
                errors.append(f"documentation coverage {rule_id}: missing document {relative_path}")
                continue

            terms = doc.get("terms", [])
            if not isinstance(terms, list) or not terms:
                errors.append(f"docs/DOCUMENTATION_COVERAGE.yaml: {rule_id} {relative_path} terms must be a non-empty list")
                continue

            content = path.read_text(encoding="utf-8")
            for term in terms:
                needle = str(term)
                if needle not in content:
                    errors.append(f"documentation coverage {rule_id}: {relative_path} missing term {needle!r}")

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
