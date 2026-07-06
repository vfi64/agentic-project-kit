from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any

ALLOWED_COMMAND_CATEGORIES: tuple[str, ...] = (
    "core",
    "transfer",
    "audit",
    "release",
    "handoff",
    "gui-readiness",
    "diagnostic",
    "docs",
    "workflow",
    "governance",
    "state",
    "work-order",
    "advanced/internal",
)

COMMAND_REFERENCE_PATH = Path("docs/reference/agentic-kit-commands.json")


@dataclass(frozen=True)
class CommandTaxonomyEntry:
    qualified_name: str
    group: str
    category: str
    role: str
    composition_level: str
    recommendation_weight: int

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class CommandTaxonomyReport:
    command_count: int
    entries: tuple[CommandTaxonomyEntry, ...]
    findings: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return not self.findings

    @property
    def status(self) -> str:
        return "PASS" if self.ok else "FAIL"

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "kind": "command_taxonomy_report",
            "status": self.status,
            "command_count": self.command_count,
            "category_count": len({entry.category for entry in self.entries}),
            "findings": list(self.findings),
            "entries": [entry.as_dict() for entry in self.entries],
        }


def load_command_reference(project_root: Path) -> list[dict[str, Any]]:
    path = project_root / COMMAND_REFERENCE_PATH
    data = json.loads(path.read_text(encoding="utf-8"))
    commands = data.get("commands") if isinstance(data, dict) else data
    if not isinstance(commands, list):
        raise ValueError(f"Unsupported command reference shape in {path}")
    return [command for command in commands if isinstance(command, dict)]


def classify_command(command: dict[str, Any]) -> CommandTaxonomyEntry:
    qualified = str(command.get("qualified_name") or command.get("name") or "")
    group = str(command.get("group") or "")
    path = command.get("path")
    path_parts = tuple(str(part) for part in path) if isinstance(path, list) else ()
    leaf = path_parts[-1] if path_parts else qualified.rsplit(" ", 1)[-1]

    category = _category_for(group, leaf, qualified)
    composition_level = _composition_level_for(group, leaf, qualified)
    recommendation_weight = _recommendation_weight_for(category, composition_level, qualified)
    role = _role_for(category, leaf, qualified, composition_level=composition_level)
    return CommandTaxonomyEntry(
        qualified_name=qualified,
        group=group,
        category=category,
        role=role,
        composition_level=composition_level,
        recommendation_weight=recommendation_weight,
    )


def _category_for(group: str, leaf: str, qualified: str) -> str:
    if group == "transfer" or qualified.startswith("agentic-kit transfer "):
        return "transfer"
    if group in {"handoff", "boot"} or "handoff" in qualified:
        return "handoff"
    if group in {"rules", "rule-registry", "governance"}:
        return "governance"
    if group in {"workflow", "workflow-guard"}:
        return "workflow"
    if group == "state":
        return "state"
    if group == "work-order":
        return "work-order"
    if group == "workspace":
        return "core"
    if group in {"evidence", "actions", "patterns", "pass-already-done", "dev"}:
        return "advanced/internal"
    if group == "todo":
        return "core"
    if group == "cockpit":
        return "gui-readiness"

    if leaf.startswith("audit-") or leaf.endswith("-audit"):
        return "audit"
    if group == "direction":
        return "docs"
    if leaf in {"docs-audit", "docs-registry", "doc-mesh-repair", "project-direction"} or leaf.startswith("doc-"):
        return "docs"
    if leaf in {"release-publish", "release-prep", "post-release-check", "release-metadata-authority-gate"}:
        return "release"
    if leaf == "gui-readiness-gate":
        return "gui-readiness"
    if leaf in {"doctor", "check", "check-docs", "check-todo", "standard-gates-audit-suite", "command-taxonomy-check", "patch-preflight", "patch-scope-preflight"}:
        return "diagnostic"
    if group in {"root", "scaffold"}:
        return "core"
    return "advanced/internal"


PREFERRED_COMPOSITE_COMMANDS: tuple[str, ...] = (
    "agentic-kit transfer pr-closeout-complete",
    "agentic-kit transfer post-merge-complete",
    "agentic-kit transfer pr-create-complete",
    "agentic-kit work start",
    "agentic-kit work check",
    "agentic-kit work finish",
    "agentic-kit work recover",
    "agentic-kit release ready",
    "agentic-kit release prepare",
    "agentic-kit release-publish",
)


