from __future__ import annotations

import argparse
import subprocess
from dataclasses import dataclass
from pathlib import Path

from agentic_project_kit.operational_handoff_projection import render_current_operational_handoff_state
from agentic_project_kit.workspace import LEGACY_DEFAULTS, load_workspace

DEFAULT_BOOTSTRAP_PATH = Path(LEGACY_DEFAULTS.handoff_root) / "NEXT_CHAT_BOOTSTRAP.md"
START_PROMPT_PATH = "docs/handoff/START_NEW_CHAT_PROMPT.md"
CLOSEOUT_PROMPT_PATH = "docs/handoff/CLOSEOUT_BEFORE_CHAT_SWITCH_PROMPT.md"
BOOT_REPORT_PATH = Path(LEGACY_DEFAULTS.handoff_root) / "BOOT_REPORT.md"

MANDATORY_BOOT_SOURCES = (
    ".agentic/compiled_agent_context.yaml",
    ".agentic/handoff_state.yaml",
    ".agentic/operational_handoff_state.yaml",
    ".agentic/rule_mechanism_inventory.yaml",
    ".agentic/rule_migrations.yaml",
    ".agentic/rule_preservation.yaml",
    "docs/STATUS.md",
    "docs/handoff/CURRENT_HANDOFF.md",
    "docs/handoff/START_NEW_CHAT_PROMPT.md",
    "docs/handoff/CLOSEOUT_BEFORE_CHAT_SWITCH_PROMPT.md",
    "docs/governance/FINAL_SUMMARY_CONTRACT.md",
    "docs/governance/CHAT_COMMUNICATION_CONTRACT.md",
    "docs/governance/PORTABLE_CHAT_EXECUTION_CONTRACT.md",
    "docs/governance/CHAT_BOOTSTRAP_AND_DRIFT_CONTRACT.md",
    "docs/DOCUMENTATION_REGISTRY.yaml",
    "docs/planning/PROJECT_DIRECTION.yaml",
)

BOOTLOADER_RULES = (
    "Start from repository artifacts instead of chat memory.",
    "Read mandatory boot sources before repository changes.",
    "Prefer Python runners for local workflow execution; shell remains a thin adapter.",
    "Use run_summary_renderer for final summaries in evidence-bearing workflows.",
    "Evidence-bearing local workflow finalization must use `agentic-kit evidence finalize-log` or a stricter successor. Freehand final PASS footers are not valid closeout evidence.",
    "Treat d, f, and w as communication signals rather than evidence.",
    "Run `agentic-kit evidence inspect --require-summary` or inspect equivalent remote/repo evidence before continuing after chat control signals.",
    "Inspect repo or remote evidence before requesting pasted terminal output.",
    (
        "Use the supported protected-change planning route before protected YAML, JSON, "
        "or Markdown control changes: `./ns protected-change-plan --diff-file <file>` "
        "or `python -m agentic_project_kit.protected_change_planner --diff-file <file>`. "
        "Do not use `agentic-kit protected-change-plan`; that package CLI command is not "
        "registered."
    ),
    "Before a chat switch, run the closeout prompt and check whether START_NEW_CHAT_PROMPT.md, CLOSEOUT_BEFORE_CHAT_SWITCH_PROMPT.md, and NEXT_CHAT_BOOTSTRAP.md all need updates.",
)

def current_operational_handoff_state(root: Path | str = ".") -> tuple[str, ...]:
    return render_current_operational_handoff_state(root)

NEXT_WORK_ITEMS = (
    "Finish local sync after the bootloader/summary-runner merge and verify boot write/check plus targeted tests.",
    "Use boot write to refresh docs/handoff/NEXT_CHAT_BOOTSTRAP.md before chat changes.",
    "Harden no-op/PASS_ALREADY_DONE handling for already satisfied target states.",
    "Use `agentic-kit evidence inspect --require-summary` after chat control signals so d/f/w do not rely on chat memory.",
    "Use `agentic-kit evidence finalize-log` for evidence-bearing local workflow closeout so invalid summary fields cannot still end in a freehand final PASS.",
    "Automate red CI failed-log diagnosis in the repo workflow path.",
    "Resume Rule Registry Phase A only in small PRs: typed schema, generated projections, stronger assertions, query/impact analysis, and documentation integration.",
    "Continue the document-management projection system: move operative truth into machine-readable sources and keep Markdown as generated or verified projection where possible.",
    "Postpone GUI work until the workflow kernel, no-op handling, evidence inspection, and red-CI diagnosis are stable.",
)


@dataclass(frozen=True)
class BootCheckResult:
    source: str
    exists: bool


def _run_git(args: list[str], root: Path) -> str:
    completed = subprocess.run(["git", *args], cwd=root, text=True, capture_output=True, check=False)
    return completed.stdout.strip() if completed.returncode == 0 else "UNKNOWN"


def current_git_head(root: Path | str = ".") -> str:
    return _run_git(["rev-parse", "HEAD"], Path(root))


