from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

DEFAULT_BOOTSTRAP_PATH = Path("docs/handoff/NEXT_CHAT_BOOTSTRAP.md")

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

NEXT_WORK_ITEMS = (
    "Finish local sync after the bootloader/summary-runner merge.",
    "Use boot write to refresh docs/handoff/NEXT_CHAT_BOOTSTRAP.md before chat changes.",
    "Harden no-op/PASS_ALREADY_DONE handling for already satisfied target states.",
    "Harden d/f semantics through repo evidence instead of chat discipline.",
    "Automate red CI failed-log diagnosis in the repo workflow path.",
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


def render_next_chat_bootstrap(root: Path | str = ".") -> str:
    bootloader_text = render_bootloader(root)
    lines = [
        "# NEXT CHAT BOOTSTRAP",
        "",
        "This file is the canonical remote handoff entry point for a successor chat.",
        "Do not start from chat memory. Read this file first, then follow its boot sequence.",
        "",
        "## Standard successor-chat prompt",
        "",
        "Copy this into the next chat:",
        "",
        "```text",
        "We work in repo vfi64/agentic-project-kit. Do not start from chat memory.",
        "Read the remote file docs/handoff/NEXT_CHAT_BOOTSTRAP.md on main completely and execute its boot routine.",
        "After that, verify main, open PRs, CI, STATUS, CURRENT_HANDOFF, handoff_state, compiled_agent_context, rule registry files, document-management rules, and FINAL_SUMMARY_CONTRACT before any mutation.",
        "```",
        "",
        "## First chat command",
        "",
        "1. Read this file completely from remote main.",
        "2. Run or verify `agentic-kit boot check` and `agentic-kit boot prompt` if a local checkout is available.",
        "3. Open every mandatory boot source listed below before repository mutation.",
        "4. Report current main HEAD, open PRs, CI status, last clean evidence, and next smallest safe slice.",
        "",
        "## Bootloader output",
        "",
        "```text",
        bootloader_text,
        "```",
        "",
        "## Next work items",
        "",
    ]
    lines.extend(f"- {item}" for item in NEXT_WORK_ITEMS)
    lines.extend(
        [
            "",
            "## Final summary requirement",
            "",
            "Evidence-bearing workflow outputs must use `agentic_project_kit.run_summary_renderer.SummaryPayload` or the Python workflow summary runner. Do not hand-write legacy final summaries.",
            "",
            "### RESULT: PASS ###",
            "",
        ]
    )
    return "\n".join(lines)


def write_next_chat_bootstrap(path: Path | str = DEFAULT_BOOTSTRAP_PATH, root: Path | str = ".") -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_next_chat_bootstrap(root), encoding="utf-8")
    return output_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="chat-bootloader")
    parser.add_argument("--root", default=".")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--path", default=str(DEFAULT_BOOTSTRAP_PATH))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.write:
        output_path = write_next_chat_bootstrap(args.path, args.root)
        print(f"WROTE {output_path}")
    else:
        print(render_bootloader(args.root))
    if args.check:
        missing = [item.source for item in check_boot_sources(args.root) if not item.exists]
        return 1 if missing else 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
