"""Read-only cockpit readiness report."""

from __future__ import annotations

from collections import Counter

from agentic_project_kit.action_registry import SafetyClass, list_actions


def build_cockpit_readiness_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for action in list_actions():
        rows.append(
            {
                "name": action.name,
                "safety_class": action.safety_class.value,
                "mutation_scope": action.mutation_scope,
                "dry_run_supported": action.dry_run_supported,
                "outcome_contract": list(action.outcome_contract),
                "summary": action.summary,
            }
        )
    return rows


def build_cockpit_readiness_summary() -> dict[str, object]:
    rows = build_cockpit_readiness_rows()
    counts = Counter(str(row["safety_class"]) for row in rows)
    missing_outcomes = [str(row["name"]) for row in rows if not row["outcome_contract"]]
    read_only_with_mutation = [
        str(row["name"])
        for row in rows
        if row["safety_class"] == SafetyClass.READ_ONLY.value and row["mutation_scope"] != "none"
    ]
    return {
        "action_count": len(rows),
        "safety_class_counts": dict(sorted(counts.items())),
        "missing_outcomes": missing_outcomes,
        "read_only_with_mutation": read_only_with_mutation,
        "ready_for_read_only_cockpit": not missing_outcomes and not read_only_with_mutation,
    }


def render_cockpit_readiness_markdown() -> str:
    summary = build_cockpit_readiness_summary()
    rows = build_cockpit_readiness_rows()
    lines = [
        "# Cockpit Readiness",
        "",
        "This report is read-only and derived from static action metadata.",
        "",
        "## Summary",
        "",
        f"- Action count: {summary['action_count']}",
        f"- Ready for read-only cockpit: {summary['ready_for_read_only_cockpit']}",
        f"- Missing outcomes: {summary['missing_outcomes']}",
        f"- Read-only actions with mutation scope: {summary['read_only_with_mutation']}",
        "",
        "## Actions",
        "",
        "| Action | Safety class | Mutation scope | Dry-run | Outcomes |",
        "|---|---|---|---|---|",
    ]
    for row in rows:
        outcomes = ", ".join(str(item) for item in row["outcome_contract"])
        lines.append(f"| `{row['name']}` | {row['safety_class']} | {row['mutation_scope']} | {row['dry_run_supported']} | {outcomes} |")
    return "\n".join(lines) + "\n"
