from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

MANDATORY_BOOT_SOURCES = (
    ".agentic/compiled_agent_context.yaml",
    ".agentic/handoff_state.yaml",
    ".agentic/rule_mechanism_inventory.yaml",
    ".agentic/rule_migrations.yaml",
    ".agentic/rule_preservation.yaml",
    "docs/STATUS.md",
    "docs/handoff/CURRENT_HANDOFF.md",
    "docs/governance/FINAL_SUMMARY_CONTRACT.md",
    "docs/governance/CHAT_COMMUNICATION_CONTRACT.md",
    "docs/governance/PORTABLE_CHAT_EXECUTION_CONTRACT.md",
    "docs/governance/CHAT_BOOTSTRAP_AND_DRIFT_CONTRACT.md",
    "docs/planning/RULE_REGISTRY_IMPROVEMENT_PLAN.md",
    "docs/planning/WORKFLOW_REDUCTION_FOCUS.md",
)

BOOTLOADER_RULES = (
    "Start from repository artifacts instead of chat memory.",
    "Read mandatory boot sources before repository changes.",
    "Prefer Python runners for local workflow execution; shell remains a thin adapter.",
    "Use run_summary_renderer for final summaries in evidence-bearing workflows.",
    "Treat d, f, and w as communication signals rather than evidence.",
    "Inspect repo or remote evidence before requesting pasted terminal output.",
    "Use protected change planning before protected YAML, JSON, or Markdown control changes.",
)


@dataclass(frozen=True)
class BootCheckResult:
    source: str
    exists: bool


def check_boot_sources(root: Path | str = ".") -> tuple[BootCheckResult, ...]:
    root_path = Path(root)
    return tuple(BootCheckResult(source, (root_path / source).exists()) for source in MANDATORY_BOOT_SOURCES)


def render_bootloader(root: Path | str = ".") -> str:
    checks = check_boot_sources(root)
    lines = [
        "CHAT_BOOTLOADER",
        "",
        "Purpose: bootstrap a successor chat from repository truth.",
        "",
        "Mandatory boot sources:",
    ]
    for check in checks:
        state = "present" if check.exists else "missing"
        lines.append(f"- [{state}] {check.source}")
    lines.extend(["", "Mandatory workflow rules:"])
    for rule in BOOTLOADER_RULES:
        lines.append(f"- {rule}")
    lines.extend(
        [
            "",
            "Required first action in a successor chat:",
            "- Read these sources and verify main, open PRs, CI, STATUS, handoff, rule registry, and final-summary contracts before repository changes.",
            "",
            "### RESULT: PASS ###",
        ]
    )
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="chat-bootloader")
    parser.add_argument("--root", default=".")
    parser.add_argument("--check", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    print(render_bootloader(args.root))
    if args.check:
        missing = [item.source for item in check_boot_sources(args.root) if not item.exists]
        return 1 if missing else 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
