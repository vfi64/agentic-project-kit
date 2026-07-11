from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from typer.main import get_command

from agentic_project_kit.workspace import LEGACY_DEFAULTS, load_workspace

JSON_PATH = Path(LEGACY_DEFAULTS.reference_root) / "agentic-kit-commands.json"
MD_PATH = Path(LEGACY_DEFAULTS.reference_root) / "AGENTIC_KIT_COMMANDS.md"
SAFETY_VALUES = {"READ_ONLY", "BOUNDED", "DESTRUCTIVE"}

RAW_REPLACEMENTS: dict[str, tuple[str, ...]] = {
    "agentic-kit transfer push-current": ("git push",),
    "agentic-kit transfer commit": ("git commit",),
    "agentic-kit transfer branch-create": ("git switch -c", "git checkout -b"),
    "agentic-kit transfer pr-create-complete": ("gh pr create",),
    "agentic-kit transfer pr-merge-safe": ("gh pr merge",),
    "agentic-kit transfer delete-merged-work-branch": ("git push --delete", "git branch -D"),
    "agentic-kit release ready": ("git tag", "gh release create"),
}


@dataclass(frozen=True)
class CommandManifestFinding:
    severity: str
    code: str
    message: str

    def as_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class CommandManifestAudit:
    root: str
    findings: tuple[CommandManifestFinding, ...]

    @property
    def blockers(self) -> tuple[CommandManifestFinding, ...]:
        return tuple(finding for finding in self.findings if finding.severity == "BLOCK")

    @property
    def ok(self) -> bool:
        return not self.blockers

    @property
    def status(self) -> str:
        return "PASS" if self.ok else "BLOCK"

    @property
    def returncode(self) -> int:
        return 0 if self.ok else 2

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "kind": "command_manifest_audit",
            "root": self.root,
            "status": self.status,
            "finding_count": len(self.findings),
            "blocker_count": len(self.blockers),
            "findings": [finding.as_dict() for finding in self.findings],
        }


