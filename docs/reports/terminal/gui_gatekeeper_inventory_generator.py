#!/usr/bin/env python3
"""Generate the GUI gatekeeper implementation inventory.

Repository-local inspection tooling. It performs no product-code mutation and
writes only planning/report artifacts.
"""

from __future__ import annotations

import sys
import traceback
from dataclasses import dataclass
from pathlib import Path

ROOTS = [
    Path("src"),
    Path("tests"),
    Path("docs/planning"),
    Path("docs/governance"),
    Path("docs/handoff"),
]

MATCH_TERMS = (
    "gui", "tkinter", "cockpit", "action", "work", "order", "evidence",
    "handoff", "summary", "gatekeeper", "upload", "merge", "freshness",
    "classifier", "preflight",
)

EXCLUDED_PARTS = {"__pycache__"}
EXCLUDED_SUFFIXES = {".pyc"}

INVENTORY_PATH = Path("docs/reports/terminal/gui-gatekeeper-inventory-files.txt")
MARKDOWN_PATH = Path("docs/planning/GUI_GATEKEEPER_IMPLEMENTATION_INVENTORY.md")
LOG_PATH = Path("docs/reports/terminal/gui-gatekeeper-inventory-generation.log")

AREA_RULES = [
    ("Result/log classification", ("result_report_classifier", "run_summary", "workflow_summary_runner")),
    ("Summary validation", ("FINAL_SUMMARY", "final_summary", "run_summary")),
    ("Evidence/upload preflight", ("evidence", "upload", "patch_artifact_preflight")),
    ("Work-order routing", ("work_order", "work_orders", "typed_work_order")),
    ("Action registry / cockpit", ("action_registry", "action_specs", "cockpit")),
    ("GUI display layer", ("gui_", "TKINTER", "GUI_COCKPIT", "TKINTER_WORKBENCH")),
    ("Handoff freshness", ("handoff", "freshness", "state_freshness")),
    ("PR/merge readiness", ("merge", "MERGE_READINESS")),
    ("Shell-adapter migration", ("ns", "shell", "runner")),
    ("Tests", ("tests/",)),
]


@dataclass(frozen=True)
class Classification:
    areas: dict[str, list[str]]
    unclassified: list[str]


def is_relevant_file(path: Path) -> bool:
    text = str(path).replace("\\", "/")
    lower = text.lower()
    if any(part in EXCLUDED_PARTS for part in path.parts):
        return False
    if path.suffix in EXCLUDED_SUFFIXES:
        return False
    return any(term in lower for term in MATCH_TERMS)


def collect_files() -> list[str]:
    files: list[str] = []
    for root in ROOTS:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if path.is_file() and is_relevant_file(path):
                files.append(str(path).replace("\\", "/"))
    return sorted(dict.fromkeys(files))


def classify(files: list[str]) -> Classification:
    used: set[str] = set()
    areas: dict[str, list[str]] = {}
    for area, terms in AREA_RULES:
        selected: list[str] = []
        for file in files:
            lower = file.lower()
            if file in used:
                continue
            if any(term.lower() in lower for term in terms):
                selected.append(file)
                used.add(file)
        areas[area] = selected
    return Classification(areas=areas, unclassified=[file for file in files if file not in used])


