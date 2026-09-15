from __future__ import annotations

from pathlib import Path
from typing import Any


def canonical_fact_findings(
    project_root: Path,
    registry: dict[str, Any],
) -> tuple[list[str], list[dict[str, str]]]:
    """Validate registry-owned facts and report projection drift."""
    facts = registry.get("canonical_facts", [])
    errors: list[str] = []
    findings: list[dict[str, str]] = []
    if facts is None:
        return errors, findings
    if not isinstance(facts, list):
        return ["documentation registry canonical_facts must be a list"], findings

    seen_ids: set[str] = set()
    for index, fact in enumerate(facts):
        prefix = f"canonical_facts[{index}]"
        if not isinstance(fact, dict):
            errors.append(f"{prefix} must be a mapping")
            continue
        fact_id = str(fact.get("id", "")).strip()
        value = fact.get("value")
        if not fact_id:
            errors.append(f"{prefix}.id must be a non-empty string")
            continue
        if fact_id in seen_ids:
            errors.append(f"duplicate canonical fact id: {fact_id}")
        seen_ids.add(fact_id)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{prefix}.value must be a non-empty string")
            continue
        for field in ("managed_paths", "review_paths"):
            paths = fact.get(field, [])
            if not isinstance(paths, list):
                errors.append(f"{prefix}.{field} must be a list")
                continue
            invalid = any(
                not isinstance(path, str)
                or not path.strip()
                or Path(path).is_absolute()
                or ".." in Path(path).parts
                for path in paths
            )
            if invalid:
                errors.append(f"{prefix}.{field} must contain only relative paths")
                continue
            for path_text in paths:
                path = project_root / path_text
                if not path.exists():
                    errors.append(f"{prefix}.{field}: missing path {path_text}")
                    continue
                content = path.read_text(encoding="utf-8")
                if value not in content:
                    severity = "BLOCK" if field == "managed_paths" else "WARN"
                    message = f"canonical fact {fact_id!r} is missing from {path_text}"
                    findings.append(
                        {
                            "severity": severity,
                            "kind": "canonical_fact_projection_drift",
                            "path": path_text,
                            "message": message,
                            "next_action": (
                                "Refresh the managed projection from the documentation registry."
                                if severity == "BLOCK"
                                else "Review project-owned prose against the canonical fact."
                            ),
                        }
                    )
                    if severity == "BLOCK":
                        errors.append(message)
    return errors, findings