def manifest_sha(commands: list[dict[str, Any]]) -> str:
    canonical = json.dumps(commands, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()[:12]


def _jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    return repr(value)


def _param_record(param: Any) -> dict[str, Any]:
    record: dict[str, Any] = {
        "name": param.name,
        "param_type": param.__class__.__name__,
        "required": bool(getattr(param, "required", False)),
        "default": _jsonable(getattr(param, "default", None)),
        "metavar": getattr(param, "metavar", None),
    }
    if hasattr(param, "opts"):
        record["opts"] = list(getattr(param, "opts", []))
        record["secondary_opts"] = list(getattr(param, "secondary_opts", []))
        record["help"] = getattr(param, "help", None) or ""
        record["is_flag"] = bool(getattr(param, "is_flag", False))
        record["multiple"] = bool(getattr(param, "multiple", False))
    return record


def _record_for(path: list[str], command: Any) -> dict[str, Any]:
    group = "root" if len(path) == 1 else " ".join(path[:-1])
    qualified_name = "agentic-kit " + " ".join(path)
    params = [_param_record(param) for param in command.params]
    command_record: dict[str, Any] = {
        "group": group,
        "name": path[-1],
        "path": path,
        "qualified_name": qualified_name,
        "help": command.help or "",
        "params": params,
    }
    return _with_manifest_fields(command_record)


def _walk(path: list[str], command: Any) -> list[dict[str, Any]]:
    commands = getattr(command, "commands", None)
    if isinstance(commands, dict):
        records: list[dict[str, Any]] = []
        for name in sorted(commands):
            records.extend(_walk([*path, name], commands[name]))
        return records
    return [_record_for(path, command)]


def _leaf(command: dict[str, Any]) -> str:
    path = command.get("path")
    if isinstance(path, list) and path:
        return str(path[-1])
    return str(command.get("name") or command.get("qualified_name") or "").rsplit(" ", 1)[-1]


def _all_opts(command: dict[str, Any]) -> set[str]:
    opts: set[str] = set()
    for param in command.get("params") or []:
        if not isinstance(param, dict):
            continue
        opts.update(str(opt) for opt in param.get("opts") or [])
        opts.update(str(opt) for opt in param.get("secondary_opts") or [])
    return opts


def infer_safety(command: dict[str, Any]) -> str:
    qualified = str(command.get("qualified_name") or "")
    group = str(command.get("group") or "")
    leaf = _leaf(command)

    destructive_terms = (
        "delete",
        "merge",
        "publish",
        "release-publish",
        "branch-delete",
        "delete-merged-work-branch",
    )
    if any(term in qualified for term in destructive_terms):
        return "DESTRUCTIVE"

    read_only_leafs = {
        "check",
        "check-docs",
        "check-todo",
        "doctor",
        "status",
        "state",
        "list",
        "show",
        "report",
        "inspect",
        "head-sha",
        "lint",
        "repo-log",
        "repo-diff",
        "divergence-status",
        "require-fresh-llm-context",
        "verify-llm-context-refresh",
        "command-reference-check",
        "command-taxonomy-check",
        "standard-gates-audit-suite",
        "protected-diff-plan",
        "post-merge-check",
        "command-for",
        "render-md",
    }
    read_only_prefixes = (
        "agentic-kit audit-",
        "agentic-kit direction audit-",
        "agentic-kit docs lifecycle plan",
        "agentic-kit docs lifecycle triage",
        "agentic-kit docs removed-source-audit",
        "agentic-kit governance check",
        "agentic-kit actions list",
        "agentic-kit actions show",
        "agentic-kit cockpit status",
        "agentic-kit cockpit gatekeeper-status",
        "agentic-kit cockpit actions",
    )
    if leaf in read_only_leafs or qualified.startswith(read_only_prefixes):
        return "READ_ONLY"
    if leaf.startswith("audit-") or leaf.endswith("-audit") or leaf.startswith("validate"):
        return "READ_ONLY"
    if group in {"actions", "patterns"} and leaf in {"list", "show"}:
        return "READ_ONLY"

    return "BOUNDED"


def _task_tags(command: dict[str, Any]) -> list[str]:
    tags = []
    group = str(command.get("group") or "")
    if group and group != "root":
        tags.append(group.replace(" ", "-"))
    safety = str(command.get("safety") or infer_safety(command)).lower()
    tags.append(safety.replace("_", "-"))
    return sorted(dict.fromkeys(tags))


def _when_to_use(command: dict[str, Any]) -> str:
    help_text = str(command.get("help") or "").strip()
    if help_text:
        return help_text.splitlines()[0].strip()
    return f"Run {command.get('qualified_name')}."


def _dry_run_available(command: dict[str, Any]) -> bool:
    opts = _all_opts(command)
    return "--dry-run" in opts or "--execute" in opts


def _with_manifest_fields(command: dict[str, Any]) -> dict[str, Any]:
    enriched = dict(command)
    enriched["safety"] = str(enriched.get("safety") or infer_safety(enriched))
    enriched["task_tags"] = list(enriched.get("task_tags") or _task_tags(enriched))
    enriched["when_to_use"] = str(enriched.get("when_to_use") or _when_to_use(enriched))
    enriched["replaces_raw"] = list(
        enriched.get("replaces_raw")
        or RAW_REPLACEMENTS.get(str(enriched.get("qualified_name") or ""), ())
    )
    enriched["dry_run_available"] = bool(
        enriched.get("dry_run_available")
        if "dry_run_available" in enriched
        else _dry_run_available(enriched)
    )
    return enriched


def build_reference_from_app(app: Any) -> dict[str, Any]:
    root = get_command(app)
    commands: list[dict[str, Any]] = []
    if not hasattr(root, "commands"):
        command_name = str(getattr(root, "name", None) or "root")
        commands.append(_record_for([command_name], root))
        sha = manifest_sha(commands)
        return {
            "schema_version": 2,
            "kind": "agentic_kit_command_reference",
            "source": "generated_from_typer_click_registry",
            "generated_by": "scripts/generate_agentic_kit_command_reference.py",
            "successor_execution_contract": "docs/reports/handoff-packages/latest/execution_contract.json",
            "meta": {
                "schema_version": 1,
                "manifest_sha": sha,
                "generated_md": MD_PATH.as_posix(),
            },
            "commands": commands,
        }
    for name, command in sorted(root.commands.items()):
        nested = getattr(command, "commands", None)
        if isinstance(nested, dict):
            commands.extend(_walk([name], command))
        else:
            commands.append(_record_for([name], command))

    commands = sorted(commands, key=lambda item: item["qualified_name"])
    sha = manifest_sha(commands)
    return {
        "schema_version": 2,
        "kind": "agentic_kit_command_reference",
        "source": "generated_from_typer_click_registry",
        "generated_by": "scripts/generate_agentic_kit_command_reference.py",
        "successor_execution_contract": "docs/reports/handoff-packages/latest/execution_contract.json",
        "meta": {
            "schema_version": 1,
            "manifest_sha": sha,
            "generated_md": MD_PATH.as_posix(),
        },
        "commands": commands,
    }


def build_current_reference() -> dict[str, Any]:
    from agentic_project_kit.cli import app

    return build_reference_from_app(app)


def render_markdown(data: dict[str, Any]) -> str:
    commands = data.get("commands") or []
    meta = data.get("meta") if isinstance(data.get("meta"), dict) else {}
    sha = str(meta.get("manifest_sha") or manifest_sha(commands))
    lines = [
        "# Agentic-kit command reference",
        "",
        f"GENERATED FROM agentic-kit-commands.json — do not edit; manifest_sha: {sha}",
        "",
        "> Successor handoff contract note: the machine-readable successor execution contract is written to `docs/reports/handoff-packages/latest/execution_contract.json`. This generated command reference points to the contract instead of duplicating local-command rules.",
        "",
        f"- Schema version: `{data['schema_version']}`",
        f"- Source: `{data['source']}`",
        f"- Command count: `{len(commands)}`",
        "",
        "## Commands",
        "",
    ]
    for command in commands:
        lines.append(f"### `{command['qualified_name']}`")
        lines.append("")
        lines.append(f"- Safety: `{command.get('safety', '')}`")
        lines.append(f"- When to use: {command.get('when_to_use', '')}")
        lines.append(f"- Dry-run available: `{bool(command.get('dry_run_available'))}`")
        replaces = command.get("replaces_raw") or []
        if replaces:
            lines.append("- Replaces raw: " + ", ".join(f"`{item}`" for item in replaces))
        lines.append("")
        if command.get("help"):
            lines.append(str(command["help"]).strip())
            lines.append("")
        if command.get("params"):
            lines.append("| Parameter | Type | Options | Required | Default | Help |")
            lines.append("|---|---:|---|---:|---|---|")
            for param in command["params"]:
                opts = ", ".join(param.get("opts", []) + param.get("secondary_opts", []))
                default = "" if param.get("default") is None else f"`{param.get('default')}`"
                help_text = (param.get("help") or "").replace("\n", " ")
                lines.append(
                    f"| `{param.get('name')}` | `{param.get('param_type')}` | "
                    f"{opts} | `{param.get('required')}` | {default} | {help_text} |"
                )
            lines.append("")
        else:
            lines.append("_No parameters._")
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def write_reference(root: Path) -> dict[str, Any]:
    data = build_current_reference()
    json_path = load_workspace(root).reference_file("agentic-kit-commands.json")
    md_path = load_workspace(root).reference_file("AGENTIC_KIT_COMMANDS.md")
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(data), encoding="utf-8")
    return data


