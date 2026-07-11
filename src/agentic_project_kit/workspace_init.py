from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from agentic_project_kit.workspace import (
    ALLOWED_PROFILES,
    ALLOWED_PROJECT_TYPES,
    SUPPORTED_MANIFEST_SCHEMA_VERSION,
    load_workspace,
)
from agentic_project_kit.workspace_adopt import (
    PRIVATE_PUBLIC_BOUNDARY,
    WORKSPACE_INIT_TREE,
    ProjectSuggestion,
    analyze_workspace_adoption,
)
from agentic_project_kit.chat_entrypoint_contract import command_reference_prompt_block
from agentic_project_kit.workspace_lock import acquire_workspace_lock


GITIGNORE_TMP_LINE = ".agentic/tmp/"
CI_TEMPLATE_PATH = ".agentic/ci/agentic-gate.yaml"
PRE_COMMIT_TEMPLATE_PATH = ".agentic/ci/pre-commit-snippet.yaml"
CI_INJECTION_TARGET = ".github/workflows/agentic-gate.yaml"
PRE_COMMIT_INJECTION_TARGET = ".pre-commit-config.yaml"
MANAGED_CI_HEADER = "# managed template — source of truth: .agentic/ci/agentic-gate.yaml"
MANAGED_PRE_COMMIT_HEADER = (
    "# managed template — source of truth: .agentic/ci/pre-commit-snippet.yaml"
)


class WorkspaceInitError(RuntimeError):
    def __init__(self, message: str, *, code: str = "FAIL") -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class WorkspaceInitPlan:
    root: Path
    project: ProjectSuggestion
    manifest: dict[str, object]
    manifest_yaml: str
    files: dict[str, str]
    directories: tuple[str, ...]
    gitignore_diff: tuple[str, ...]
    inject_ci: bool
    inject_pre_commit: bool
    injection_targets: tuple[str, ...]
    execute: bool
    privacy_boundary: str = PRIVATE_PUBLIC_BOUNDARY

    @property
    def tree(self) -> tuple[str, ...]:
        return WORKSPACE_INIT_TREE

    def as_json_data(self, *, written: bool = False) -> dict[str, object]:
        return {
            "schema_version": 1,
            "kind": "workspace_init_plan",
            "root": self.root.as_posix(),
            "result_status": "PASS",
            "mode": "execute" if self.execute else "dry-run",
            "written": written,
            "project": self.project.as_json_data(),
            "manifest": self.manifest,
            "manifest_yaml": self.manifest_yaml,
            "tree": list(self.tree),
            "directories": list(self.directories),
            "files": sorted(self.files),
            "gitignore_diff": list(self.gitignore_diff),
            "injection_targets": list(self.injection_targets),
            "privacy_boundary": self.privacy_boundary,
            "final_signal": "d",
        }


def build_workspace_init_plan(
    root: Path | str = Path("."),
    *,
    name: str | None = None,
    project_type: str | None = None,
    profile: str | None = None,
    execute: bool = False,
    inject_ci: bool = False,
    inject_pre_commit: bool = False,
) -> WorkspaceInitPlan:
    root_path = Path(root)
    _preflight_workspace_absence(root_path)
    adopted = analyze_workspace_adoption(root_path)
    project = _override_project(
        adopted.project,
        name=name,
        project_type=project_type,
        profile=profile,
    )
    manifest = _manifest_for(project)
    manifest_yaml = yaml.safe_dump(manifest, sort_keys=False)
    files = _planned_files(project, manifest_yaml)
    directories = (
        ".agentic",
        ".agentic/registries",
        ".agentic/rules",
        ".agentic/state",
        ".agentic/state/handoff",
        ".agentic/state/handoff/packages",
        ".agentic/state/handoff/packages/latest",
        ".agentic/state/handoff/reports",
        ".agentic/state/handoff/terminal",
        ".agentic/state/handoff/transfer_handoff_reports",
        ".agentic/transfer",
        ".agentic/transfer/inbox",
        ".agentic/transfer/outbox",
        ".agentic/tmp",
        ".agentic/ci",
    )
    injection_targets = tuple(
        target
        for enabled, target in (
            (inject_ci, CI_INJECTION_TARGET),
            (inject_pre_commit, PRE_COMMIT_INJECTION_TARGET),
        )
        if enabled
    )
    if execute:
        _preflight_injection_targets(root_path, injection_targets)
    return WorkspaceInitPlan(
        root=root_path,
        project=project,
        manifest=manifest,
        manifest_yaml=manifest_yaml,
        files=files,
        directories=directories,
        gitignore_diff=_gitignore_diff(root_path),
        inject_ci=inject_ci,
        inject_pre_commit=inject_pre_commit,
        injection_targets=injection_targets,
        execute=execute,
    )