def render_markdown(files: list[str], classification: Classification) -> str:
    lines: list[str] = [
        "# GUI Gatekeeper Implementation Inventory",
        "",
        "Status: draft",
        "Scope: read-only inventory; no product-code changes.",
        "Baseline: post-PR882 main after post-PR880/PR881 bootstrap refresh.",
        "",
        "## Purpose",
        "",
        "This document maps the implementation surface for the GUI deterministic gatekeeper migration before product-code changes start.",
        "",
        "## Current inventory",
        "",
    ]
    lines.extend(f"- {file}" for file in files)
    lines.extend(["", "## Initial gatekeeper area classification", ""])
    for area, selected in classification.areas.items():
        lines.extend([f"### {area}", ""])
        lines.extend(f"- {file}" for file in selected) if selected else lines.append("- none found in this inspection")
        lines.append("")
    lines.extend(["### Unclassified / review required", ""])
    lines.extend(f"- {file}" for file in classification.unclassified) if classification.unclassified else lines.append("- none")
    lines.extend([
        "",
        "## Required follow-up classification",
        "",
        "The next slice must refine this inventory into deterministic implementation targets for result/log classification, summary validation, upload/evidence preflight, work-order routing, action registry, GUI display, handoff freshness, PR/merge readiness, and shell-adapter migration.",
        "",
        "## Standard failure modes to cover",
        "",
        "- Long manual shell blocks, heredocs, and risky multiline quote states must not be normal evidence-bearing workflows.",
        "- Remote-tool failure must not fall back to manual long shell copy/paste.",
        "- Terminal-to-LLM evidence should flow through repo-readable logs, not manual transcript paste.",
        "- LLM-to-terminal execution should flow through repo-backed work orders or registered actions, not ad-hoc shell blocks.",
        "- Administrative handoff/refresh merges must not create handoff freshness drift through unsupported custom merge subjects.",
        "- Shell quoting must not allow Markdown/code markers such as backticks to disappear through command substitution.",
        "",
        "## Non-goals",
        "",
        "- No GUI execution changes in this inventory slice.",
        "- No upload behavior changes in this inventory slice.",
        "- No merge automation changes in this inventory slice.",
        "- No removal of ./ns in this inventory slice.",
        "",
    ])
    return "\n".join(lines)


def validate(files: list[str], markdown: str, classification: Classification) -> list[str]:
    errors: list[str] = []
    if not files:
        errors.append("inventory is empty")
    bad_files = [file for file in files if "__pycache__" in file or file.endswith(".pyc") or not file.strip()]
    if bad_files:
        errors.append(f"inventory contains excluded or empty paths: {bad_files[:5]}")
    if "\n- \n" in markdown or markdown.endswith("\n- \n"):
        errors.append("markdown contains empty bullet points")
    for section in ["## Current inventory", "## Initial gatekeeper area classification", "## Standard failure modes to cover", "## Non-goals"]:
        if section not in markdown:
            errors.append(f"missing section: {section}")
    non_empty_areas = sum(1 for selected in classification.areas.values() if selected)
    if non_empty_areas < 5:
        errors.append(f"too few classified areas have entries: {non_empty_areas}")
    return errors


def main() -> int:
    try:
        files = collect_files()
        classification = classify(files)
        markdown = render_markdown(files, classification)
        errors = validate(files, markdown, classification)
        INVENTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
        MARKDOWN_PATH.parent.mkdir(parents=True, exist_ok=True)
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        INVENTORY_PATH.write_text("\n".join(files) + "\n", encoding="utf-8")
        MARKDOWN_PATH.write_text(markdown, encoding="utf-8")
        log_lines = [
            "GUI_GATEKEEPER_INVENTORY_GENERATION",
            f"inventory_path={INVENTORY_PATH}",
            f"markdown_path={MARKDOWN_PATH}",
            f"files={len(files)}",
            f"classified_areas_with_entries={sum(1 for selected in classification.areas.values() if selected)}",
            f"unclassified={len(classification.unclassified)}",
        ]
        if errors:
            log_lines.append("result=FAIL")
            log_lines.extend(f"error={error}" for error in errors)
            LOG_PATH.write_text("\n".join(log_lines) + "\n", encoding="utf-8")
            print("\n".join(log_lines))
            return 1
        log_lines.append("result=PASS")
        LOG_PATH.write_text("\n".join(log_lines) + "\n", encoding="utf-8")
        print("\n".join(log_lines))
        return 0
    except Exception:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        detail = traceback.format_exc()
        LOG_PATH.write_text("GUI_GATEKEEPER_INVENTORY_GENERATION\nresult=FAIL\n" + detail, encoding="utf-8")
        print(detail, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
