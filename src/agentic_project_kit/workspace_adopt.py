from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import tomllib
from typing import Any

import yaml

from agentic_project_kit.documentation_registry import (
    build_doc_registry_scope_decision_rows,
)
from agentic_project_kit.workspace import SUPPORTED_MANIFEST_SCHEMA_VERSION, load_workspace


PRIVATE_PUBLIC_BOUNDARY = (
    "Regardless of mode: **no secrets, credentials, private chat fragments, or\n"
    "personal logs belong in any versioned part of `.agentic/`.** The task carrier\n"
    "contains the work order the user knowingly publishes — `SEND` already makes\n"
    "the push explicit. Machine-local state lives under `.agentic/tmp/` and is\n"
    "ignored by construction. `workspace adopt` and `workspace init` must print\n"
    "this boundary; documentation for public target repos must repeat it."
)

WORKSPACE_INIT_TREE = (
    ".agentic/",
    ".agentic/config.yaml",
    ".agentic/registries/",
    ".agentic/registries/documentation.yaml",
    ".agentic/registries/rules.yaml",
    ".agentic/rules/",
    ".agentic/rules/README.md",
    ".agentic/state/",
    ".agentic/state/README.md",
    ".agentic/state/status.md",
    ".agentic/state/handoff/",
    ".agentic/state/handoff/README.md",
    ".agentic/state/handoff/packages/",
    ".agentic/state/handoff/packages/latest/",
    ".agentic/state/handoff/reports/",
    ".agentic/state/handoff/terminal/",
    ".agentic/state/handoff/transfer_handoff_reports/",
    ".agentic/transfer/",
    ".agentic/transfer/inbox/",
    ".agentic/transfer/outbox/",
    ".agentic/tmp/",
    ".agentic/ci/",
    ".agentic/ci/agentic-gate.yaml",
    ".agentic/ci/pre-commit-snippet.yaml",
    ".agentic/INITIAL_LLM_PROMPT.md",
    ".gitignore",
)


@dataclass(frozen=True)
class ProjectSuggestion:
    name: str
    type: str
    profile: str

    def as_json_data(self) -> dict[str, str]:
        return {
            "name": self.name,
            "type": self.type,
            "profile": self.profile,
        }


@dataclass(frozen=True)
class AgenticCollision:
    status: str
    message: str
    manifest_version: int | None = None

    def as_json_data(self) -> dict[str, object]:
        data: dict[str, object] = {
            "status": self.status,
            "message": self.message,
        }
        if self.manifest_version is not None:
            data["manifest_version"] = self.manifest_version
        return data


@dataclass(frozen=True)
class DocsPreviewRow:
    docs_path: str
    registration_candidates: int

    def as_json_data(self) -> dict[str, object]:
        return {
            "docs_path": self.docs_path,
            "registration_candidates": self.registration_candidates,
        }


@dataclass(frozen=True)
class WorkspaceAdoptReport:
    root: Path
    project: ProjectSuggestion
    manifest: dict[str, object]
    manifest_yaml: str
    docs_preview: tuple[DocsPreviewRow, ...]
    ci_workflows: tuple[str, ...]
    agentic: AgenticCollision
    init_tree: tuple[str, ...] = WORKSPACE_INIT_TREE
    privacy_boundary: str = PRIVATE_PUBLIC_BOUNDARY

    def as_json_data(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "kind": "workspace_adopt_report",
            "root": self.root.as_posix(),
            "result_status": "PASS",
            "project": self.project.as_json_data(),
            "proposed_manifest": self.manifest,
            "proposed_manifest_yaml": self.manifest_yaml,
            "docs_preview": [row.as_json_data() for row in self.docs_preview],
            "ci_workflows": list(self.ci_workflows),
            "agentic": self.agentic.as_json_data(),
            "init_tree": list(self.init_tree),
            "privacy_boundary": self.privacy_boundary,
            "final_signal": "d",
        }


def analyze_workspace_adoption(root: Path | str = Path(".")) -> WorkspaceAdoptReport:
    root_path = Path(root)
    project = _suggest_project(root_path)
    manifest = _proposed_manifest(project)
    manifest_yaml = yaml.safe_dump(manifest, sort_keys=False)
    return WorkspaceAdoptReport(
        root=root_path,
        project=project,
        manifest=manifest,
        manifest_yaml=manifest_yaml,
        docs_preview=_docs_preview(root_path),
        ci_workflows=_ci_workflows(root_path),
        agentic=_agentic_collision(root_path),
    )


