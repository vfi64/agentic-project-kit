from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from agentic_project_kit.chat_entrypoint_contract import (
    command_reference_contract,
    ensure_command_reference_in_prompt,
)
from typing import Any

from agentic_project_kit import __version__ as PACKAGE_VERSION
from agentic_project_kit.project_direction import load_project_direction
from agentic_project_kit.workspace import KitConfig, Workspace, load_workspace

REPO_FULL_NAME = "vfi64/agentic-project-kit"
DEFAULT_LOCAL_PATH = "cd /path/to/agentic-project-kit"

_LEGACY_WORKSPACE = Workspace(root=Path("."), config=KitConfig())


def _path_text(path: Path) -> str:
    return path.as_posix()


def _workspace_path_text(ws: Workspace, path: Path) -> str:
    try:
        return path.relative_to(ws.root).as_posix()
    except ValueError:
        return path.as_posix()


NEXT_CHAT_BOOTSTRAP = _LEGACY_WORKSPACE.handoff_file("NEXT_CHAT_BOOTSTRAP.md")
START_NEW_CHAT_PROMPT = _LEGACY_WORKSPACE.handoff_file("START_NEW_CHAT_PROMPT.md")
CLOSEOUT_BEFORE_CHAT_SWITCH_PROMPT = _LEGACY_WORKSPACE.handoff_file("CLOSEOUT_BEFORE_CHAT_SWITCH_PROMPT.md")

DEFAULT_PACKAGE_DIR = _LEGACY_WORKSPACE.handoff_packages_latest()


def _long_term_sources(ws: Workspace) -> tuple[str, ...]:
    return (
        ".agentic/compiled_agent_context.yaml",
        ".agentic/handoff_state.yaml",
        ".agentic/operational_handoff_state.yaml",
        ".agentic/rule_mechanism_inventory.yaml",
        ".agentic/rule_migrations.yaml",
        ".agentic/rule_preservation.yaml",
        "AGENTS.md",
        "README.md",
        "SECURITY.md",
        _workspace_path_text(ws, ws.documentation_coverage_path()),
        _workspace_path_text(ws, ws.doc_registry_path()),
        _workspace_path_text(ws, ws.status_path()),
        _workspace_path_text(ws, ws.test_gates_path()),
        _workspace_path_text(ws, ws.handoff_file("CURRENT_HANDOFF.md")),
        _workspace_path_text(ws, ws.handoff_file("NEXT_CHAT_BOOTSTRAP.md")),
        _workspace_path_text(ws, ws.handoff_file("START_NEW_CHAT_PROMPT.md")),
        _workspace_path_text(ws, ws.handoff_file("CLOSEOUT_BEFORE_CHAT_SWITCH_PROMPT.md")),
        _workspace_path_text(ws, ws.governance_file("FINAL_SUMMARY_CONTRACT.md")),
        _workspace_path_text(ws, ws.governance_file("CHAT_COMMUNICATION_CONTRACT.md")),
        _workspace_path_text(ws, ws.governance_file("PORTABLE_CHAT_EXECUTION_CONTRACT.md")),
        _workspace_path_text(ws, ws.governance_file("CHAT_BOOTSTRAP_AND_DRIFT_CONTRACT.md")),
        _workspace_path_text(ws, ws.project_direction_path()),
        _workspace_path_text(ws, ws.reference_file("AGENTIC_KIT_COMMANDS.md")),
        _workspace_path_text(ws, ws.reference_file("agentic-kit-commands.json")),
    )


LONG_TERM_SOURCES: tuple[str, ...] = _long_term_sources(_LEGACY_WORKSPACE)

STARTUP_COMMANDS: tuple[str, ...] = (
    "cd /path/to/agentic-project-kit",
    "./.venv/bin/agentic-kit transfer normalize-session --repair-known-volatile",
    "./.venv/bin/agentic-kit rules acknowledge",
    "./.venv/bin/agentic-kit transfer normalize-session --repair-known-volatile",
    "git branch --show-current",
    "git status -sb",
    "git status --short",
    "./.venv/bin/agentic-kit transfer post-merge-check",
    "./.venv/bin/agentic-kit transfer repo-status",
)

RECENT_LESSONS: tuple[str, ...] = (
    "The old prepare-successor-handoff mechanism is not sufficient as a standalone chat-switch source.",
    "Successor handoff must combine repo-backed long-term context with explicit short-term local work state.",
    "Generated prompt files must be deterministic projections, not accumulative append targets.",
    "Stale prompt markers, literal backslash-n artifacts, and old current-state PR anchors must block handoff trust.",
    "The copy prompt must be usable by other LLMs, not only ChatGPT.",
    "After v0.4.9, release metadata preparation must have one supported agentic-kit route before manual-metadata gates are tightened.",
    "release_publish_core must not remain able to execute removed ./ns release routes after the ns entrypoint removal.",
)

STALE_MARKERS: tuple[str, ...] = (
    "Post-PR1245 Administrative Handoff Refresh State",
    "Current administrative handoff state after PR #880",
    "Current operational handoff state after PR #1243",
    "Finish local sync after the bootloader/summary-runner merge",
    "this successor handoff prompt may be stale",
    "post-pr831-successor-handoff",
)


REQUIRED_EXECUTION_CONTRACT_RULE_IDS: frozenset[str] = frozenset(
    {
        "local-copy-paste-protocol",
        "strict-start-decision",
        "protected-file-preservation",
        "bootstrap_acceptance_gate",
        "wrapper-first-complete-development-cycle",
        "successor-package-not-prompt-only",
        "documentation-authority-model",
        "repo-backed-rules-and-gates",
        "gc-retention-not-document-migration",
        "ns-legacy-not-active-control-plane",
        "generated-handoff-projection-update-policy",
        "patch-cycle-diagnostic-gate",
        "copy-paste-output-discipline",
    }
)

GENERAL_CONTRACT_RULE_IDS: frozenset[str] = frozenset(
    {
        "wrapper-first-complete-development-cycle",
        "successor-package-not-prompt-only",
        "documentation-authority-model",
        "repo-backed-rules-and-gates",
        "gc-retention-not-document-migration",
        "ns-legacy-not-active-control-plane",
        "generated-handoff-projection-update-policy",
        "patch-cycle-diagnostic-gate",
        "copy-paste-output-discipline",
    }
)

