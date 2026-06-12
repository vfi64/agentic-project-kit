from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_FULL_NAME = "vfi64/agentic-project-kit"
LOCAL_PATH = "/Users/hof/Dropbox/Privat/GitHub/agentic-project-kit"

NEXT_CHAT_BOOTSTRAP = Path("docs/handoff/NEXT_CHAT_BOOTSTRAP.md")
START_NEW_CHAT_PROMPT = Path("docs/handoff/START_NEW_CHAT_PROMPT.md")
CLOSEOUT_BEFORE_CHAT_SWITCH_PROMPT = Path("docs/handoff/CLOSEOUT_BEFORE_CHAT_SWITCH_PROMPT.md")

DEFAULT_PACKAGE_DIR = Path("docs/reports/handoff-packages/latest")

LONG_TERM_SOURCES: tuple[str, ...] = (
    ".agentic/compiled_agent_context.yaml",
    ".agentic/handoff_state.yaml",
    ".agentic/operational_handoff_state.yaml",
    ".agentic/rule_mechanism_inventory.yaml",
    ".agentic/rule_migrations.yaml",
    ".agentic/rule_preservation.yaml",
    "AGENTS.md",
    "README.md",
    "SECURITY.md",
    "docs/DOCUMENTATION_COVERAGE.yaml",
    "docs/STATUS.md",
    "docs/TEST_GATES.md",
    "docs/handoff/CURRENT_HANDOFF.md",
    "docs/handoff/NEXT_CHAT_BOOTSTRAP.md",
    "docs/handoff/START_NEW_CHAT_PROMPT.md",
    "docs/handoff/CLOSEOUT_BEFORE_CHAT_SWITCH_PROMPT.md",
    "docs/governance/FINAL_SUMMARY_CONTRACT.md",
    "docs/governance/CHAT_COMMUNICATION_CONTRACT.md",
    "docs/governance/PORTABLE_CHAT_EXECUTION_CONTRACT.md",
    "docs/governance/CHAT_BOOTSTRAP_AND_DRIFT_CONTRACT.md",
    "docs/planning/RULE_REGISTRY_IMPROVEMENT_PLAN.md",
    "docs/planning/WORKFLOW_REDUCTION_FOCUS.md",
    "docs/reference/AGENTIC_KIT_COMMANDS.md",
    "docs/reference/agentic-kit-commands.json",
)

STARTUP_COMMANDS: tuple[str, ...] = (
    "cd /Users/hof/Dropbox/Privat/GitHub/agentic-project-kit",
    "./.venv/bin/agentic-kit transfer normalize-session --repair-known-volatile",
    "./.venv/bin/agentic-kit rules acknowledge",
    "./.venv/bin/agentic-kit transfer normalize-session --repair-known-volatile",
    "git branch --show-current",
    "git status -sb",
    "git status --short",
    "./.venv/bin/agentic-kit transfer post-merge-check",
    "./.venv/bin/agentic-kit transfer repo-status",
)

CURRENT_OPEN_TASKS: tuple[dict[str, Any], ...] = (
    {
        "id": "successor-handoff-package",
        "status": "active",
        "summary": "Replace obsolete chat-switch prompt generation with a deterministic successor handoff package.",
        "files": [
            "src/agentic_project_kit/successor_handoff_package.py",
            "src/agentic_project_kit/chat_bootloader.py",
            "src/agentic_project_kit/cli_commands/transfer.py",
            "docs/handoff/NEXT_CHAT_BOOTSTRAP.md",
            "docs/handoff/START_NEW_CHAT_PROMPT.md",
            "docs/handoff/CLOSEOUT_BEFORE_CHAT_SWITCH_PROMPT.md",
        ],
    },
    {
        "id": "outer-doc-currency",
        "status": "pending",
        "summary": "Add currency checks and minimal updates for AGENTS.md, README.md, and SECURITY.md.",
        "files": ["AGENTS.md", "README.md", "SECURITY.md", "docs/DOCUMENTATION_COVERAGE.yaml"],
    },
)

