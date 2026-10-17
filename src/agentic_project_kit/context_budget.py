"""Context budget: measure what a successor LLM reads and render task-specific packets.

Plan item ``context-budgeted-handoff-projections`` and part 2 of ``gate-and-context-benchmark``
(docs/planning/PROJECT_DIRECTION.yaml). Two read-only functions:

- :func:`context_report` measures the context carriers a successor is told to read today
  (baseline B) and the task-specific packets (condition C) rendered from the same sources.
- :func:`render_packet` renders a deterministic packet for one task profile. It quotes the
  Kit's own authorities (command manifest entries, execution-contract rules, Direction items)
  and points to every longer source by path, size and hash instead of repeating it. No LLM
  summary is involved; the same repository state always renders the same packet.

Token counts are estimates: ``ceil(characters / 4)``. The same estimator is used for B and C,
so ratios are comparable; absolute numbers differ from any specific tokenizer.

A packet does not change any rule. Whether a packet may replace the mandatory full-manifest
read is an owner decision after the benchmark.
"""

from __future__ import annotations

import hashlib
import json
import math
import subprocess
from pathlib import Path
from typing import Any

import yaml

from agentic_project_kit.command_manifest import JSON_PATH as MANIFEST
from agentic_project_kit.workspace import load_workspace

PACKET_DIR = Path(".agentic/tmp/context")

# Baseline B: what a successor is told to read before working (each entry cites its source).
SUCCESSOR_REQUIRED_READS: tuple[tuple[str, str], ...] = (
    ("docs/reports/handoff-packages/latest/successor_prompt.md", "START_NEW_CHAT_PROMPT.md: copy into the successor chat"),
    ("docs/reports/handoff-packages/latest/execution_contract.json", "successor_prompt.md: Read first"),
    ("docs/reports/handoff-packages/latest/successor_context.yaml", "successor_prompt.md: Read first"),
    ("docs/reports/handoff-packages/latest/validation_report.json", "successor_prompt.md: Read first"),
    ("docs/reports/handoff-packages/latest/source_manifest.json", "successor_prompt.md: Read first"),
    ("docs/handoff/NEXT_CHAT_BOOTSTRAP.md", "START_NEW_CHAT_PROMPT.md: canonical_bootstrap"),
    ("AGENTS.md", "source_manifest.json and START_NEW_CHAT_PROMPT.md required_terms"),
    ("docs/reference/agentic-kit-commands.json", "AGENTS.md / successor_prompt.md: MANDATORY FIRST READ"),
    ("docs/reference/AGENTIC_KIT_COMMANDS.md", "successor_prompt.md: read before composing agentic-kit commands"),
)

PROFILES: dict[str, dict[str, Any]] = {
    "slice": {
        "purpose": "Implement one bugfix or feature slice from work start to a merged PR.",
        "commands": [
            "agentic-kit rules acknowledge",
            "agentic-kit work start",
            "agentic-kit transfer commit",
            "agentic-kit work finish",
            "agentic-kit transfer post-merge-check",
            "agentic-kit transfer repo-status",
            "agentic-kit commands sync-entrypoints",
            "agentic-kit doc-registry register",
            "agentic-kit command-for",
        ],
        "gates": [
            "ruff check .",
            "python -m pytest -q -n 4",
            "agentic-kit check-docs",
            "agentic-kit docs-audit",
            "agentic-kit doctor",
            "agentic-kit audit-command-authority",
            "agentic-kit direction validate",
            "agentic-kit doc-registry check-unregistered --strict-scope",
        ],
    },
    "planning": {
        "purpose": "Change docs/planning/PROJECT_DIRECTION.yaml or a planning document.",
        "commands": [
            "agentic-kit rules acknowledge",
            "agentic-kit work start",
            "agentic-kit work finish",
            "agentic-kit direction validate",
            "agentic-kit direction audit-drift",
            "agentic-kit project-direction",
            "agentic-kit doc-registry register",
            "agentic-kit command-for",
        ],
        "gates": [
            "agentic-kit direction validate",
            "agentic-kit check-docs",
            "agentic-kit docs-audit",
            "agentic-kit doctor",
            "python -m pytest -q -n 4",
        ],
    },
    "release": {
        "purpose": "Prepare, publish and close out a Kit release after the owner's go.",
        "commands": [
            "agentic-kit rules acknowledge",
            "agentic-kit release prepare",
            "agentic-kit release ready",
            "agentic-kit release run",
            "agentic-kit release-publish",
            "agentic-kit post-release-doi-closeout",
            "agentic-kit transfer post-merge-check",
            "agentic-kit command-for",
        ],
        "gates": [
            "agentic-kit release ready",
            "agentic-kit doctor",
            "agentic-kit post-release-doi-closeout",
        ],
    },
    "handoff": {
        "purpose": "Close out a chat and hand over to a successor.",
        "commands": [
            "agentic-kit rules acknowledge",
            "agentic-kit transfer chat-switch-complete",
            "agentic-kit transfer post-merge-check",
            "agentic-kit handoff check",
            "agentic-kit transfer repo-status",
            "agentic-kit command-for",
        ],
        "gates": [
            "agentic-kit transfer post-merge-check",
            "agentic-kit handoff check",
            "agentic-kit docs-audit",
        ],
    },
}