def _generated_handoff_projection_paths(ws: Workspace) -> tuple[str, ...]:
    return (
        _workspace_path_text(ws, ws.handoff_file("NEXT_CHAT_BOOTSTRAP.md")),
        _workspace_path_text(ws, ws.handoff_file("START_NEW_CHAT_PROMPT.md")),
        _workspace_path_text(ws, ws.handoff_file("CLOSEOUT_BEFORE_CHAT_SWITCH_PROMPT.md")),
        _workspace_path_text(ws, ws.package_file("execution_contract.json")),
        _workspace_path_text(ws, ws.package_file("source_manifest.json")),
        _workspace_path_text(ws, ws.package_file("successor_context.yaml")),
        _workspace_path_text(ws, ws.package_file("successor_prompt.md")),
        _workspace_path_text(ws, ws.package_file("validation_report.json")),
        _workspace_path_text(ws, ws.transfer_handoff_report_file("latest-transfer-handoff-report.json")),
        _workspace_path_text(ws, ws.transfer_handoff_report_file("latest-transfer-handoff-report.log")),
    )


GENERATED_HANDOFF_PROJECTION_PATHS: tuple[str, ...] = _generated_handoff_projection_paths(_LEGACY_WORKSPACE)


def _general_source_authorities(ws: Workspace) -> tuple[str, ...]:
    return (
        ".agentic/compiled_agent_context.yaml",
        ".agentic/transfer_safety_rules.yaml",
        ".agentic/transfer/one_command_transfer_protocol.yaml",
        _workspace_path_text(ws, ws.project_direction_path()),
        _workspace_path_text(ws, ws.doc_registry_path()),
        _workspace_path_text(ws, ws.reference_file("agentic-kit-commands.json")),
        _workspace_path_text(ws, ws.reference_file("AGENTIC_KIT_COMMANDS.md")),
    )


GENERAL_SOURCE_AUTHORITIES: tuple[str, ...] = _general_source_authorities(_LEGACY_WORKSPACE)

FORBIDDEN_LOCAL_COMMAND_RECOMMENDATIONS: tuple[str, ...] = (
    "python ",
    "pytest ",
    "git add .",
    "{ ... } > \"$OUT\" 2>&1",
)


def _forbidden_local_command_recommendations(text: str) -> list[str]:
    """Return forbidden local command recommendations, ignoring explicit forbidden lists."""

    findings: list[str] = []
    for line in text.splitlines():
        stripped = line.strip().strip("`")
        lower = stripped.lower()

        if not stripped:
            continue
        if lower.startswith(("forbidden ", "forbidden:", "verboten ", "verboten:")):
            continue
        if "\"forbidden\"" in lower or "'forbidden'" in lower:
            continue

        if stripped.startswith("python "):
            findings.append("python ")
        if stripped.startswith("pytest "):
            findings.append("pytest ")
        if stripped == "git add ." or stripped.startswith("git add . "):
            findings.append("git add .")
        if stripped.startswith("{ ... } > \"$OUT\" 2>&1"):
            findings.append("{ ... } > \"$OUT\" 2>&1")

    return findings


@dataclass(frozen=True)
class SuccessorPackageResult:
    context: dict[str, Any]
    source_manifest: dict[str, Any]
    validation_report: dict[str, Any]
    execution_contract: dict[str, object]
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
        "local_path": DEFAULT_LOCAL_PATH,
        "branch": branch,
        "head": head,
        "head_short": _head_short(head),
        "origin_main": origin_main,
        "origin_main_short": _head_short(origin_main),
        "head_matches_origin_main": bool(head and origin_main and head == origin_main),
        "worktree_clean": status_short == "",
    }


def _open_tasks_from_project_direction(root: Path, ws: Workspace) -> list[dict[str, Any]]:
    project_direction_path = _workspace_path_text(ws, ws.project_direction_path())
    registry_path = _workspace_path_text(ws, ws.doc_registry_path())
    try:
        direction = load_project_direction(root)
        findings = direction.validate()
    except (OSError, ValueError) as exc:
        return [
            {
                "id": "project-direction-unavailable",
                "status": "blocked",
                "summary": f"Cannot load {project_direction_path}: {exc}",
                "files": [project_direction_path],
            }
        ]
    if findings:
        return [
            {
                "id": "project-direction-invalid",
                "status": "blocked",
                "summary": "Project direction validation failed: " + "; ".join(findings),
                "files": [project_direction_path],
            }
        ]

    tasks: list[dict[str, Any]] = []
    open_statuses = {
        "roadmap": {"next", "planned", "blocked"},
        "plans": {"active", "planned", "blocked"},
    }
    for section, statuses in open_statuses.items():
        section_items = direction.data.get(section, [])
        if not isinstance(section_items, list):
            continue
        for item in section_items:
            if not isinstance(item, dict):
                continue
            status = str(item.get("status", "")).strip()
            if status not in statuses:
                continue
            task_id = str(item.get("id", f"unknown-{section}-item")).strip()
            title = str(item.get("title", task_id)).strip()
            target = str(item.get("target_release") or item.get("phase") or "").strip()
            summary = title
            if target:
                summary = f"{summary} for {target}"
            tasks.append(
                {
                    "id": task_id,
                    "status": status,
                    "summary": summary,
                    "files": [
                        project_direction_path,
                        registry_path,
                    ],
                }
            )
    return tasks or [
        {
            "id": "project-direction-no-open-milestones",
            "status": "review",
            "summary": "No active or planned milestones are listed in PROJECT_DIRECTION.yaml.",
            "files": [project_direction_path],
        }
    ]


