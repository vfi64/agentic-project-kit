from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import argparse
import re
import sys

PROTECTED_FILES = {
    ".agentic/compiled_agent_context.yaml",
    ".agentic/handoff_state.yaml",
    ".agentic/control_file_preservation.yaml",
    ".agentic/rule_mechanism_inventory.yaml",
    "docs/DOCUMENTATION_REGISTRY.yaml",
    "docs/governance/FINAL_SUMMARY_CONTRACT.md",
    "docs/governance/PROTECTED_CONTROL_FILE_CHANGE_CONTRACT.md",
}

VALID_DECISIONS = {"keep", "migrate", "obsolete", "abort"}
LARGE_PROTECTED_REMOVAL_THRESHOLD = 20

GENERATED_ARTIFACTS = {
    "docs/handoff/NEXT_CHAT_BOOTSTRAP.md": (
        "src/agentic_project_kit/successor_handoff_package.py",
        "src/agentic_project_kit/chat_bootloader.py",
        "src/agentic_project_kit/operational_handoff_projection.py",
        ".agentic/operational_handoff_state.yaml",
    ),
}

SUCCESSOR_HANDOFF_PROJECTION_BUNDLE = {
    "docs/reports/handoff-packages/latest/execution_contract.json",
    "docs/reports/handoff-packages/latest/successor_context.yaml",
    "docs/reports/handoff-packages/latest/successor_prompt.md",
    "docs/reports/handoff-packages/latest/validation_report.json",
}

ANCHORS = {
    ".agentic/compiled_agent_context.yaml": {"hard_rules", "final_summary_contract", "communication_rules", "normal_operator_path"},
    ".agentic/handoff_state.yaml": {"safe_state", "release", "recent_failure_patterns"},
    ".agentic/rule_mechanism_inventory.yaml": {"mechanisms"},
    "docs/DOCUMENTATION_REGISTRY.yaml": {"documents"},
    "docs/governance/FINAL_SUMMARY_CONTRACT.md": {"WORK RESULT", "OVERALL RESULT", "NEXT_CHAT_REPLY"},
    "docs/governance/PROTECTED_CONTROL_FILE_CHANGE_CONTRACT.md": {"migration record", "user decision", "protected_control"},
}
YAML_PROTECTED_FILES = {
    ".agentic/compiled_agent_context.yaml",
    ".agentic/handoff_state.yaml",
    ".agentic/control_file_preservation.yaml",
    ".agentic/rule_mechanism_inventory.yaml",
    "docs/DOCUMENTATION_REGISTRY.yaml",
}

@dataclass(frozen=True)
class ProtectedChangeFinding:
    path: str
    severity: str
    code: str
    message: str

def touched_files(diff_text: str) -> set[str]:
    touched: set[str] = set()
    for line in diff_text.splitlines():
        if line.startswith("diff --git "):
            parts = line.split()
            for part in parts[2:]:
                candidate = part[2:] if part.startswith(("a/", "b/")) else part
                touched.add(candidate)
    return touched


def touched_protected_files(diff_text: str) -> set[str]:
    return touched_files(diff_text) & PROTECTED_FILES

def removed_lines_for_path(diff_text: str, path: str) -> list[str]:
    lines: list[str] = []
    active = False
    for line in diff_text.splitlines():
        if line.startswith("diff --git "):
            active = (" a/" + path + " ") in line or (" b/" + path) in line or line.endswith(" " + "b/" + path)
            continue
        if active and line.startswith("-") and not line.startswith("---"):
            lines.append(line[1:])
    return lines

def added_lines_for_path(diff_text: str, path: str) -> list[str]:
    lines: list[str] = []
    active = False
    for line in diff_text.splitlines():
        if line.startswith("diff --git "):
            active = (" a/" + path + " ") in line or (" b/" + path) in line or line.endswith(" " + "b/" + path)
            continue
        if active and line.startswith("+") and not line.startswith("+++"):
            lines.append(line[1:])
    return lines

def _has_valid_decision(path: str, decisions: dict[str, str]) -> bool:
    return decisions.get(path) in VALID_DECISIONS