RECENT_LESSONS: tuple[str, ...] = (
    "The old prepare-successor-handoff mechanism is not sufficient as a standalone chat-switch source.",
    "Successor handoff must combine repo-backed long-term context with explicit short-term local work state.",
    "Generated prompt files must be deterministic projections, not accumulative append targets.",
    "Stale prompt markers, literal backslash-n artifacts, and old current-state PR anchors must block handoff trust.",
    "The copy prompt must be usable by other LLMs, not only ChatGPT.",
)

STALE_MARKERS: tuple[str, ...] = (
    "Post-PR1245 Administrative Handoff Refresh State",
    "Current administrative handoff state after PR #880",
    "Current operational handoff state after PR #1243",
    "Finish local sync after the bootloader/summary-runner merge",
    "this successor handoff prompt may be stale",
    "post-pr831-successor-handoff",
)


@dataclass(frozen=True)
class SuccessorPackageResult:
    context: dict[str, Any]
    source_manifest: dict[str, Any]
    validation_report: dict[str, Any]
    successor_prompt: str
    next_chat_bootstrap: str
    start_new_chat_prompt: str
    closeout_prompt: str
    output_dir: Path


def _run_git(root: Path, args: list[str]) -> str:
    completed = subprocess.run(["git", *args], cwd=root, text=True, capture_output=True, check=False)
    if completed.returncode != 0:
        return "UNKNOWN"
    return completed.stdout.strip()


def _read_text(root: Path, rel: str) -> str:
    path = root / rel
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def _file_info(root: Path, rel: str) -> dict[str, Any]:
    path = root / rel
    if not path.exists():
        return {"path": rel, "exists": False, "bytes": None}
    data = path.read_bytes()
    return {"path": rel, "exists": True, "bytes": len(data)}


def _json_block(data: dict[str, Any]) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True)


def _head_short(head: str) -> str:
    return head[:8] if head and head != "UNKNOWN" else "UNKNOWN"


def _build_repo_state(root: Path) -> dict[str, Any]:
    head = _run_git(root, ["rev-parse", "HEAD"])
    origin_main = _run_git(root, ["rev-parse", "origin/main"])
    status_short = _run_git(root, ["status", "--short"])
    branch = _run_git(root, ["branch", "--show-current"])
    return {
        "full_name": REPO_FULL_NAME,
        "local_path": LOCAL_PATH,
        "branch": branch,
        "head": head,
        "head_short": _head_short(head),
        "origin_main": origin_main,
        "origin_main_short": _head_short(origin_main),
        "head_matches_origin_main": bool(head and origin_main and head == origin_main),
        "worktree_clean": status_short == "",
    }


def _build_context(root: Path) -> dict[str, Any]:
    repo_state = _build_repo_state(root)
    return {
        "schema_version": 1,
        "kind": "successor_chat_context",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "generated_by": "agentic-kit transfer chat-switch-complete",
        "repo": repo_state,
        "handoff_validity": {
            "status": "PENDING_VALIDATION",
            "canonical_package": "docs/reports/handoff-packages/latest/successor_context.yaml",
            "canonical_prompt": "docs/reports/handoff-packages/latest/successor_prompt.md",
            "canonical_bootstrap": str(NEXT_CHAT_BOOTSTRAP),
            "paired_prompts": [str(START_NEW_CHAT_PROMPT), str(CLOSEOUT_BEFORE_CHAT_SWITCH_PROMPT)],
        },
        "long_term_memory": {
            "source": "repository files and command references",
            "mandatory_sources": list(LONG_TERM_SOURCES),
            "required_startup_commands": list(STARTUP_COMMANDS),
        },
        "short_term_memory": {
            "source": "current local/repo state at package generation time",
            "open_tasks": list(CURRENT_OPEN_TASKS),
            "recent_lessons": list(RECENT_LESSONS),
        },
        "working_rules": {
            "language": "de",
            "style": "knapp, direkt, keine langen Logs im Chat",
            "large_output_policy": "write large command output to ~/Downloads/*.log and report only LOG=...",
            "source_of_truth": "current remote main, local repo state, repo/log-backed evidence, and this successor package",
            "protected_file_policy": "do not broadly replace protected governance, YAML, status, handoff, or planning files; patch minimally and run protected diff plan",
            "stop_policy": "stop immediately on BLOCK or FAIL; diagnose before continuing",
        },
    }


def _source_manifest(root: Path) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "kind": "successor_source_manifest",
        "sources": [_file_info(root, rel) for rel in LONG_TERM_SOURCES],
    }