def render_workspace_adopt_report(report: WorkspaceAdoptReport) -> str:
    lines = [
        "WORKSPACE_ADOPT",
        "STATUS=PASS",
        f"ROOT={report.root.as_posix()}",
        f"PROJECT_NAME={report.project.name}",
        f"PROJECT_TYPE={report.project.type}",
        f"PROFILE={report.project.profile}",
        f"AGENTIC_STATUS={report.agentic.status}",
        f"AGENTIC_MESSAGE={report.agentic.message}",
    ]
    if report.agentic.manifest_version is not None:
        lines.append(f"AGENTIC_MANIFEST_VERSION={report.agentic.manifest_version}")

    lines.extend(["", "Proposed manifest:", "```yaml"])
    lines.extend(report.manifest_yaml.rstrip().splitlines())
    lines.append("```")

    lines.extend(["", "Docs registration candidates:"])
    if report.docs_preview:
        for row in report.docs_preview:
            lines.append(f"- {row.docs_path}: {row.registration_candidates}")
    else:
        lines.append("- none")

    lines.extend(["", "Existing CI workflows:"])
    if report.ci_workflows:
        for workflow in report.ci_workflows:
            lines.append(f"- {workflow}")
    else:
        lines.append("- none")

    lines.extend(["", "Workspace init would create:"])
    lines.extend(f"- {entry}" for entry in report.init_tree)

    lines.extend(["", "Private/public boundary:", report.privacy_boundary])
    return "\n".join(lines) + "\n"


def _suggest_project(root: Path) -> ProjectSuggestion:
    pyproject = root / "pyproject.toml"
    package_json = root / "package.json"
    if pyproject.exists():
        name = _pyproject_name(pyproject) or _fallback_project_name(root)
        return ProjectSuggestion(name=name, type="python", profile="python-default")
    if package_json.exists():
        name = _package_json_name(package_json) or _fallback_project_name(root)
        return ProjectSuggestion(name=name, type="node", profile="generic")
    return ProjectSuggestion(
        name=_fallback_project_name(root),
        type="generic",
        profile="generic",
    )


def _pyproject_name(path: Path) -> str:
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return ""
    project = data.get("project")
    if not isinstance(project, dict):
        return ""
    name = project.get("name")
    return name.strip() if isinstance(name, str) else ""


def _package_json_name(path: Path) -> str:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ""
    name = data.get("name") if isinstance(data, dict) else None
    return name.strip() if isinstance(name, str) else ""


def _fallback_project_name(root: Path) -> str:
    return root.name or "project"


def _proposed_manifest(project: ProjectSuggestion) -> dict[str, object]:
    return {
        "kit_schema_version": SUPPORTED_MANIFEST_SCHEMA_VERSION,
        "project": {
            "name": project.name,
            "type": project.type,
        },
        "profile": project.profile,
        "modules": {
            "doc_registry": True,
            "release_governance": True,
            "rule_registry": True,
            "transfer": True,
        },
        "transfer": {
            "visibility": "repo",
        },
        "paths": {
            "docs_root": "docs",
        },
        "gates": {
            "extra": [],
            "skip": [],
        },
    }


def _docs_preview(root: Path) -> tuple[DocsPreviewRow, ...]:
    rows = build_doc_registry_scope_decision_rows(root)
    return tuple(
        DocsPreviewRow(
            docs_path=str(row["docs_path"]),
            registration_candidates=int(row["md_files"]),
        )
        for row in rows
        if int(row["md_files"]) > 0
    )


def _ci_workflows(root: Path) -> tuple[str, ...]:
    workflows = root / ".github" / "workflows"
    if not workflows.exists():
        return ()
    return tuple(
        path.relative_to(root).as_posix()
        for path in sorted(workflows.glob("*.yml"))
        if path.is_file() and not path.is_symlink()
    )


def _agentic_collision(root: Path) -> AgenticCollision:
    agentic = root / ".agentic"
    manifest = agentic / "config.yaml"
    if not agentic.exists():
        return AgenticCollision(
            status="ready_for_workspace_init",
            message="ready for workspace init",
        )
    if not manifest.exists():
        return AgenticCollision(
            status="foreign_agentic_directory",
            message="FOREIGN .agentic/ directory without kit manifest; workspace init will refuse it",
        )
    try:
        load_workspace(root)
    except RuntimeError as exc:
        return AgenticCollision(
            status="invalid_workspace_manifest",
            message=str(exc),
        )
    version = _manifest_version(manifest)
    return AgenticCollision(
        status="already_initialized",
        message="already initialized",
        manifest_version=version,
    )


def _manifest_version(path: Path) -> int | None:
    try:
        data: Any = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return None
    if not isinstance(data, dict):
        return None
    version = data.get("kit_schema_version")
    return version if type(version) is int else None
