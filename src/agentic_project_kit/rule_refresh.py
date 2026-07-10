from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from agentic_project_kit.workspace import LEGACY_DEFAULTS, Workspace, load_workspace

COMMUNICATION_RULE_SOURCES = (
    "docs/workflow/NO_COPY_TERMINAL_EVIDENCE.md",
    "docs/governance/CHAT_COMMUNICATION_CONTRACT.md",
    "docs/governance/PORTABLE_CHAT_EXECUTION_CONTRACT.md",
    "docs/governance/CHAT_BOOTSTRAP_AND_DRIFT_CONTRACT.md",
    ".agentic/compiled_agent_context.yaml",
    ".agentic/handoff_state.yaml",
)

HANDOFF_RULE_SOURCES = (
    "docs/handoff/CURRENT_HANDOFF.md",
    "docs/handoff/START_NEW_CHAT_PROMPT.md",
    "docs/handoff/CLOSEOUT_BEFORE_CHAT_SWITCH_PROMPT.md",
    "docs/governance/CHAT_BOOTSTRAP_AND_DRIFT_CONTRACT.md",
    "docs/governance/PORTABLE_CHAT_EXECUTION_CONTRACT.md",
    ".agentic/handoff_state.yaml",
    ".agentic/compiled_agent_context.yaml",
)

COMMUNICATION_RULES_OUTPUT = Path(LEGACY_DEFAULTS.reports_root) / "communication_rules" / "CURRENT_COMMUNICATION_RULES.md"
HANDOFF_RULES_OUTPUT = Path(LEGACY_DEFAULTS.reports_root) / "handoff_rules" / "CURRENT_HANDOFF_RULES.md"


@dataclass(frozen=True)
class RuleRefreshResult:
    output_path: str
    source_paths: tuple[str, ...]
    missing_paths: tuple[str, ...]
    next_reply: str
    instruction: str


def refresh_communication_rules(project_root: Path = Path(".")) -> RuleRefreshResult:
    return _write_rule_file(
        project_root.resolve(),
        title="Current communication rules refresh",
        output_path=COMMUNICATION_RULES_OUTPUT,
        sources=COMMUNICATION_RULE_SOURCES,
        next_reply="d2",
        instruction=(
            "On user reply d2, read this generated file before continuing and refresh "
            "the active dialog rules from the repo-backed source snapshots."
        ),
    )


def refresh_handoff_rules(project_root: Path = Path(".")) -> RuleRefreshResult:
    return _write_rule_file(
        project_root.resolve(),
        title="Current handoff rules refresh",
        output_path=HANDOFF_RULES_OUTPUT,
        sources=HANDOFF_RULE_SOURCES,
        next_reply="d3",
        instruction=(
            "On user reply d3, read this generated file before continuing and start "
            "the documented handoff mechanism from the repo-backed source snapshots."
        ),
    )


def rule_refresh_result_as_json_data(result: RuleRefreshResult) -> dict[str, object]:
    return {
        "schema_version": 1,
        "output_path": result.output_path,
        "source_paths": list(result.source_paths),
        "missing_paths": list(result.missing_paths),
        "next_reply": result.next_reply,
        "instruction": result.instruction,
    }


def render_rule_refresh_result(result: RuleRefreshResult) -> str:
    lines = [
        "RULE_REFRESH_RESULT",
        f"output_path={result.output_path}",
        f"next_reply={result.next_reply}",
        f"instruction={result.instruction}",
    ]
    for source in result.source_paths:
        lines.append(f"source_path={source}")
    for missing in result.missing_paths:
        lines.append(f"missing_path={missing}")
    return "\n".join(lines)


def _write_rule_file(
    project_root: Path,
    *,
    title: str,
    output_path: Path,
    sources: tuple[str, ...],
    next_reply: str,
    instruction: str,
) -> RuleRefreshResult:
    workspace = load_workspace(project_root)
    source_texts: list[tuple[str, str]] = []
    missing: list[str] = []
    for rel in sources:
        path = project_root / rel
        if path.exists() and path.is_file():
            source_texts.append((rel, path.read_text(encoding="utf-8")))
        else:
            missing.append(rel)

    output = _rule_output_path(workspace, output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        _render_rule_file(title, source_texts, missing, next_reply, instruction),
        encoding="utf-8",
    )
    return RuleRefreshResult(
        workspace.path_text(output),
        tuple(rel for rel, _text in source_texts),
        tuple(missing),
        next_reply,
        instruction,
    )


def _rule_output_path(workspace: Workspace, output_path: Path) -> Path:
    if output_path == COMMUNICATION_RULES_OUTPUT:
        return workspace.communication_rules_output_path()
    if output_path == HANDOFF_RULES_OUTPUT:
        return workspace.handoff_rules_output_path()
    return output_path if output_path.is_absolute() else workspace.root / output_path


def _render_rule_file(
    title: str,
    source_texts: list[tuple[str, str]],
    missing: list[str],
    next_reply: str,
    instruction: str,
) -> str:
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    parts = [
        f"# {title}",
        "",
        "Status: generated",
        f"Generated at: {generated_at}",
        f"Next reply trigger: `{next_reply}`",
        "",
        "## Assistant instruction",
        "",
        instruction,
        "",
        "## Source files",
        "",
    ]
    parts.extend(f"- `{rel}`" for rel, _text in source_texts)
    if missing:
        parts.extend(["", "## Missing source files", ""])
        parts.extend(f"- `{rel}`" for rel in missing)
    parts.extend(["", "## Source snapshots", ""])
    for rel, text in source_texts:
        parts.extend(
            [
                f"### `{rel}`",
                "",
                "```text",
                text.rstrip(),
                "```",
                "",
            ]
        )
    return "\n".join(parts).rstrip() + "\n"