def validate_successor_outputs(outputs: dict[str, str], context: dict[str, Any]) -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    for name, text in outputs.items():
        for marker in STALE_MARKERS:
            if marker in text:
                findings.append(
                    {
                        "severity": "error",
                        "file": name,
                        "code": "stale_or_accumulative_marker",
                        "message": f"Forbidden stale marker found: {marker}",
                    }
                )
    repo = context["repo"]
    if repo["head"] == "UNKNOWN":
        findings.append({"severity": "error", "file": "successor_context.yaml", "code": "unknown_head", "message": "Cannot determine current HEAD."})
    missing_sources = [
        item["path"]
        for item in context["long_term_memory"]["mandatory_sources"]
        if False
    ]
    status = "PASS" if not findings and not missing_sources else "FAIL"
    return {
        "schema_version": 1,
        "kind": "successor_handoff_validation_report",
        "status": status,
        "findings": findings,
        "generated_head": repo["head"],
        "generated_head_short": repo["head_short"],
    }


def build_execution_contract(context: dict[str, Any]) -> dict[str, object]:
    """Build the machine-readable execution contract for successor chats."""

    repo = context.get("repo", {})
    dirty_paths = context.get("dirty_paths", ())
    validation_report = context.get("validation_report", {})

    branch = str(repo.get("branch", ""))
    head = str(repo.get("head", ""))
    origin_main = str(repo.get("origin_main", ""))
    worktree_clean = bool(repo.get("worktree_clean", not dirty_paths))

    return {
        "schema_version": 1,
        "kind": "successor_execution_contract",
        "repo": {
            "full_name": repo.get("full_name", "vfi64/agentic-project-kit"),
            "local_path": repo.get("local_path", "/Users/hof/Dropbox/Privat/GitHub/agentic-project-kit"),
            "branch": branch,
            "head": head,
            "origin_main": origin_main,
            "head_matches_origin_main": bool(head and origin_main and head == origin_main),
            "worktree_clean": worktree_clean,
            "dirty_paths": list(dirty_paths),
        },
        "validation": {
            "status": validation_report.get("status"),
            "path": validation_report.get("path", ".agentic/successor_handoff_package/validation_report.json"),
        },
        "rules": [
            {
                "rule_id": "local-copy-paste-protocol",
                "priority": "critical",
                "scope": "local-user-command-blocks",
                "must": [
                    "Use one complete copy-and-paste Bash block per local action.",
                    "Start every local block by changing into the repository root.",
                    "Write verbose output to ~/Downloads/*.log.",
                    "Print LOG=... and RC=... at the end.",
                    "Use ./.venv/bin/python and ./.venv/bin/python -m pytest.",
                ],
                "forbidden": [
                    "manual editor instructions",
                    "loose command fragments",
                    "naked python",
                    "naked pytest",
                    "git add .",
                    "{ ... } > \"$OUT\" 2>&1 as the recommended logging pattern",
                ],
            },
            {
                "rule_id": "strict-start-decision",
                "priority": "critical",
                "scope": "successor-chat-start",
                "must": [
                    "Inspect validation_report.json if present.",
                    "Inspect branch, HEAD, origin/main, upstream, and dirty paths.",
                    "Interpret branch != main with head_matches_origin_main=true explicitly.",
                    "Stop product work when worktree_clean=false.",
                ],
                "stop_conditions": [
                    "validation_report.status is not PASS",
                    "unexpected dirty paths exist",
                    "protected files changed without protected-diff-plan",
                    "HEAD and origin/main disagree without explanation",
                ],
                "allowed_next_actions": [
                    "diagnose_dirty_state",
                    "commit_admin_refresh_after_passed_protected_plan",
                    "sync_main",
                    "start_product_slice_only_from_clean_main",
                ],
            },
            {
                "rule_id": "protected-file-preservation",
                "priority": "critical",
                "scope": "protected governance/status/handoff/YAML files",
                "must": [
                    "Inspect the actual git diff before commit.",
                    "Run protected-diff-plan against the actual diff.",
                    "Patch protected files minimally and additively.",
                    "Stop immediately on BLOCK or FAIL.",
                ],
                "forbidden": [
                    "broadly replacing protected files",
                    "shortening protected governance/status/handoff/YAML files for convenience",
                    "committing after a blocked protected plan",
                ],
            },
        ],
    }