def _composition_level_for(group: str, leaf: str, qualified: str) -> str:
    if qualified in PREFERRED_COMPOSITE_COMMANDS:
        return "composite"
    if leaf in {
        "pr-closeout-complete",
        "post-merge-complete",
        "pr-create-complete",
        "patch-cycle-status",
        "standard-gates-audit-suite",
    }:
        return "composite"
    if group in {"actions", "dev", "evidence", "patterns"}:
        return "elementary/internal"
    return "elementary"


def _recommendation_weight_for(category: str, composition_level: str, qualified: str) -> int:
    if qualified == "agentic-kit transfer pr-closeout-complete":
        return 100
    if composition_level == "composite":
        return 90
    if category == "advanced/internal" or composition_level == "elementary/internal":
        return 20
    return 50



def _role_for(category: str, leaf: str, qualified: str, *, composition_level: str = "elementary") -> str:
    if category == "audit":
        return "Runs a focused repository safety or consistency audit."
    if category == "transfer":
        if composition_level == "composite":
            return "Preferred high-level wrapper for guarded transfer or PR lifecycle workflows; LLMs should choose this before low-level commands."
        return "Supports guarded GitHub/local transfer and PR lifecycle workflows."
    if category == "release":
        return "Supports release preparation, verification, or controlled publishing."
    if category == "gui-readiness":
        return "Supports GUI gatekeeper readiness or cockpit workflows."
    if category == "docs":
        return "Maintains documentation coverage, lifecycle, or mesh consistency."
    if category == "diagnostic":
        return "Summarizes health, taxonomy, preflight, or standard gate state."
    if category == "handoff":
        return "Supports successor-chat handoff and bootstrap continuity."
    if category == "governance":
        return "Maintains rules, policy, or governance state."
    if category == "workflow":
        return "Runs workflow planning or guard utilities."
    if category == "state":
        return "Inspects or repairs project state metadata."
    if category == "work-order":
        return "Supports typed work-order execution and validation."
    if category == "advanced/internal":
        return "Advanced or internal helper; not a primary GUI action."
    return f"Classified command: {qualified or leaf}"


def build_command_taxonomy_report(project_root: Path) -> CommandTaxonomyReport:
    commands = load_command_reference(project_root.resolve())
    entries = tuple(classify_command(command) for command in commands)
    findings: list[str] = []

    if not entries:
        findings.append("command reference contains no commands")

    allowed = set(ALLOWED_COMMAND_CATEGORIES)
    for entry in entries:
        if not entry.qualified_name:
            findings.append("command without qualified_name")
        if entry.category not in allowed:
            findings.append(f"{entry.qualified_name}: unsupported category {entry.category}")
        if not entry.role:
            findings.append(f"{entry.qualified_name}: missing role")
        if entry.composition_level not in {"composite", "elementary", "elementary/internal"}:
            findings.append(f"{entry.qualified_name}: unsupported composition level {entry.composition_level}")
        if not 0 <= entry.recommendation_weight <= 100:
            findings.append(f"{entry.qualified_name}: recommendation weight outside 0..100")
        if entry.group == "root" and entry.category == "core" and entry.qualified_name.startswith("agentic-kit audit-"):
            findings.append(f"{entry.qualified_name}: audit command classified as core")

    return CommandTaxonomyReport(
        command_count=len(commands),
        entries=entries,
        findings=tuple(findings),
    )


def render_command_taxonomy_report(report: CommandTaxonomyReport) -> str:
    lines = [
        "COMMAND_TAXONOMY_CHECK",
        f"STATUS={report.status}",
        f"COMMAND_COUNT={report.command_count}",
        f"FINDING_COUNT={len(report.findings)}",
    ]
    by_category: dict[str, int] = {}
    for entry in report.entries:
        by_category[entry.category] = by_category.get(entry.category, 0) + 1
    for category, count in sorted(by_category.items()):
        lines.append(f"CATEGORY={category}|{count}")
    by_level: dict[str, int] = {}
    for entry in report.entries:
        by_level[entry.composition_level] = by_level.get(entry.composition_level, 0) + 1
    for level, count in sorted(by_level.items()):
        lines.append(f"COMPOSITION_LEVEL={level}|{count}")
    for entry in sorted(report.entries, key=lambda item: (-item.recommendation_weight, item.qualified_name))[:12]:
        if entry.recommendation_weight >= 90:
            lines.append(
                f"PREFERRED={entry.qualified_name}|level={entry.composition_level}|weight={entry.recommendation_weight}"
            )
    for finding in report.findings:
        lines.append(f"FINDING={finding}")
    return "\n".join(lines) + "\n"