def execute_workspace_init(plan: WorkspaceInitPlan) -> None:
    _preflight_workspace_absence(plan.root)
    _preflight_injection_targets(plan.root, plan.injection_targets)
    with acquire_workspace_lock(plan.root, "workspace_init"):
        for directory in plan.directories:
            (plan.root / directory).mkdir(parents=True, exist_ok=True)
        for relative_path, content in plan.files.items():
            path = plan.root / relative_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        _append_gitignore_tmp(plan.root)
        if plan.inject_ci:
            _inject_template(
                plan.root,
                source=CI_TEMPLATE_PATH,
                target=CI_INJECTION_TARGET,
                header=MANAGED_CI_HEADER,
            )
        if plan.inject_pre_commit:
            _inject_template(
                plan.root,
                source=PRE_COMMIT_TEMPLATE_PATH,
                target=PRE_COMMIT_INJECTION_TARGET,
                header=MANAGED_PRE_COMMIT_HEADER,
            )
        load_workspace(plan.root)


def render_workspace_init_plan(plan: WorkspaceInitPlan, *, written: bool = False) -> str:
    lines = [
        "WORKSPACE_INIT",
        "STATUS=PASS",
        f"MODE={'execute' if plan.execute else 'dry-run'}",
        f"WRITTEN={str(written).lower()}",
        f"ROOT={plan.root.as_posix()}",
        f"PROJECT_NAME={plan.project.name}",
        f"PROJECT_TYPE={plan.project.type}",
        f"PROFILE={plan.project.profile}",
        "",
        "Workspace tree:",
    ]
    lines.extend(f"- {entry}" for entry in plan.tree)
    lines.extend(["", "Proposed manifest:", "```yaml"])
    lines.extend(plan.manifest_yaml.rstrip().splitlines())
    lines.append("```")
    lines.extend(["", ".gitignore diff:"])
    if plan.gitignore_diff:
        lines.extend(f"- {line}" for line in plan.gitignore_diff)
    else:
        lines.append("- no change")
    lines.extend(["", "Injection targets:"])
    if plan.injection_targets:
        lines.extend(f"- {target}" for target in plan.injection_targets)
    else:
        lines.append("- none")
    lines.extend(["", "Private/public boundary:", plan.privacy_boundary])
    return "\n".join(lines) + "\n"


def render_workspace_init_error(error: WorkspaceInitError) -> str:
    return f"WORKSPACE_INIT\nSTATUS=FAIL\nCODE={error.code}\nERROR={error}\n"


def _preflight_workspace_absence(root: Path) -> None:
    agentic = root / ".agentic"
    manifest = agentic / "config.yaml"
    if manifest.exists():
        raise WorkspaceInitError(
            "already initialized; see workspace upgrade for schema migrations",
            code="ALREADY_INITIALIZED",
        )
    if agentic.exists():
        raise WorkspaceInitError(
            "FOREIGN .agentic/ directory without kit manifest; refusing workspace init",
            code="FOREIGN_AGENTIC",
        )


def _preflight_injection_targets(root: Path, targets: tuple[str, ...]) -> None:
    for target in targets:
        if (root / target).exists():
            raise WorkspaceInitError(
                f"{target} already exists; refusing to overwrite injected template",
                code="INJECTION_TARGET_EXISTS",
            )


def _override_project(
    project: ProjectSuggestion,
    *,
    name: str | None,
    project_type: str | None,
    profile: str | None,
) -> ProjectSuggestion:
    resolved_type = project_type.strip() if isinstance(project_type, str) and project_type.strip() else project.type
    resolved_profile = profile.strip() if isinstance(profile, str) and profile.strip() else project.profile
    resolved_name = name.strip() if isinstance(name, str) and name.strip() else project.name
    if resolved_type not in ALLOWED_PROJECT_TYPES:
        allowed = ", ".join(sorted(ALLOWED_PROJECT_TYPES))
        raise WorkspaceInitError(
            f"invalid project type {resolved_type!r}; expected one of {allowed}",
            code="INVALID_PROJECT_TYPE",
        )
    if resolved_profile not in ALLOWED_PROFILES:
        allowed = ", ".join(sorted(ALLOWED_PROFILES))
        raise WorkspaceInitError(
            f"invalid profile {resolved_profile!r}; expected one of {allowed}",
            code="INVALID_PROFILE",
        )
    return ProjectSuggestion(
        name=resolved_name,
        type=resolved_type,
        profile=resolved_profile,
    )