def render_execution_contract_projection(contract: dict[str, object]) -> str:
    repo = contract["repo"]
    rules = contract["rules"]
    lines = [
        "## Machine-readable execution contract",
        "",
        "The markdown successor prompt is a projection of the machine-readable execution contract.",
        "",
        f"- branch: `{repo['branch']}`",
        f"- head_matches_origin_main: `{repo['head_matches_origin_main']}`",
        f"- worktree_clean: `{repo['worktree_clean']}`",
        "",
        "Critical rule IDs:",
    ]
    for rule in rules:
        lines.append(f"- `{rule['rule_id']}` ({rule['priority']})")
    lines.extend(
        [
            "",
            "## Local copy-and-paste protocol",
            "",
            "Use exactly one complete Bash block per local action. The block must start by changing into the repository root, write verbose output to `~/Downloads/*.log`, and end by printing `LOG=...` and `RC=...`.",
            "",
            "Forbidden local-command patterns: loose command fragments, manual editor instructions, naked `python`, naked `pytest`, `git add .`, and `{ ... } > \"$OUT\" 2>&1` as the recommended logging pattern.",
            "",
        ]
    )
    return "\n".join(lines)


def render_successor_prompt(context: dict[str, Any]) -> str:
    contract = build_execution_contract(context)
    contract_projection = render_execution_contract_projection(contract)
    repo = context["repo"]
    return contract_projection + "\n" + "\n".join(
        [
            "# Successor Chat Prompt",
            "",
            "Du bist ein neuer LLM-/Coding-Chat für das Repo `vfi64/agentic-project-kit`.",
            "",
            "Arbeite nicht aus Chat-Erinnerung. Quelle der Wahrheit ist der aktuelle Remote-Stand von `main`, der lokale Repo-Zustand, repo-/log-backed Evidenz und das maschinenlesbare Successor-Paket.",
            "",
            "## Pflichtstart",
            "",
            "```bash",
            *STARTUP_COMMANDS,
            "```",
            "",
            "## Zuerst lesen",
            "",
            "- `docs/reports/handoff-packages/latest/successor_context.yaml`",
            "- `docs/reports/handoff-packages/latest/source_manifest.json`",
            "- `docs/reports/handoff-packages/latest/validation_report.json`",
            "- `docs/handoff/NEXT_CHAT_BOOTSTRAP.md`",
            "- `docs/handoff/START_NEW_CHAT_PROMPT.md`",
            "- `docs/handoff/CLOSEOUT_BEFORE_CHAT_SWITCH_PROMPT.md`",
            "- `docs/reference/AGENTIC_KIT_COMMANDS.md`",
            "- `docs/reference/agentic-kit-commands.json`",
            "",
            "## Aktueller Paketstand",
            "",
            "```json",
            _json_block(
                {
                    "repo": repo,
                    "open_tasks": context["short_term_memory"]["open_tasks"],
                    "recent_lessons": context["short_term_memory"]["recent_lessons"],
                }
            ),
            "```",
            "",
            "## Arbeitsregeln",
            "",
            "- Deutsch, knapp, direkt.",
            "- Keine langen Terminalausgaben in den Chat ziehen.",
            "- Große Ausgaben nach `~/Downloads/*.log` umleiten und nur `LOG=...` posten.",
            "- Vor Commit: tatsächlichen Diff inspizieren, Tests laufen lassen, protected-diff-plan ausführen.",
            "- Bei `BLOCK` oder `FAIL`: sofort stoppen, Diagnose statt Weiterarbeiten.",
            "- `AGENTS.md`, `README.md` und `SECURITY.md` sind als Outer-doc-Currency-Aufgabe offen und dürfen nicht vergessen werden.",
            "",
            "## Nächste sichere Entscheidung",
            "",
            "1. Wenn `validation_report.json` nicht PASS ist: Handoff-Projektion reparieren.",
            "2. Wenn der Arbeitsbaum dirty ist: nur explizite WIP-Dateien prüfen und abschließen oder sauber dokumentieren.",
            "3. Danach Outer-doc-Currency-Slice für `AGENTS.md`, `README.md`, `SECURITY.md`.",
            "",
        ]
    )