def current_git_branch(root: Path | str = ".") -> str:
    return _run_git(["branch", "--show-current"], Path(root))


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
            "- If continuing after a chat control signal, run `agentic-kit evidence inspect --require-summary` or inspect equivalent remote/repo evidence first.",
            "",
            "### RESULT: PASS ###",
        ]
    )
    return "\n".join(lines)


def render_next_chat_bootstrap(root: Path | str = ".", *, include_state: bool = False) -> str:
    """Render the deterministic successor handoff bootstrap projection.

    Prefer the committed latest successor package when present. This makes
    bootstrap validation stable in CI merge-checkout contexts. The
    chat-switch-complete command remains responsible for refreshing the package
    from live local state.
    """
    package_context = Path(root) / "docs/reports/handoff-packages/latest/successor_context.yaml"
    if package_context.exists():
        from agentic_project_kit.successor_handoff_package import (
            load_successor_context,
            render_next_chat_bootstrap_from_context,
        )

        return render_next_chat_bootstrap_from_context(load_successor_context(package_context))

    from agentic_project_kit.successor_handoff_package import build_successor_handoff_package

    result = build_successor_handoff_package(root)
    return result.next_chat_bootstrap



def write_next_chat_bootstrap(
    path: Path | str = DEFAULT_BOOTSTRAP_PATH,
    root: Path | str = ".",
    *,
    include_state: bool = False,
) -> Path:
    output_path = Path(path)
    if output_path == DEFAULT_BOOTSTRAP_PATH:
        output_path = load_workspace(Path(root)).handoff_file("NEXT_CHAT_BOOTSTRAP.md")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_next_chat_bootstrap(root, include_state=include_state), encoding="utf-8")
    return output_path


def validate_generated_bootstrap(path: Path | str = DEFAULT_BOOTSTRAP_PATH, root: Path | str = ".") -> list[str]:
    output_path = Path(path)
    if output_path == DEFAULT_BOOTSTRAP_PATH:
        output_path = load_workspace(Path(root)).handoff_file("NEXT_CHAT_BOOTSTRAP.md")
    elif not output_path.is_absolute():
        output_path = Path(root) / output_path
    if not output_path.exists():
        return [f"missing bootstrap file: {path}"]
    expected = render_next_chat_bootstrap(root)
    actual = output_path.read_text(encoding="utf-8")
    if actual != expected:
        return ["bootstrap file is not generated from chat_bootloader.py"]
    return []


def render_boot_report(root: Path | str = ".") -> str:
    checks = check_boot_sources(root)
    missing = [item.source for item in checks if not item.exists]
    drift = validate_generated_bootstrap(root=root)
    lines = [
        "BOOT_REPORT",
        "",
        f"branch: {current_git_branch(root)}",
        f"head: {current_git_head(root)}",
        f"mandatory_sources_total: {len(checks)}",
        f"mandatory_sources_missing: {len(missing)}",
        "sources_read_required: yes",
        "open_prs: inspect_remote_github_before_mutation",
        "ci: inspect_remote_github_before_mutation",
        "drift_findings:",
    ]
    lines.extend(f"- {finding}" for finding in drift) if drift else lines.append("- none")
    lines.extend(
        [
            "next_safe_slice: verify remote PRs/CI, then continue with no-op/PASS_ALREADY_DONE hardening",
            "### RESULT: PASS ###" if not missing and not drift else "### RESULT: FAIL ###",
        ]
    )
    return "\n".join(lines)


def write_boot_report(path: Path | str = BOOT_REPORT_PATH, root: Path | str = ".") -> Path:
    output_path = Path(path)
    if output_path == BOOT_REPORT_PATH:
        output_path = load_workspace(Path(root)).handoff_file("BOOT_REPORT.md")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_boot_report(root), encoding="utf-8")
    return output_path


def run_chat_switch_closeout(root: Path | str = ".") -> list[str]:
    findings: list[str] = []
    findings.extend(validate_generated_bootstrap(root=root))
    missing = [item.source for item in check_boot_sources(root) if not item.exists]
    findings.extend(f"missing mandatory boot source: {source}" for source in missing)
    return findings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="chat-bootloader")
    parser.add_argument("--root", default=".")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--path", default=str(DEFAULT_BOOTSTRAP_PATH))
    parser.add_argument("--include-state", action="store_true")
    parser.add_argument("--report", action="store_true")
    parser.add_argument("--closeout", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    status = 0
    if args.write:
        output_path = write_next_chat_bootstrap(args.path, args.root, include_state=args.include_state)
        print(f"WROTE {output_path}")
    elif args.report:
        print(render_boot_report(args.root))
    elif args.closeout:
        findings = run_chat_switch_closeout(args.root)
        if findings:
            print("CHAT_SWITCH_CLOSEOUT: FAIL")
            for finding in findings:
                print(f"- {finding}")
            status = 1
        else:
            print("CHAT_SWITCH_CLOSEOUT: PASS")
    else:
        print(render_bootloader(args.root))
    if args.check:
        missing = [item.source for item in check_boot_sources(args.root) if not item.exists]
        if missing:
            status = 1
    return status


if __name__ == "__main__":
    raise SystemExit(main())