def estimate_tokens(text: str) -> int:
    return math.ceil(len(text) / 4)


def _sha12(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()[:12]


def _measure(root: Path, paths: list[str]) -> dict[str, Any]:
    files = []
    for rel in paths:
        path = root / rel
        if not path.is_file():
            files.append({"path": rel, "exists": False})
            continue
        data = path.read_bytes()
        text = data.decode("utf-8", errors="replace")
        files.append({
            "path": rel,
            "exists": True,
            "bytes": len(data),
            "characters": len(text),
            "estimated_tokens": estimate_tokens(text),
            "sha256_12": _sha12(data),
        })
    present = [item for item in files if item["exists"]]
    return {
        "file_count": len(present),
        "missing": [item["path"] for item in files if not item["exists"]],
        "bytes": sum(item["bytes"] for item in present),
        "estimated_tokens": sum(item["estimated_tokens"] for item in present),
        "files": sorted(present, key=lambda item: -item["estimated_tokens"]),
    }


def _package_file(root: Path, name: str) -> Path:
    return load_workspace(root, suppress_legacy_profile_warning=True).package_file(name)


def _source_manifest_paths(root: Path) -> list[str]:
    path = _package_file(root, "source_manifest.json")
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return [str(item["path"]) for item in data.get("sources", []) if isinstance(item, dict) and item.get("path")]


def _git(root: Path, *args: str) -> str:
    completed = subprocess.run(["git", *args], cwd=root, text=True, capture_output=True, check=False)
    return completed.stdout.strip() if completed.returncode == 0 else ""


def _manifest(root: Path) -> dict[str, Any]:
    return json.loads((root / MANIFEST).read_text(encoding="utf-8"))


def _command_lines(manifest: dict[str, Any], names: list[str]) -> list[str]:
    by_name = {str(c.get("qualified_name")): c for c in manifest.get("commands", []) if isinstance(c, dict)}
    lines = []
    for name in names:
        command = by_name.get(name)
        if command is None:
            raise KeyError(f"profile command not in the manifest: {name}")
        options = []
        for param in command.get("params") or []:
            opts = [str(opt) for opt in (param.get("opts") or []) if str(opt).startswith("-")]
            secondary = [str(opt) for opt in (param.get("secondary_opts") or []) if str(opt).startswith("-")]
            if opts and secondary:
                options.append(f"{opts[0]}/{secondary[0]}")
            elif opts:
                options.append(opts[0] + ("" if param.get("is_flag") else " <value>"))
            elif param.get("name"):
                options.append(f"<{param['name']}>")
        effects = ",".join(command.get("remote_effects") or [])
        summary = " ".join(str(command.get("help") or command.get("when_to_use") or "").split())
        lines.append(
            f"- `{name}` ({command.get('surface')}, {command.get('safety')}, remote: {effects}): {summary}"
            + (f" Options: {' '.join(options)}." if options else "")
        )
    return lines


def _contract_rules(root: Path) -> list[str]:
    path = _package_file(root, "execution_contract.json")
    if not path.exists():
        return ["- execution_contract.json is missing; regenerate the successor package first."]
    lines = []
    for rule in json.loads(path.read_text(encoding="utf-8")).get("rules", []):
        lines.append(f"- `{rule.get('rule_id')}` ({rule.get('priority')})")
        lines.extend(f"  - must: {item}" for item in rule.get("must") or [])
        lines.extend(f"  - forbidden: {item}" for item in rule.get("forbidden") or [])
    return lines


def _open_direction_items(root: Path) -> list[str]:
    path = load_workspace(root, suppress_legacy_profile_warning=True).project_direction_path()
    if not path.exists():
        return []
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    lines = []
    for section in ("roadmap", "plans"):
        for item in data.get(section) or []:
            if not isinstance(item, dict) or item.get("status") not in {"active", "next"}:
                continue
            lines.append(f"- {section} `{item.get('id')}` ({item.get('status')}): {item.get('title')}")
            for step in item.get("steps") or []:
                if isinstance(step, dict) and step.get("status") in {"active", "next"}:
                    lines.append(f"  - step `{step.get('id')}` ({step.get('status')})")
    return lines


def render_packet(root: Path, profile: str) -> str:
    if profile not in PROFILES:
        raise KeyError(f"unknown context profile: {profile}; known: {', '.join(sorted(PROFILES))}")
    spec = PROFILES[profile]
    manifest = _manifest(root)
    meta = manifest.get("meta") or {}
    sha = str(meta.get("manifest_sha") or "")
    on_demand = _measure(root, sorted({path for path, _ in SUCCESSOR_REQUIRED_READS} | set(_source_manifest_paths(root))))
    lines = [
        f"# Kit context packet: {profile}",
        "",
        f"Generated deterministically by `agentic-kit context render --profile {profile}` from repository authorities;",
        "it quotes them and points to longer sources by path and hash. No LLM summary is involved.",
        "",
        f"COMMAND_MANIFEST_ACK {sha}",
        "",
        "## Task profile",
        "",
        f"- {spec['purpose']}",
        "",
        "## Repository state",
        "",
        f"- origin: `{_git(root, 'remote', 'get-url', 'origin')}`",
        f"- branch: `{_git(root, 'branch', '--show-current')}`; HEAD: `{_git(root, 'rev-parse', 'HEAD')}`",
        f"- origin/main: `{_git(root, 'rev-parse', 'origin/main')}`",
        f"- command manifest: `{MANIFEST.as_posix()}` (manifest_sha `{sha}`, {len(manifest.get('commands', []))} commands)",
        "",
        "## Command authority",
        "",
        "- The commands below are excerpts of the command manifest. For any other command run",
        "  `agentic-kit command-for \"<intent>\"` or read its manifest entry; never reconstruct commands from memory.",
        "- Stop on BLOCKED or FAIL and diagnose from the Kit's own output; do not bypass a gate.",
        "",
        "## Commands for this task",
        "",
        *_command_lines(manifest, spec["commands"]),
        "",
        "## Gates before finishing",
        "",
        *[f"- `{gate}`" for gate in spec["gates"]],
        "",
        "## Execution contract rules",
        "",
        *_contract_rules(root),
        "",
        "## Open Direction items",
        "",
        *(_open_direction_items(root) or ["- none"]),
        "",
        "## Sources on demand",
        "",
        "Read these only when the task needs them; the hashes identify the exact version.",
        "",
        *[f"- `{item['path']}` ({item['bytes']} bytes, sha256 {item['sha256_12']})" for item in sorted(on_demand["files"], key=lambda f: f["path"])],
        "",
    ]
    return "\n".join(lines)


def context_report(root: Path) -> dict[str, Any]:
    baseline = _measure(root, [path for path, _ in SUCCESSOR_REQUIRED_READS])
    long_term = _measure(root, _source_manifest_paths(root))
    packets = {}
    for name in sorted(PROFILES):
        text = render_packet(root, name)
        tokens = estimate_tokens(text)
        packets[name] = {
            "characters": len(text),
            "estimated_tokens": tokens,
            "share_of_baseline": round(tokens / baseline["estimated_tokens"], 4) if baseline["estimated_tokens"] else None,
        }
    return {
        "schema_version": 1,
        "kind": "context_budget_report",
        "result_status": "PASS",
        "estimator": "ceil(characters / 4)",
        "baseline_successor_required_reads": {
            **baseline,
            "sources": {path: source for path, source in SUCCESSOR_REQUIRED_READS},
        },
        "source_manifest_long_term_truth": {key: value for key, value in long_term.items() if key != "files"}
        | {"largest": long_term["files"][:5]},
        "packets": packets,
    }


def render_context_report(report: dict[str, Any]) -> str:
    baseline = report["baseline_successor_required_reads"]
    long_term = report["source_manifest_long_term_truth"]
    lines = [
        "CONTEXT_BUDGET_REPORT",
        f"STATUS={report['result_status']}",
        f"ESTIMATOR={report['estimator']}",
        f"BASELINE_REQUIRED_READS_FILES={baseline['file_count']}",
        f"BASELINE_REQUIRED_READS_TOKENS={baseline['estimated_tokens']}",
        f"SOURCE_MANIFEST_FILES={long_term['file_count']}",
        f"SOURCE_MANIFEST_TOKENS={long_term['estimated_tokens']}",
    ]
    for item in baseline["files"]:
        lines.append(f"BASELINE_FILE={item['path']}|tokens={item['estimated_tokens']}")
    for name, packet in report["packets"].items():
        lines.append(f"PACKET={name}|tokens={packet['estimated_tokens']}|share_of_baseline={packet['share_of_baseline']}")
    return "\n".join(lines)
