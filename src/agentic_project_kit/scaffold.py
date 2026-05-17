from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re


ALLOWED_STATUSES = {"active", "idea-note", "implemented", "superseded"}


@dataclass(frozen=True)
class PlanningDocSpec:
    title: str
    status: str
    decision_status: str
    scope: str
    review_policy: str


def slugify_title(title: str) -> str:
    text = title.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text or "planning-doc"


def planning_doc_path(root: Path, title: str, directory: str = "docs/planning") -> Path:
    stem = slugify_title(title).upper().replace("-", "_")
    return root.resolve() / directory / f"{stem}.md"


def render_planning_doc(spec: PlanningDocSpec) -> str:
    if spec.status not in ALLOWED_STATUSES:
        allowed = ", ".join(sorted(ALLOWED_STATUSES))
        raise ValueError(f"invalid status: {spec.status}; allowed: {allowed}")
    lines = [
        f"# {spec.title}",
        "",
        f"Status: {spec.status}",
        f"Decision status: {spec.decision_status}",
        f"Scope: {spec.scope}",
        f"Review policy: {spec.review_policy}",
        "",
        "## Purpose",
        "",
        "TODO: describe the purpose of this governed planning document.",
        "",
        "## Context",
        "",
        "TODO: summarize the relevant repository state and constraints.",
        "",
        "## Plan",
        "",
        "TODO: define the planned work in small, reviewable slices.",
        "",
        "## Evidence",
        "",
        "TODO: list required gates, tests, review points, or audit evidence.",
        "",
    ]
    return "\n".join(lines)


def write_planning_doc(path: Path, spec: PlanningDocSpec, overwrite: bool = False) -> Path:
    target = path.resolve()
    if target.exists() and not overwrite:
        raise FileExistsError(f"refusing to overwrite existing planning document: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render_planning_doc(spec), encoding="utf-8")
    return target