def _migration_record_decisions(diff_text: str) -> dict[str, str]:
    decisions: dict[str, str] = {}
    added_text = "\n".join(
        line[1:]
        for line in diff_text.splitlines()
        if line.startswith("+") and not line.startswith("+++")
    )
    if "protected_control" not in added_text and "migration record" not in added_text.lower():
        return decisions
    for path in PROTECTED_FILES:
        if path not in added_text:
            continue
        match = re.search(r"(?im)^\s*decision\s*:\s*(keep|migrate|obsolete|abort)\s*$", added_text)
        if match:
            decisions[path] = match.group(1)
    return decisions


def _contains_anchor(path: str, text: str, anchor: str) -> bool:
    if path in YAML_PROTECTED_FILES:
        return re.search(rf"(?m)^\s*{re.escape(anchor)}\s*:", text) is not None
    return anchor in text


def _is_handoff_state_refresh(path: str, added_text: str) -> bool:
    if path != ".agentic/handoff_state.yaml":
        return False
    required_anchors = {"safe_state", "handoff_maintenance", "next_step"}
    candidate_text = added_text
    current_path = Path(path)
    if current_path.exists():
        candidate_text = candidate_text + "\n" + current_path.read_text(encoding="utf-8", errors="replace")
    return (
        "source: agentic-kit handoff refresh" in candidate_text
        and all(_contains_anchor(path, candidate_text, anchor) for anchor in required_anchors)
    )


def _is_successor_handoff_projection_refresh(touched: set[str]) -> bool:
    return SUCCESSOR_HANDOFF_PROJECTION_BUNDLE <= touched


def analyze_diff(diff_text: str, decisions: dict[str, str] | None = None) -> list[ProtectedChangeFinding]:
    decisions = {**_migration_record_decisions(diff_text), **(decisions or {})}
    findings: list[ProtectedChangeFinding] = []
    touched = touched_files(diff_text)
    for path, generator_sources in sorted(GENERATED_ARTIFACTS.items()):
        if (
            path in touched
            and not any(source in touched for source in generator_sources)
            and not _is_successor_handoff_projection_refresh(touched)
        ):
            findings.append(ProtectedChangeFinding(path, "block", "generated-artifact-direct-edit", "generated artifact changed without its generator source; use the generator path instead of direct editing"))
    for path in sorted(touched & PROTECTED_FILES):
        removed = removed_lines_for_path(diff_text, path)
        added = added_lines_for_path(diff_text, path)
        has_valid_decision = _has_valid_decision(path, decisions)
        if len(removed) >= LARGE_PROTECTED_REMOVAL_THRESHOLD and not has_valid_decision:
            added_text = "\n".join(added)
            if len(added) >= LARGE_PROTECTED_REMOVAL_THRESHOLD and _is_handoff_state_refresh(path, added_text):
                pass
            elif len(added) >= LARGE_PROTECTED_REMOVAL_THRESHOLD:
                findings.append(ProtectedChangeFinding(path, "block", "large-protected-file-rewrite-without-decision", "large protected-file rewrite requires keep/migrate/obsolete/abort decision before replacement-style editing"))
            else:
                findings.append(ProtectedChangeFinding(path, "block", "possible-full-replacement-or-large-deletion", "large protected-file deletion requires migration record or user decision"))
        removed_text = "\n".join(removed)
        added_text = "\n".join(added)
        for anchor in ANCHORS.get(path, set()):
            if _contains_anchor(path, removed_text, anchor) and not _contains_anchor(path, added_text, anchor):
                if not has_valid_decision:
                    findings.append(ProtectedChangeFinding(path, "block", "protected-anchor-removal-without-decision", f"anchor {anchor!r} removed without keep/migrate/obsolete/abort decision"))
    return findings

def render_findings(findings: list[ProtectedChangeFinding]) -> str:
    if not findings:
        return "PROTECTED_CHANGE_PLAN\nresult=PASS\nfindings=0\n### RESULT: PASS ###\n"
    out = ["PROTECTED_CHANGE_PLAN", "result=BLOCK", f"findings={len(findings)}"]
    for finding in findings:
        out.append(f"- {finding.severity}:{finding.code}:{finding.path}: {finding.message}")
    out.append("required_decision=keep|migrate|obsolete|abort")
    out.append("### RESULT: FAIL ###")
    return "\n".join(out) + "\n"

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--diff-file", required=True)
    args = parser.parse_args(argv)
    diff_text = Path(args.diff_file).read_text(encoding="utf-8")
    findings = analyze_diff(diff_text)
    sys.stdout.write(render_findings(findings))
    return 1 if findings else 0

if __name__ == "__main__":
    raise SystemExit(main())