def load_manifest(root: Path) -> dict[str, Any]:
    return json.loads(load_workspace(root).reference_file("agentic-kit-commands.json").read_text(encoding="utf-8"))


def evaluate_command_manifest(root: Path = Path(".")) -> CommandManifestAudit:
    root = root.resolve()
    findings: list[CommandManifestFinding] = []
    json_path = load_workspace(root).reference_file("agentic-kit-commands.json")
    md_path = load_workspace(root).reference_file("AGENTIC_KIT_COMMANDS.md")

    try:
        committed = load_manifest(root)
    except Exception as exc:
        return CommandManifestAudit(
            root=root.as_posix(),
            findings=(CommandManifestFinding("BLOCK", "JSON_UNREADABLE", str(exc)),),
        )

    commands = committed.get("commands")
    if not isinstance(commands, list):
        findings.append(CommandManifestFinding("BLOCK", "COMMANDS_NOT_LIST", "commands is not a list"))
        commands = []

    current = build_current_reference()
    committed_names = {str(item.get("qualified_name")) for item in commands if isinstance(item, dict)}
    current_names = {
        str(item.get("qualified_name"))
        for item in current.get("commands", [])
        if isinstance(item, dict)
    }
    for name in sorted(current_names - committed_names):
        findings.append(CommandManifestFinding("BLOCK", "CLI_WITHOUT_JSON", name))
    for name in sorted(committed_names - current_names):
        findings.append(CommandManifestFinding("BLOCK", "JSON_WITHOUT_CLI", name))

    for command in commands:
        if not isinstance(command, dict):
            findings.append(CommandManifestFinding("BLOCK", "COMMAND_NOT_OBJECT", repr(command)))
            continue
        qualified = str(command.get("qualified_name") or "<unknown>")
        safety = command.get("safety")
        if safety not in SAFETY_VALUES:
            findings.append(
                CommandManifestFinding("BLOCK", "SAFETY_INVALID", f"{qualified}: {safety!r}")
            )
        replaces_raw = command.get("replaces_raw", [])
        if replaces_raw is None:
            replaces_raw = []
        if not isinstance(replaces_raw, list) or any(not str(item).strip() for item in replaces_raw):
            findings.append(
                CommandManifestFinding("BLOCK", "REPLACES_RAW_INVALID", f"{qualified}: {replaces_raw!r}")
            )

    meta = committed.get("meta") if isinstance(committed.get("meta"), dict) else {}
    expected_sha = manifest_sha(commands)
    if meta.get("manifest_sha") != expected_sha:
        findings.append(
            CommandManifestFinding(
                "BLOCK",
                "MANIFEST_SHA_MISMATCH",
                f"expected {expected_sha}, found {meta.get('manifest_sha')!r}",
            )
        )
    if meta.get("generated_md") != MD_PATH.as_posix():
        findings.append(
            CommandManifestFinding(
                "BLOCK",
                "GENERATED_MD_MISMATCH",
                f"expected {MD_PATH.as_posix()}, found {meta.get('generated_md')!r}",
            )
        )

    if committed != current:
        findings.append(
            CommandManifestFinding("BLOCK", "JSON_DRIFT", f"{json_path.as_posix()} differs from CLI")
        )
    expected_md = render_markdown(committed)
    actual_md = md_path.read_text(encoding="utf-8") if md_path.exists() else ""
    if actual_md != expected_md:
        findings.append(
            CommandManifestFinding("BLOCK", "MD_DRIFT", f"{md_path.as_posix()} differs from generator")
        )

    return CommandManifestAudit(root=root.as_posix(), findings=tuple(findings))


def render_command_manifest_audit(audit: CommandManifestAudit) -> str:
    lines = [
        "COMMAND_MANIFEST_AUDIT",
        f"STATUS={audit.status}",
        f"FINDING_COUNT={len(audit.findings)}",
        f"BLOCKER_COUNT={len(audit.blockers)}",
    ]
    for finding in audit.findings:
        lines.append(f"FINDING={finding.severity}|{finding.code}|{finding.message}")
    return "\n".join(lines) + "\n"