def _build_context(root: Path, ws: Workspace) -> dict[str, Any]:
    repo_state = _build_repo_state(root)
    successor_context_path = _workspace_path_text(ws, ws.package_file("successor_context.yaml"))
    successor_prompt_path = _workspace_path_text(ws, ws.package_file("successor_prompt.md"))
    next_chat_bootstrap_path = _workspace_path_text(ws, ws.handoff_file("NEXT_CHAT_BOOTSTRAP.md"))
    start_prompt_path = _workspace_path_text(ws, ws.handoff_file("START_NEW_CHAT_PROMPT.md"))
    closeout_prompt_path = _workspace_path_text(ws, ws.handoff_file("CLOSEOUT_BEFORE_CHAT_SWITCH_PROMPT.md"))
    return {
        "schema_version": 1,
        "kind": "successor_chat_context",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "generated_by": "agentic-kit transfer chat-switch-complete",
        "repo": repo_state,
        "release": {
            "package_version": PACKAGE_VERSION,
        },
        "handoff_validity": {
            "status": "PENDING_VALIDATION",
            "canonical_package": successor_context_path,
            "canonical_prompt": successor_prompt_path,
            "canonical_bootstrap": next_chat_bootstrap_path,
            "paired_prompts": [start_prompt_path, closeout_prompt_path],
        },
        "long_term_memory": {
            "source": "repository files and command references",
            "mandatory_sources": list(_long_term_sources(ws)),
            "required_startup_commands": list(STARTUP_COMMANDS),
        },
        "short_term_memory": {
            "source": "current local/repo state at package generation time",
            "open_tasks": _open_tasks_from_project_direction(root, ws),
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


def _source_manifest(root: Path, ws: Workspace) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "kind": "successor_source_manifest",
        "sources": [_file_info(root, rel) for rel in _long_term_sources(ws)],
    }


def validate_successor_outputs(
    outputs: dict[str, str],
    context: dict[str, Any],
    ws: Workspace | None = None,
) -> dict[str, Any]:
    ws = ws or _LEGACY_WORKSPACE
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

    execution_contract_text = outputs.get("execution_contract.json")
    if execution_contract_text is None:
        findings.append(
            {
                "severity": "error",
                "file": "execution_contract.json",
                "code": "missing_execution_contract",
                "message": "Successor handoff package must include execution_contract.json.",
            }
        )
    else:
        try:
            execution_contract = json.loads(execution_contract_text)
        except json.JSONDecodeError as exc:
            findings.append(
                {
                    "severity": "error",
                    "file": "execution_contract.json",
                    "code": "invalid_execution_contract_json",
                    "message": f"execution_contract.json is not valid JSON: {exc}",
                }
            )
            execution_contract = {}

        if execution_contract.get("kind") != "successor_execution_contract":
            findings.append(
                {
                    "severity": "error",
                    "file": "execution_contract.json",
                    "code": "invalid_execution_contract_kind",
                    "message": "execution_contract.json must have kind=successor_execution_contract.",
                }
            )

        rules = execution_contract.get("rules", [])
        if not isinstance(rules, list):
            rules = []
        rule_ids = {rule.get("rule_id") for rule in rules if isinstance(rule, dict)}
        missing_rule_ids = sorted(REQUIRED_EXECUTION_CONTRACT_RULE_IDS - rule_ids)
        if missing_rule_ids:
            findings.append(
                {
                    "severity": "error",
                    "file": "execution_contract.json",
                    "code": "missing_execution_contract_rule_ids",
                    "message": "Missing required execution contract rule IDs: " + ", ".join(missing_rule_ids),
                }
            )

        general_contract = execution_contract.get("general_contract")
        if not isinstance(general_contract, dict):
            findings.append(
                {
                    "severity": "error",
                    "file": "execution_contract.json",
                    "code": "missing_general_contract",
                    "message": "execution_contract.json must separate durable agentic-kit rules into general_contract.",
                }
            )
            general_contract = {}
        general_rule_ids = set(general_contract.get("rule_ids", []))
        missing_general_rule_ids = sorted(GENERAL_CONTRACT_RULE_IDS - general_rule_ids)
        if missing_general_rule_ids:
            findings.append(
                {
                    "severity": "error",
                    "file": "execution_contract.json",
                    "code": "missing_general_contract_rule_ids",
                    "message": "Missing general contract rule IDs: " + ", ".join(missing_general_rule_ids),
                }
            )
        if general_contract.get("scope") != "durable-agentic-kit-operating-model":
            findings.append(
                {
                    "severity": "error",
                    "file": "execution_contract.json",
                    "code": "invalid_general_contract_scope",
                    "message": "general_contract.scope must identify durable agentic-kit operating rules.",
                }
            )

        current_state_contract = execution_contract.get("current_state_contract")
        if not isinstance(current_state_contract, dict):
            findings.append(
                {
                    "severity": "error",
                    "file": "execution_contract.json",
                    "code": "missing_current_state_contract",
                    "message": "execution_contract.json must separate current continuation state into current_state_contract.",
                }
            )
            current_state_contract = {}
        if current_state_contract.get("scope") != "current-continuation-state":
            findings.append(
                {
                    "severity": "error",
                    "file": "execution_contract.json",
                    "code": "invalid_current_state_contract_scope",
                    "message": "current_state_contract.scope must identify volatile/current continuation state.",
                }
            )

        projection_contract = execution_contract.get("handoff_projection_contract")
        if not isinstance(projection_contract, dict):
            findings.append(
                {
                    "severity": "error",
                    "file": "execution_contract.json",
                    "code": "missing_handoff_projection_contract",
                    "message": "execution_contract.json must state that markdown prompts are projections.",
                }
            )
            projection_contract = {}
        if projection_contract.get("prompt_is_projection_only") is not True:
            findings.append(
                {
                    "severity": "error",
                    "file": "execution_contract.json",
                    "code": "prompt_not_marked_projection_only",
                    "message": "handoff_projection_contract.prompt_is_projection_only must be true.",
                }
            )
        if projection_contract.get("machine_readable_files_take_precedence") is not True:
            findings.append(
                {
                    "severity": "error",
                    "file": "execution_contract.json",
                    "code": "machine_readable_precedence_missing",
                    "message": "handoff_projection_contract must make machine-readable files authoritative over copied prompt text.",
                }
            )
        expected_projection_paths = set(_generated_handoff_projection_paths(ws))
        actual_projection_paths = set(projection_contract.get("generated_projection_paths", []))
        missing_projection_paths = sorted(expected_projection_paths - actual_projection_paths)
        if missing_projection_paths:
            findings.append(
                {
                    "severity": "error",
                    "file": "execution_contract.json",
                    "code": "missing_generated_handoff_projection_paths",
                    "message": "Missing generated handoff projection paths: " + ", ".join(missing_projection_paths),
                }
            )
        if projection_contract.get("source_of_truth") != "generator_and_machine_readable_successor_package":
            findings.append(
                {
                    "severity": "error",
                    "file": "execution_contract.json",
                    "code": "invalid_handoff_projection_source_of_truth",
                    "message": "handoff_projection_contract.source_of_truth must point at generator and machine-readable package.",
                }
            )
        if projection_contract.get("generator_command") != "agentic-kit transfer prepare-successor-handoff --render-prompt":
            findings.append(
                {
                    "severity": "error",
                    "file": "execution_contract.json",
                    "code": "missing_handoff_projection_generator_command",
                    "message": "handoff_projection_contract.generator_command must name the canonical projection generator.",
                }
            )
        if "manual direct edits to generated handoff projections" not in projection_contract.get("forbidden_update_path", []):
            findings.append(
                {
                    "severity": "error",
                    "file": "execution_contract.json",
                    "code": "missing_forbidden_generated_handoff_update_path",
                    "message": "handoff_projection_contract must forbid manual direct edits to generated handoff projections.",
                }
            )

        forbidden_text = execution_contract_text + "\n" + outputs.get("successor_prompt.md", "")
        for forbidden in _forbidden_local_command_recommendations(forbidden_text):
            findings.append(
                {
                    "severity": "error",
                    "file": "execution_contract.json",
                    "code": "forbidden_local_command_recommendation",
                    "message": f"Forbidden local command recommendation found: {forbidden}",
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


def build_execution_contract(context: dict[str, Any], ws: Workspace | None = None) -> dict[str, object]:
    """Build the machine-readable execution contract for successor chats."""

    ws = ws or _LEGACY_WORKSPACE
    repo = context.get("repo", {})
    dirty_paths = context.get("dirty_paths", ())
    validation_report = context.get("validation_report", {})
    successor_context_path = _workspace_path_text(ws, ws.package_file("successor_context.yaml"))
    source_manifest_path = _workspace_path_text(ws, ws.package_file("source_manifest.json"))
    validation_report_path = _workspace_path_text(ws, ws.package_file("validation_report.json"))
    execution_contract_path = _workspace_path_text(ws, ws.package_file("execution_contract.json"))
    successor_prompt_path = _workspace_path_text(ws, ws.package_file("successor_prompt.md"))

    branch = str(repo.get("branch", ""))
    head = str(repo.get("head", ""))
    origin_main = str(repo.get("origin_main", ""))
    worktree_clean = bool(repo.get("worktree_clean", not dirty_paths))

    open_tasks = context.get("short_term_memory", {}).get("open_tasks", [])
    recent_lessons = context.get("short_term_memory", {}).get("recent_lessons", [])

    general_contract = {
        "scope": "durable-agentic-kit-operating-model",
        "rule_ids": sorted(GENERAL_CONTRACT_RULE_IDS),
        "source_authorities": list(_general_source_authorities(ws)),
        "summary": {
            "agentic_kit_is_control_plane": True,
            "wrapper_first": True,
            "complete_development_cycle_required": True,
            "repo_backed_rules_and_gates_required": True,
            "documentation_authority_model_required": True,
            "gc_is_retention_not_document_migration": True,
            "ns_is_legacy_not_active_control_plane": True,
            "do_not_plan_from_stale_chat_memory": True,
        },
    }

    current_state_contract = {
        "scope": "current-continuation-state",
        "repo": {
            "full_name": repo.get("full_name", "vfi64/agentic-project-kit"),
            "local_path": repo.get("local_path", "cd /path/to/agentic-project-kit"),
            "branch": branch,
            "head": head,
            "origin_main": origin_main,
            "head_matches_origin_main": bool(head and origin_main and head == origin_main),
            "worktree_clean": worktree_clean,
            "dirty_paths": list(dirty_paths),
        },
        "open_tasks_source": _workspace_path_text(ws, ws.project_direction_path()),
        "document_registry_source": _workspace_path_text(ws, ws.doc_registry_path()),
        "open_tasks": open_tasks,
        "recent_lessons": recent_lessons,
        "next_action_rule": "Use current_state_contract only as continuation state; do not promote it to durable rules.",
    }

    handoff_projection_contract = {
        "prompt_is_projection_only": True,
        "machine_readable_files_take_precedence": True,
        "generated_projection_paths": list(_generated_handoff_projection_paths(ws)),
        "source_of_truth": "generator_and_machine_readable_successor_package",
        "allowed_update_path": [
            "Change successor_handoff_package.py, execution contract inputs, or repo-backed rule sources.",
            "Add or update tests and validation for new handoff content.",
            "Run agentic-kit transfer prepare-successor-handoff --render-prompt to regenerate projections.",
        ],
        "forbidden_update_path": [
            "manual direct edits to generated handoff projections",
            "adding durable rules only to docs/handoff/*.md",
            "editing latest handoff-package JSON/YAML/Markdown as the primary patch",
        ],
        "generator_command": "agentic-kit transfer prepare-successor-handoff --render-prompt",
        "must_read_files": [
            execution_contract_path,
            successor_context_path,
            validation_report_path,
            source_manifest_path,
            successor_prompt_path,
        ],
        "stale_local_prompt_files_are_not_authoritative": True,
        "do_not_use_uploaded_or_copied_prompt_text_as_sole_source": True,
    }

    return {
        "schema_version": 1,
        "kind": "successor_execution_contract",
        "general_contract": general_contract,
        "current_state_contract": current_state_contract,
        "handoff_projection_contract": handoff_projection_contract,
        "repo": current_state_contract["repo"],
        "command_reference": command_reference_contract(ws.root),
        "source_hashes": command_reference_contract(ws.root)["source_hashes"],
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
                "rule_id": BOOTSTRAP_ACCEPTANCE_GATE_RULE_ID,
                "priority": "critical",
                "scope": "successor-chat-bootstrap",
                "must": [
                    "After running the bootstrap block, evaluate the log before starting any new work.",
                    "Confirm RC=0 and RESULT=NEW_CHAT_BOOTSTRAP_DONE.",
                    "Confirm main == origin/main and worktree clean.",
                    "Confirm post-merge-check PASS with refresh_required=False, result=NOOP, next_safe_action=none.",
                    "Confirm repo-status PASS and docs-audit PASS.",
                    "Confirm validation_report.json PASS and execution_contract.json was read.",
                    "Emit exactly one status decision: Übergabe akzeptiert, keine Admin-Arbeit nötig. or BLOCK with the concrete log-backed reason.",
                ],
                "forbidden_when_bootstrap_is_green": [
                    "revalidating already-merged handoff PRs",
                    "regenerating handoff files",
                    "running prepare-successor-handoff --render-prompt",
                    "starting administrative refresh work",
                ],
            },
            {
                "rule_id": "wrapper-first-complete-development-cycle",
                "priority": "critical",
                "scope": "feature-development-pr-handoff",
                "must": [
                    "Use agentic-kit wrappers as the authoritative control plane.",
                    "Prefer complex transfer wrappers over hand-built Git/GitHub/handoff/release/GC shell logic.",
                    "Run focused tests, full tests/audits as needed, inspect actual diff, and run transfer protected-diff-plan before commit.",
                    "Commit through transfer commit, then run rules acknowledge.",
                    "Before PR completion, regenerate and publish fresh successor/LLM handoff context.",
                    "Use transfer pr-create-complete with --post-merge-complete for the normal PR lifecycle.",
                    "After merge, sync main, restore known volatile files, run post-merge-check on main, repo-status, audits, standard gates, and final successor handoff.",
                ],
                "forbidden": [
                    "manual PR creation/merge when the wrapper can perform the lifecycle",
                    "running post-merge-check as a feature-branch pre-PR gate",
                    "planning from stale chat memory or stale copied prompt text",
                ],
            },
            {
                "rule_id": "successor-package-not-prompt-only",
                "priority": "critical",
                "scope": "chat-switch-handoff",
                "must": [
                    "Treat successor_prompt.md as a human-readable projection only.",
                    "Read execution_contract.json, successor_context.yaml, validation_report.json, and source_manifest.json before work.",
                    "Use machine-readable files over stale copied prompt text when they disagree.",
                ],
                "forbidden": [
                    "using NEW_CHAT_HANDOFF_PROMPT.md or copied chat text as the sole start authority",
                    "starting product work before validation_report.json and execution_contract.json were inspected",
                ],
            },
            {
                "rule_id": "documentation-authority-model",
                "priority": "critical",
                "scope": "documentation-reconciliation",
                "must": [
                    "Use docs/planning/PROJECT_DIRECTION.yaml for active roadmap, strategy, and current tasks.",
                    "Use docs/DOCUMENTATION_REGISTRY.yaml for document classification and authority mapping.",
                    "Classify obsolete documents before archive/delete decisions.",
                    "Retarget active references away from obsolete/superseded documents before archival.",
                ],
                "forbidden": [
                    "adding new operational rules to historical, archived, superseded, or migration-report documents",
                    "treating old roadmap or planning markdown files as active authority",
                    "deleting semantic documentation through report-retention GC",
                ],
            },
            {
                "rule_id": "repo-backed-rules-and-gates",
                "priority": "critical",
                "scope": "rules-tests-evidence",
                "must": [
                    "Treat repo-backed rules, tests, gates, and evidence logs as authoritative.",
                    "Stop on BLOCK or FAIL and diagnose before continuing.",
                    "Run protected-diff-plan before protected/governance/status/handoff/YAML commits.",
                    "Use evidence-producing commands; do not substitute a free-text PASS.",
                ],
                "forbidden": [
                    "committing, pushing, creating PRs, or merging after protected-diff-plan FAIL",
                    "overwriting protected files broadly to make gates pass",
                ],
            },
            {
                "rule_id": "gc-retention-not-document-migration",
                "priority": "critical",
                "scope": "artifact-gc",
                "must": [
                    "Treat report-retention GC as technical artifact/report retention.",
                    "Use dry-run before execute.",
                    "Restrict automatic report-retention execution to explicitly allowed candidate types.",
                ],
                "forbidden": [
                    "using GC as semantic documentation migration",
                    "deleting .md/.py/.yaml/.txt without explicit policy and review",
                ],
            },
            {
                "rule_id": "ns-legacy-not-active-control-plane",
                "priority": "critical",
                "scope": "legacy-ns-references",
                "must": [
                    "Treat ns migration documents as historical or compatibility context unless the registry says otherwise.",
                    "Classify ./ns references as historical, test fixture, compatibility implementation, or active blocker before changing them.",
                ],
                "forbidden": [
                    "placing new operational rules in docs/reports/ns-migration/",
                    "resurrecting removed ./ns routes as active workflow instructions",
                ],
            },
            {
                "rule_id": "generated-handoff-projection-update-policy",
                "priority": "critical",
                "scope": "generated handoff projections",
                "must": [
                    "Treat docs/handoff/*.md and latest successor package files as generated projections.",
                    "Change the generator, execution contract, validation, or rule source before changing projected handoff content.",
                    "Regenerate projections with agentic-kit transfer prepare-successor-handoff --render-prompt.",
                ],
                "forbidden": [
                    "manual direct edits to generated handoff projection files as the primary source of a new rule",
                    "making copied prompt text the durable source of truth",
                ],
            },
            {
                "rule_id": "patch-cycle-diagnostic-gate",
                "priority": "critical",
                "scope": "failed patch/test cycles",
                "must": [
                    "After one failed patch, allow exactly one direct correction in the same patch family.",
                    "After a second failure in the same patch family, stop mutations and run a bounded diagnosis block.",
                    "Classify product bug versus test-model bug before another mutation.",
                    "Record next_mutation_allowed explicitly before continuing.",
                ],
                "forbidden": [
                    "starting a third mutation in the same patch family without diagnosis",
                    "continuing a micro-patch cascade after repeated red tests",
                ],
            },
            {
                "rule_id": "copy-paste-output-discipline",
                "priority": "critical",
                "scope": "local copy-and-paste workflows",
                "must": [
                    "After local blocks, chat output should be only LOG=... and RC=....",
                    "Write large outputs to tmp/*.log or ~/Downloads/*.log.",
                    "Use compact JSON summaries for diagnostics.",
                    "Compress or summarize large logs before discussion.",
                ],
                "forbidden": [
                    "cat whole diagnostic or summary files into chat",
                    "unbounded grep over docs/reports, .agentic/outbox, generated JSON, or logs",
                    "tail or grep excerpts as chat output for long workflows",
                    "large terminal output pasted directly into chat",
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
    general_contract = contract.get("general_contract", {})
    current_state_contract = contract.get("current_state_contract", {})
    projection_contract = contract.get("handoff_projection_contract", {})

    lines = [
        "## Machine-readable execution contract",
        "",
        "The markdown successor prompt is a compact projection. The machine-readable files take precedence.",
        "",
        "Read first: `execution_contract.json`, `successor_context.yaml`, `validation_report.json`, and `source_manifest.json`.",
        "",
        "## Durable agentic-kit operating model",
        "",
        f"- scope: `{general_contract.get('scope', 'UNKNOWN')}`",
        "- agentic-kit wrappers are the authoritative control plane.",
        "- Use the rule system, command reference, documentation registry, project direction authority, the `agentic-kit project-direction` command, the `agentic-kit docs-reconciliation` command, gates, evidence logs, report-retention GC, and successor handoff package as active subsystems.",
        "- GC is technical retention, not semantic documentation migration.",
        "- Historical `ns` migration documents are not active rule locations.",
        "",
        "Source authorities:",
    ]
    for source in general_contract.get("source_authorities", []):
        lines.append(f"- `{source}`")

    lines.extend(
        [
            "",
            "Critical rule IDs:",
        ]
    )
    for rule in rules:
        lines.append(f"- `{rule['rule_id']}` ({rule['priority']})")

    lines.extend(
        [
            "",
            "## Current continuation state",
            "",
            f"- branch: `{repo['branch']}`",
            f"- head_matches_origin_main: `{repo['head_matches_origin_main']}`",
            f"- worktree_clean: `{repo['worktree_clean']}`",
            f"- open_tasks_source: `{current_state_contract.get('open_tasks_source', 'UNKNOWN')}`",
            f"- document_registry_source: `{current_state_contract.get('document_registry_source', 'UNKNOWN')}`",
            "- Current state is volatile continuation data, not a durable rule source.",
            "",
            "## Wrapper-first complete development cycle",
            "",
            "Normal feature lifecycle: feature branch -> tests/audits -> `transfer protected-diff-plan` -> `transfer commit` -> `rules acknowledge` -> fresh successor/LLM context -> `transfer pr-create-complete ... --post-merge-complete` -> sync main -> `transfer post-merge-check` on main -> `transfer repo-status` -> docs/program/standard gates -> final successor handoff package.",
            "",
            "`transfer post-merge-check` is a main/post-merge lifecycle check, not a feature-branch pre-PR gate. Use `transfer repo-status` for feature-branch cleanliness.",
            "",
            "## Handoff package precedence",
            "",
            f"- prompt_is_projection_only: `{projection_contract.get('prompt_is_projection_only')}`",
            f"- machine_readable_files_take_precedence: `{projection_contract.get('machine_readable_files_take_precedence')}`",
            f"- source_of_truth: `{projection_contract.get('source_of_truth')}`",
            f"- generator_command: `{projection_contract.get('generator_command')}`",
            "- Markdown handoff files and latest package files are generated projections; update generator/contract/rule sources first, then regenerate projections.",
            "- Forbidden update path: manual direct edits to generated handoff projections as the primary source of new rules.",
            "- Do not use stale copied prompt text or `NEW_CHAT_HANDOFF_PROMPT.md` as sole authority.",
            "",
            "## Patch-cycle diagnostic gate",
            "",
            "After one failed patch, exactly one direct correction is allowed. After a second failure in the same patch family, stop mutations, run bounded diagnosis, classify product bug versus test-model bug, and record `next_mutation_allowed`.",
            "",
            "## Local copy-and-paste protocol",
            "",
            "Use exactly one complete Bash block per local action. The block must start by changing into the repository root, write verbose output to `~/Downloads/*.log`, and end by printing `LOG=...` and `RC=...`.",
            "",
            "Chat output after local blocks should be only `LOG=...` and `RC=...`; large diagnostics belong in compact JSON summaries or log files.",
            "",
            "Forbidden local-command patterns: loose command fragments, manual editor instructions, naked `python`, naked `pytest`, `git add .`, `{ ... } > \"$OUT\" 2>&1` as the recommended logging pattern, `cat` of whole diagnostic files, and unbounded grep over reports/outbox/generated logs.",
            "",
        ]
    )
    return "\n".join(lines)


def render_successor_prompt(context: dict[str, Any], ws: Workspace | None = None) -> str:
    ws = ws or _LEGACY_WORKSPACE
    contract = build_execution_contract(context, ws)
    contract_projection = render_execution_contract_projection(contract)
    repo = context["repo"]
    package_files = [
        ws.package_file("successor_context.yaml"),
        ws.package_file("source_manifest.json"),
        ws.package_file("validation_report.json"),
        ws.package_file("execution_contract.json"),
        ws.handoff_file("NEXT_CHAT_BOOTSTRAP.md"),
        ws.handoff_file("START_NEW_CHAT_PROMPT.md"),
        ws.handoff_file("CLOSEOUT_BEFORE_CHAT_SWITCH_PROMPT.md"),
        ws.reference_file("AGENTIC_KIT_COMMANDS.md"),
        ws.reference_file("agentic-kit-commands.json"),
    ]
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
            *(f"- `{_workspace_path_text(ws, path)}`" for path in package_files),
            "",
            "## Bootstrap-Akzeptanzbremse",
            "",
            BOOTSTRAP_ACCEPTANCE_GATE_PROMPT.rstrip(),
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
            "- Aktive Aufgaben stammen aus `docs/planning/PROJECT_DIRECTION.yaml`; alte Planungsdokumente sind keine Startautorität.",
            "- Allgemeingültige Regeln stehen in `execution_contract.json.general_contract`; aktueller Fortsetzungspunkt steht in `execution_contract.json.current_state_contract` und `successor_context.yaml`.",
            "- `successor_prompt.md` ist nur Projektion. Maschinenlesbare Dateien haben Vorrang.",
            "- Komplexe `agentic-kit`-Wrapper haben Vorrang vor selbstgebauten Git-/GitHub-/Handoff-/GC-/Release-Blöcken.",
            "- Garbage Collector nur für technische Retention verwenden, nicht für semantische Dokumentenmigration.",
            "",
            "## Nächste sichere Entscheidung",
            "",
            "1. Wenn `validation_report.json` nicht PASS ist: Handoff-Projektion reparieren.",
            "2. Wenn der Arbeitsbaum dirty ist: nur explizite WIP-Dateien prüfen und abschließen oder sauber dokumentieren.",
            "3. Danach die nächste aktive Aufgabe aus `docs/planning/PROJECT_DIRECTION.yaml` bearbeiten.",
            "",
        ]
    )


def _format_open_tasks_for_bootstrap(context: dict[str, Any]) -> list[str]:
    tasks = context.get("short_term_memory", {}).get("open_tasks", [])
    lines: list[str] = []
    if not isinstance(tasks, list):
        return ["- No structured open task list available; inspect `successor_context.yaml`."]
    for task in tasks:
        if not isinstance(task, dict):
            continue
        task_id = str(task.get("id", "unknown-task"))
        status = str(task.get("status", "unknown"))
        summary = str(task.get("summary", "")).strip()
        if summary:
            lines.append(f"- `{task_id}` ({status}): {summary}")
        else:
            lines.append(f"- `{task_id}` ({status})")
    return lines or ["- No open tasks recorded."]


def render_next_chat_bootstrap_from_context(context: dict[str, Any], ws: Workspace | None = None) -> str:
    ws = ws or _LEGACY_WORKSPACE
    repo = context["repo"]
    successor_context_path = _workspace_path_text(ws, ws.package_file("successor_context.yaml"))
    source_manifest_path = _workspace_path_text(ws, ws.package_file("source_manifest.json"))
    validation_report_path = _workspace_path_text(ws, ws.package_file("validation_report.json"))
    successor_prompt_path = _workspace_path_text(ws, ws.package_file("successor_prompt.md"))
    start_prompt_path = _workspace_path_text(ws, ws.handoff_file("START_NEW_CHAT_PROMPT.md"))
    closeout_prompt_path = _workspace_path_text(ws, ws.handoff_file("CLOSEOUT_BEFORE_CHAT_SWITCH_PROMPT.md"))
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
            f"- Handoff freshness marker: `{repo['head_short']}`",
            f"- Branch at generation: `{repo['branch']}`",
            f"- Worktree clean at generation: `{repo['worktree_clean']}`",
            "",
            "## Successor handoff package",
            "",
            f"- `{successor_context_path}`",
            f"- `{source_manifest_path}`",
            f"- `{validation_report_path}`",
            f"- `{successor_prompt_path}`",
            "",
            "## Canonical chat-switch prompt files",
            "",
            f"- Start a successor chat with `{start_prompt_path}`.",
            f"- Before leaving a chat, run the closeout routine in `{closeout_prompt_path}`.",
            "",
            "## Bootstrap-Akzeptanzbremse",
            "",
            BOOTSTRAP_ACCEPTANCE_GATE_PROMPT.rstrip(),
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
            "Source: `docs/planning/PROJECT_DIRECTION.yaml`.",
            "",
            *_format_open_tasks_for_bootstrap(context),
            "",
            "### RESULT: PASS ###",
            "",
        ]
    )



BOOTSTRAP_ACCEPTANCE_GATE_RULE_ID = "bootstrap_acceptance_gate"

BOOTSTRAP_ACCEPTANCE_GATE_PROMPT = """\
Zusätzliche Startbremse nach dem Bootstrap:

Nach Ausführung des Bootstrap-Blocks darfst du nicht sofort mit neuer Arbeit beginnen. Werte zuerst ausschließlich das Bootstrap-Log aus.

Prüfe:
- `RC=0`
- `RESULT=NEW_CHAT_BOOTSTRAP_DONE`
- `main == origin/main`
- Worktree clean
- `post-merge-check PASS` mit `refresh_required=False`, `result=NOOP`, `next_safe_action=none`
- Wenn `validation_report.generated_head` vom aktuellen HEAD abweicht, akzeptiere nur die
  durch `post-merge-check` geloggte Evidence `successor_package_head_status=refresh_only_descendant`;
  sonst `BLOCK`.
- `repo-status PASS`
- `docs-audit PASS`
- `validation_report.json PASS`
- `execution_contract.json` wurde gelesen

Gib danach genau eine kurze Statusentscheidung aus:

- `Übergabe akzeptiert, keine Admin-Arbeit nötig.`

oder:

- `BLOCK: ...` mit konkretem Grund aus dem Log.

Beginne erst nach dieser Statusentscheidung mit neuer Arbeit.

Wenn der Bootstrap grün ist:
- PR #1304 nicht erneut validieren.
- Übergabedateien nicht neu erzeugen.
- `prepare-successor-handoff --render-prompt` nicht erneut ausführen.
- Keine Admin-Refresh-Arbeit starten.
- Neue Produktarbeit nur aus frischem, sauberem `main` beginnen.
"""

def render_start_prompt_from_context(context: dict[str, Any], ws: Workspace | None = None) -> str:
    ws = ws or _LEGACY_WORKSPACE
    repo = context["repo"]
    next_chat_bootstrap_path = _workspace_path_text(ws, ws.handoff_file("NEXT_CHAT_BOOTSTRAP.md"))
    successor_context_path = _workspace_path_text(ws, ws.package_file("successor_context.yaml"))
    start_prompt_path = _workspace_path_text(ws, ws.handoff_file("START_NEW_CHAT_PROMPT.md"))
    closeout_prompt_path = _workspace_path_text(ws, ws.handoff_file("CLOSEOUT_BEFORE_CHAT_SWITCH_PROMPT.md"))
    successor_prompt_path = _workspace_path_text(ws, ws.package_file("successor_prompt.md"))
    return "\n".join(
        [
            "---",
            "schema_version: 2",
            "artifact_type: chat_switch_prompt",
            "role: start_new_chat",
            f"current_handoff_marker: {repo['head_short']}",
            f"current_branch_at_generation: {repo['branch']}",
            f"canonical_bootstrap: {next_chat_bootstrap_path}",
            f"successor_context: {successor_context_path}",
            f"paired_prompt: {closeout_prompt_path}",
            "must_update_together:",
            f"  - {start_prompt_path}",
            f"  - {closeout_prompt_path}",
            f"  - {next_chat_bootstrap_path}",
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
            f"Current handoff marker: `{repo['head_short']}`.",
            "",
            f"Copy `{successor_prompt_path}` into the successor chat.",
            "",
            "The successor chat must treat the Successor Handoff Package as the short-term handoff and the repository files listed in `source_manifest.json` as long-term truth.",
            "",
            "If the package validation is not PASS, or if HEAD/local status differs from the package without explanation, stop and repair handoff drift first.",
            "",
            BOOTSTRAP_ACCEPTANCE_GATE_PROMPT.rstrip(),
            "",
        ]
    )


def render_closeout_prompt_from_context(context: dict[str, Any], ws: Workspace | None = None) -> str:
    ws = ws or _LEGACY_WORKSPACE
    next_chat_bootstrap_path = _workspace_path_text(ws, ws.handoff_file("NEXT_CHAT_BOOTSTRAP.md"))
    successor_context_path = _workspace_path_text(ws, ws.package_file("successor_context.yaml"))
    start_prompt_path = _workspace_path_text(ws, ws.handoff_file("START_NEW_CHAT_PROMPT.md"))
    closeout_prompt_path = _workspace_path_text(ws, ws.handoff_file("CLOSEOUT_BEFORE_CHAT_SWITCH_PROMPT.md"))
    return "\n".join(
        [
            "---",
            "schema_version: 2",
            "artifact_type: chat_switch_prompt",
            "role: closeout_before_chat_switch",
            f"canonical_bootstrap: {next_chat_bootstrap_path}",
            f"successor_context: {successor_context_path}",
            f"paired_prompt: {start_prompt_path}",
            "must_update_together:",
            f"  - {start_prompt_path}",
            f"  - {closeout_prompt_path}",
            f"  - {next_chat_bootstrap_path}",
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
            "cd /path/to/agentic-project-kit",
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


def _build_successor_handoff_package(root_path: Path, ws: Workspace) -> SuccessorPackageResult:
    context = _build_context(root_path, ws)
    source_manifest = _source_manifest(root_path, ws)
    successor_prompt = render_successor_prompt(context, ws)
    successor_prompt = ensure_command_reference_in_prompt(successor_prompt, ws.root)
    next_chat_bootstrap = render_next_chat_bootstrap_from_context(context, ws)
    start_prompt = render_start_prompt_from_context(context, ws)
    closeout_prompt = render_closeout_prompt_from_context(context, ws)
    provisional_execution_contract = build_execution_contract(context, ws)
    validation_report = validate_successor_outputs(
        {
            _workspace_path_text(ws, ws.handoff_file("NEXT_CHAT_BOOTSTRAP.md")): next_chat_bootstrap,
            _workspace_path_text(ws, ws.handoff_file("START_NEW_CHAT_PROMPT.md")): start_prompt,
            _workspace_path_text(ws, ws.handoff_file("CLOSEOUT_BEFORE_CHAT_SWITCH_PROMPT.md")): closeout_prompt,
            "successor_prompt.md": successor_prompt,
            "execution_contract.json": _json_block(provisional_execution_contract),
        },
        context,
        ws,
    )
    context["handoff_validity"]["status"] = validation_report["status"]
    execution_contract = build_execution_contract({**context, "validation_report": validation_report}, ws)
    return SuccessorPackageResult(
        context=context,
        source_manifest=source_manifest,
        validation_report=validation_report,
        execution_contract=execution_contract,
        successor_prompt=successor_prompt,
        next_chat_bootstrap=next_chat_bootstrap,
        start_new_chat_prompt=start_prompt,
        closeout_prompt=closeout_prompt,
        output_dir=Path(_workspace_path_text(ws, ws.handoff_packages_latest())),
    )


def build_successor_handoff_package(root: Path | str = ".") -> SuccessorPackageResult:
    root_path = Path(root)
    ws = load_workspace(root_path)
    return _build_successor_handoff_package(root_path, ws)


def write_successor_handoff_package(
    root: Path | str = ".",
    output_dir: Path | str = DEFAULT_PACKAGE_DIR,
    *,
    update_canonical_prompts: bool = True,
) -> SuccessorPackageResult:
    root_path = Path(root)
    ws = load_workspace(root_path)
    result = _build_successor_handoff_package(root_path, ws)
    out = root_path / output_dir
    out.mkdir(parents=True, exist_ok=True)
    (out / "successor_context.yaml").write_text(_json_block(result.context) + "\n", encoding="utf-8")
    (out / "source_manifest.json").write_text(_json_block(result.source_manifest) + "\n", encoding="utf-8")
    (out / "validation_report.json").write_text(_json_block(result.validation_report) + "\n", encoding="utf-8")
    (out / "execution_contract.json").write_text(_json_block(result.execution_contract) + "\n", encoding="utf-8")
    (out / "successor_prompt.md").write_text(result.successor_prompt, encoding="utf-8")
    # START_NEW_CHAT_PROMPT is protected against broad generator replacement. The
    # successor package refresh updates NEXT_CHAT_BOOTSTRAP, the closeout prompt,
    # and package files; START_NEW_CHAT_PROMPT must be changed only by a dedicated
    # minimal handoff-refresh/admin slice.
    if update_canonical_prompts:
        for rel, text in (
            (ws.handoff_file("NEXT_CHAT_BOOTSTRAP.md"), result.next_chat_bootstrap),
            (ws.handoff_file("CLOSEOUT_BEFORE_CHAT_SWITCH_PROMPT.md"), result.closeout_prompt),
        ):
            path = root_path / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
    return result