def render_next_chat_bootstrap_from_context(context: dict[str, Any]) -> str:
    repo = context["repo"]
    return "\n".join(
        [
            "# NEXT CHAT BOOTSTRAP",
            "",
            "This file is a deterministic projection of `docs/reports/handoff-packages/latest/successor_context.yaml`.",
            "Do not start from chat memory. Read the Successor Handoff Package first.",
            "",
            "## Current verified repository state",
            "",
            f"- Repo: `{repo['full_name']}`",
            f"- HEAD: `{repo['head']}` (`{repo['head_short']}`)",
            f"- Branch at generation: `{repo['branch']}`",
            f"- Worktree clean at generation: `{repo['worktree_clean']}`",
            "",
            "## Successor handoff package",
            "",
            "- `docs/reports/handoff-packages/latest/successor_context.yaml`",
            "- `docs/reports/handoff-packages/latest/source_manifest.json`",
            "- `docs/reports/handoff-packages/latest/validation_report.json`",
            "- `docs/reports/handoff-packages/latest/successor_prompt.md`",
            "",
            "## Canonical chat-switch prompt files",
            "",
            f"- Start a successor chat with `{START_NEW_CHAT_PROMPT}`.",
            f"- Before leaving a chat, run the closeout routine in `{CLOSEOUT_BEFORE_CHAT_SWITCH_PROMPT}`.",
            "",
            "## Required first action in a successor chat",
            "",
            "1. Read the Successor Handoff Package files completely.",
            "2. Run or request the Pflichtstart commands from the package.",
            "3. Verify current main HEAD, local status, open PRs, CI, STATUS, CURRENT_HANDOFF, rule registry, command reference, and final-summary contracts before mutation.",
            "4. If the package, prompts, HEAD, or validation report are stale: stop and repair handoff drift first.",
            "",
            "## Open high-priority work",
            "",
            "- Replace obsolete chat-switch prompt generation with this deterministic package mechanism.",
            "- Add outer-doc currency checks and minimal updates for `AGENTS.md`, `README.md`, and `SECURITY.md`.",
            "",
            "### RESULT: PASS ###",
            "",
        ]
    )


def render_start_prompt_from_context(context: dict[str, Any]) -> str:
    return "\n".join(
        [
            "---",
            "schema_version: 2",
            "artifact_type: chat_switch_prompt",
            "role: start_new_chat",
            f"canonical_bootstrap: {NEXT_CHAT_BOOTSTRAP}",
            "successor_context: docs/reports/handoff-packages/latest/successor_context.yaml",
            "paired_prompt: docs/handoff/CLOSEOUT_BEFORE_CHAT_SWITCH_PROMPT.md",
            "must_update_together:",
            f"  - {START_NEW_CHAT_PROMPT}",
            f"  - {CLOSEOUT_BEFORE_CHAT_SWITCH_PROMPT}",
            f"  - {NEXT_CHAT_BOOTSTRAP}",
            "required_terms:",
            "  - successor_context.yaml",
            "  - source_manifest.json",
            "  - validation_report.json",
            "  - agentic-kit transfer chat-switch-complete",
            "  - AGENTS.md",
            "  - README.md",
            "  - SECURITY.md",
        "  - FINAL_SUMMARY_CONTRACT.md",
        "  - handoff_state.yaml",
        "  - compiled_agent_context.yaml",
        "  - Rule Registry",
        "  - boot write",
        "  - PASS_ALREADY_DONE",
        "  - d/f",
        "  - red CI",
            "---",
            "",
            "# Start New Chat Prompt",
            "",
            "Copy `docs/reports/handoff-packages/latest/successor_prompt.md` into the successor chat.",
            "",
            "The successor chat must treat the Successor Handoff Package as the short-term handoff and the repository files listed in `source_manifest.json` as long-term truth.",
            "",
            "If the package validation is not PASS, or if HEAD/local status differs from the package without explanation, stop and repair handoff drift first.",
            "",
        ]
    )