def _manifest_for(project: ProjectSuggestion) -> dict[str, object]:
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


def _planned_files(project: ProjectSuggestion, manifest_yaml: str) -> dict[str, str]:
    return {
        ".agentic/config.yaml": manifest_yaml,
        ".agentic/registries/documentation.yaml": "schema_version: 1\ndocuments: []\n",
        ".agentic/registries/rules.yaml": "schema_version: 1\nrules: []\n",
        ".agentic/rules/README.md": "# Workspace Rules\n\nAdd reviewed project rule capsules here.\n",
        ".agentic/state/README.md": "# Workspace State\n\nMachine-readable governed state belongs here.\n",
        ".agentic/state/status.md": _workspace_status_seed(project),
        ".agentic/state/handoff/README.md": "# Workspace Handoff\n\nValidated handoff packages belong here.\n",
        CI_TEMPLATE_PATH: _ci_template(),
        PRE_COMMIT_TEMPLATE_PATH: _pre_commit_template(),
        ".agentic/INITIAL_LLM_PROMPT.md": _initial_llm_prompt(project),
    }


def _ci_template() -> str:
    return """name: Agentic Gate
"on":
  pull_request:
  push:

jobs:
  agentic-gate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: python -m pip install --upgrade pip
      - run: python -m pip install agentic-project-kit
      - run: agentic-kit standard-gates-audit-suite
"""


def _pre_commit_template() -> str:
    return """repos:
  - repo: local
    hooks:
      - id: agentic-standard-gates
        name: agentic standard gates
        entry: agentic-kit standard-gates-audit-suite
        language: system
        pass_filenames: false
"""


def _workspace_status_seed(project: ProjectSuggestion) -> str:
    return f"""# Workspace Status

Project: {project.name}
Project type: {project.type}
Profile: {project.profile}

Current state: initialized workspace.
"""


def _initial_llm_prompt(project: ProjectSuggestion) -> str:
    return f"""# Initial LLM Prompt

{command_reference_prompt_block()}

You are working in repository `{project.name}`.

Before mutating anything:
1. Inspect the repository root and current branch.
2. Read `.agentic/config.yaml`.
3. Treat `.agentic/transfer/inbox/` as the workspace transfer inbox carrier.
4. Run or request `agentic-kit standard-gates-audit-suite` before claiming completion.

Default branch: `main`
Project type: `{project.type}`
Profile: `{project.profile}`

Private/public boundary: no secrets, credentials, private chat fragments, or
personal logs belong in any versioned part of `.agentic/`. Machine-local state
lives under `.agentic/tmp/` and is ignored by construction.
"""


def _gitignore_diff(root: Path) -> tuple[str, ...]:
    gitignore = root / ".gitignore"
    if not gitignore.exists():
        return (f"+ {GITIGNORE_TMP_LINE}",)
    lines = gitignore.read_text(encoding="utf-8").splitlines()
    if GITIGNORE_TMP_LINE in lines:
        return ()
    return (f"+ {GITIGNORE_TMP_LINE}",)


def _append_gitignore_tmp(root: Path) -> None:
    gitignore = root / ".gitignore"
    existing = gitignore.read_text(encoding="utf-8") if gitignore.exists() else ""
    lines = existing.splitlines()
    if GITIGNORE_TMP_LINE in lines:
        return
    prefix = existing
    if prefix and not prefix.endswith("\n"):
        prefix += "\n"
    gitignore.write_text(prefix + GITIGNORE_TMP_LINE + "\n", encoding="utf-8")


def _inject_template(root: Path, *, source: str, target: str, header: str) -> None:
    target_path = root / target
    if target_path.exists():
        raise WorkspaceInitError(
            f"{target} already exists; refusing to overwrite injected template",
            code="INJECTION_TARGET_EXISTS",
        )
    source_text = (root / source).read_text(encoding="utf-8")
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(header + "\n" + source_text, encoding="utf-8")