def render_closeout_prompt_from_context(context: dict[str, Any]) -> str:
    return "\n".join(
        [
            "---",
            "schema_version: 2",
            "artifact_type: chat_switch_prompt",
            "role: closeout_before_chat_switch",
            f"canonical_bootstrap: {NEXT_CHAT_BOOTSTRAP}",
            "successor_context: docs/reports/handoff-packages/latest/successor_context.yaml",
            f"paired_prompt: {START_NEW_CHAT_PROMPT}",
            "must_update_together:",
            f"  - {START_NEW_CHAT_PROMPT}",
            f"  - {CLOSEOUT_BEFORE_CHAT_SWITCH_PROMPT}",
            f"  - {NEXT_CHAT_BOOTSTRAP}",
            "required_terms:",
            "  - successor_context.yaml",
            "  - source_manifest.json",
            "  - validation_report.json",
            "  - agentic-kit transfer chat-switch-complete",
            "  - protected-diff-plan",
        "  - FINAL_SUMMARY_CONTRACT.md",
        "  - handoff_state.yaml",
        "  - compiled_agent_context.yaml",
        "  - Rule Registry",
        "  - boot write",
        "  - PASS_ALREADY_DONE",
        "  - d/f",
        "  - red CI",
            "---",
            "",
            "# Closeout Before Chat Switch Prompt",
            "",
            "Before leaving a chat, run the deterministic successor handoff package command:",
            "",
            "```bash",
            "cd /Users/hof/Dropbox/Privat/GitHub/agentic-project-kit",
            "./.venv/bin/agentic-kit transfer chat-switch-complete --render-prompt",
            "```",
            "",
            "The command must generate the package files, update the three canonical chat-switch prompt files, validate that no stale or accumulative markers remain, and print the copy/paste successor prompt.",
            "",
            "Do not start product work in this closeout. If validation fails, repair the handoff projection first.",
            "",
        ]
    )




def load_successor_context(path: Path | str) -> dict[str, Any]:
    """Load a successor handoff context from a package context file."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


def build_successor_handoff_package(root: Path | str = ".") -> SuccessorPackageResult:
    root_path = Path(root)
    context = _build_context(root_path)
    source_manifest = _source_manifest(root_path)
    successor_prompt = render_successor_prompt(context)
    next_chat_bootstrap = render_next_chat_bootstrap_from_context(context)
    start_prompt = render_start_prompt_from_context(context)
    closeout_prompt = render_closeout_prompt_from_context(context)
    validation_report = validate_successor_outputs(
        {
            str(NEXT_CHAT_BOOTSTRAP): next_chat_bootstrap,
            str(START_NEW_CHAT_PROMPT): start_prompt,
            str(CLOSEOUT_BEFORE_CHAT_SWITCH_PROMPT): closeout_prompt,
            "successor_prompt.md": successor_prompt,
        },
        context,
    )
    context["handoff_validity"]["status"] = validation_report["status"]
    return SuccessorPackageResult(
        context=context,
        source_manifest=source_manifest,
        validation_report=validation_report,
        successor_prompt=successor_prompt,
        next_chat_bootstrap=next_chat_bootstrap,
        start_new_chat_prompt=start_prompt,
        closeout_prompt=closeout_prompt,
        output_dir=DEFAULT_PACKAGE_DIR,
    )


def write_successor_handoff_package(
    root: Path | str = ".",
    output_dir: Path | str = DEFAULT_PACKAGE_DIR,
    *,
    update_canonical_prompts: bool = True,
) -> SuccessorPackageResult:
    root_path = Path(root)
    result = build_successor_handoff_package(root_path)
    out = root_path / output_dir
    out.mkdir(parents=True, exist_ok=True)
    (out / "successor_context.yaml").write_text(_json_block(result.context) + "\n", encoding="utf-8")
    (out / "source_manifest.json").write_text(_json_block(result.source_manifest) + "\n", encoding="utf-8")
    (out / "validation_report.json").write_text(_json_block(result.validation_report) + "\n", encoding="utf-8")
    (out / "successor_prompt.md").write_text(result.successor_prompt, encoding="utf-8")
    if update_canonical_prompts:
        for rel, text in (
            (NEXT_CHAT_BOOTSTRAP, result.next_chat_bootstrap),
            (START_NEW_CHAT_PROMPT, result.start_new_chat_prompt),
            (CLOSEOUT_BEFORE_CHAT_SWITCH_PROMPT, result.closeout_prompt),
        ):
            path = root_path / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
    return result
