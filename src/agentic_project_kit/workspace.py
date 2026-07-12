from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field, fields, replace
import os
from pathlib import Path
from types import MappingProxyType
from typing import Any
import warnings

import yaml


SUPPORTED_MANIFEST_SCHEMA_VERSION = 1
WORKSPACE_MANIFEST_FIX_HINT = "run `agentic-kit workspace upgrade`, or fix the manifest"
LEGACY_PROFILE_WARNING_ENV = "AGENTIC_KIT_SUPPRESS_LEGACY_PROFILE_WARNING"
LEGACY_PROFILE_DEPRECATION_MESSAGE = (
    "agentic-kit implicit legacy profile is deprecated for manifest-less workspaces "
    "and will be removed in 2.0.0; run `agentic-kit workspace init --root PATH` "
    f"or set {LEGACY_PROFILE_WARNING_ENV}=1 to suppress this warning."
)
ALLOWED_PROJECT_TYPES = frozenset({"python", "node", "generic"})
ALLOWED_PROFILES = frozenset({"python-default", "generic"})
ALLOWED_MODULES = frozenset(
    {"release_governance", "doc_registry", "rule_registry", "transfer"}
)
ALLOWED_TRANSFER_VISIBILITIES = frozenset({"repo", "local"})
ALLOWED_DOC_LIFECYCLE_MODES = frozenset({"off", "warn", "strict"})
DEFAULT_DOC_LIFECYCLE_MODE = "warn"
DEFAULT_REVIEW_BUDGETS = MappingProxyType(
    {
        "governance": 180,
        "reference": 365,
        "workflow": 270,
    }
)
ALLOWED_TOP_LEVEL_KEYS = frozenset(
    {
        "kit_schema_version",
        "project",
        "profile",
        "modules",
        "transfer",
        "hygiene",
        "paths",
        "gates",
    }
)


class LegacyProfileDeprecationWarning(UserWarning):
    """Warning emitted when a manifest-less workspace uses the implicit legacy profile."""


def _default_modules() -> Mapping[str, bool]:
    return MappingProxyType({name: True for name in sorted(ALLOWED_MODULES)})


def default_review_budgets() -> Mapping[str, int]:
    return MappingProxyType(dict(DEFAULT_REVIEW_BUDGETS))


def default_hygiene_manifest() -> dict[str, object]:
    return {
        "doc_lifecycle": DEFAULT_DOC_LIFECYCLE_MODE,
        "review_budgets": dict(DEFAULT_REVIEW_BUDGETS),
    }


@dataclass(frozen=True)
class KitConfig:
    docs_root: str = "docs"
    tmp_root: str = "tmp"
    agentic_root: str = ".agentic"
    agentic_tmp_root: str = ".agentic/tmp"
    workspace_manifest_file: str = ".agentic/config.yaml"
    workspace_lock_file: str = "workspace.lock"
    transfer_root: str = ".agentic/transfer"
    transfer_inbox_name: str = "inbox"
    transfer_outbox_name: str = "outbox"
    reports_root: str = "docs/reports"
    terminal_reports_root: str = "docs/reports/terminal"
    command_runs_root: str = "docs/reports/command_runs"
    transfer_runs_root: str = "docs/reports/transfer_runs"
    transfer_handoff_reports_root: str = "docs/reports/terminal/transfer_handoff_reports"
    terminal_post_pr_successor_chat_handoff_prefix: str = "docs/reports/terminal/post-pr"
    handoff_root: str = "docs/handoff"
    handoff_packages_latest_root: str = "docs/reports/handoff-packages/latest"
    planning_root: str = "docs/planning"
    project_direction_file: str = "PROJECT_DIRECTION.yaml"
    governance_root: str = "docs/governance"
    reference_root: str = "docs/reference"
    architecture_root: str = "docs/architecture"
    source_root: str = "src/agentic_project_kit"
    pyproject_file: str = "pyproject.toml"
    admin_refresh_branch_prefix: str = "docs/post-pr"
    status_file: str = "STATUS.md"
    test_gates_file: str = "TEST_GATES.md"
    documentation_coverage_file: str = "DOCUMENTATION_COVERAGE.yaml"
    documentation_registry_file: str = "DOCUMENTATION_REGISTRY.yaml"
    rule_registry_file: str = ".agentic/rule_mechanism_inventory.yaml"
    rules_root: str = ".agentic/rules"
    handoff_state_file: str = "handoff_state.yaml"
    operational_handoff_state_file: str = "operational_handoff_state.yaml"


# Legacy->namespace mapping for manifest-bearing workspaces:
# docs_root stays docs (project documentation, not kit governance).
# tmp_root: tmp -> .agentic/tmp
# status_file: docs/STATUS.md -> .agentic/state/status.md
# documentation_registry_file: docs/DOCUMENTATION_REGISTRY.yaml -> .agentic/registries/documentation.yaml
# rule_registry_file: .agentic/rule_mechanism_inventory.yaml -> .agentic/registries/rules.yaml
# rules_root: .agentic/rules -> .agentic/rules
# handoff_state_file: .agentic/handoff_state.yaml -> .agentic/state/handoff/handoff_state.yaml
# operational_handoff_state_file: .agentic/operational_handoff_state.yaml -> .agentic/state/handoff/operational_handoff_state.yaml
# reports_root: docs/reports -> .agentic/state/handoff/reports
# terminal_reports_root: docs/reports/terminal -> .agentic/state/handoff/terminal
# command_runs_root: docs/reports/command_runs -> .agentic/state/handoff/command_runs
# transfer_runs_root: docs/reports/transfer_runs -> .agentic/state/handoff/transfer_runs
# transfer_handoff_reports_root: docs/reports/terminal/transfer_handoff_reports -> .agentic/state/handoff/transfer_handoff_reports
# terminal_post_pr_successor_chat_handoff_prefix: docs/reports/terminal/post-pr -> .agentic/state/handoff/terminal/post-pr
# handoff_root: docs/handoff -> .agentic/state/handoff
# handoff_packages_latest_root: docs/reports/handoff-packages/latest -> .agentic/state/handoff/packages/latest
LEGACY_DEFAULTS = KitConfig()
NAMESPACE_DEFAULTS = replace(
    LEGACY_DEFAULTS,
    tmp_root=".agentic/tmp",
    status_file=".agentic/state/status.md",
    documentation_registry_file=".agentic/registries/documentation.yaml",
    rule_registry_file=".agentic/registries/rules.yaml",
    handoff_state_file="state/handoff/handoff_state.yaml",
    operational_handoff_state_file="state/handoff/operational_handoff_state.yaml",
    reports_root=".agentic/state/handoff/reports",
    terminal_reports_root=".agentic/state/handoff/terminal",
    command_runs_root=".agentic/state/handoff/command_runs",
    transfer_runs_root=".agentic/state/handoff/transfer_runs",
    transfer_handoff_reports_root=".agentic/state/handoff/transfer_handoff_reports",
    terminal_post_pr_successor_chat_handoff_prefix=".agentic/state/handoff/terminal/post-pr",
    handoff_root=".agentic/state/handoff",
    handoff_packages_latest_root=".agentic/state/handoff/packages/latest",
)

PATH_OVERRIDE_ALIASES = MappingProxyType(
    {
        "tmp": "tmp_root",
        "status_path": "status_file",
        "test_gates_path": "test_gates_file",
        "documentation_coverage_path": "documentation_coverage_file",
        "doc_registry_path": "documentation_registry_file",
        "rule_registry_path": "rule_registry_file",
        "handoff_state_path": "handoff_state_file",
        "operational_handoff_state_path": "operational_handoff_state_file",
        "handoff_packages_latest": "handoff_packages_latest_root",
        "handoff_packages_latest_path": "handoff_packages_latest_root",
    }
)


@dataclass(frozen=True)
class Workspace:
    """Resolved workspace paths plus manifest metadata.

    In P2, manifest metadata is parsed and retained for later phases, but only
    `paths` overrides affect behavior. Profiles, module toggles, transfer
    visibility, and gate lists are intentionally not enforced until later
    schema-gated slices add those behaviors.
    """

    root: Path
    config: KitConfig
    profile: str = "implicit-legacy"
    project_name: str = ""
    project_type: str = "generic"
    modules: Mapping[str, bool] = field(default_factory=_default_modules)
    transfer_visibility: str = "repo"
    hygiene_doc_lifecycle: str = DEFAULT_DOC_LIFECYCLE_MODE
    hygiene_review_budgets: Mapping[str, int] = field(default_factory=default_review_budgets)
    gates_extra: tuple[str, ...] = ()
    gates_skip: tuple[str, ...] = ()

    def _path(self, relative: str | Path) -> Path:
        return self.root / Path(relative)

    def path_text(self, path: Path) -> str:
        try:
            return path.relative_to(self.root).as_posix()
        except ValueError:
            return path.as_posix()

    def root_file(self, name: str) -> Path:
        return self.root / name

    def docs_root(self) -> Path:
        return self._path(self.config.docs_root)

    def docs_file(self, name: str) -> Path:
        return self.docs_root() / name

    def tmp(self) -> Path:
        return self._path(self.config.tmp_root)

    def tmp_file(self, name: str) -> Path:
        return self.tmp() / name

    def tmp_dir(self, name: str) -> Path:
        return self.tmp() / name

    def agent_evidence_dir(self) -> Path:
        return self.tmp_dir("agent-evidence")

    def wrapper_status_path(self) -> Path:
        return self.tmp_file("current-wrapper-status.json")

    def gui_panel_state_path(self) -> Path:
        return self.tmp_file("gui-panel-state.json")

    def local_command_stack_state_path(self) -> Path:
        return self.tmp_file("local-command-stack-state.json")

    def local_gc_report_path(self) -> Path:
        return self.tmp_file("local-gc-last.json")

    def local_gc_run_marker_path(self) -> Path:
        return self.tmp_file("local-gc-last-run-id.txt")

    def agentic_root(self) -> Path:
        return self._path(self.config.agentic_root)

    def agentic_file(self, name: str) -> Path:
        return self.agentic_root() / name

    def _docs_file_or_path(self, name: str) -> Path:
        path = Path(name)
        if len(path.parts) > 1:
            return self._path(path)
        return self.docs_file(name)

    def _agentic_file_or_path(self, name: str) -> Path:
        path = Path(name)
        if len(path.parts) > 1:
            if path.parts[0] == self.config.agentic_root:
                return self._path(path)
            return self._path(self.config.agentic_root) / path
        return self.agentic_file(name)

    def agentic_tmp(self) -> Path:
        return self._path(self.config.agentic_tmp_root)

    def workspace_lock_path(self) -> Path:
        return self.agentic_tmp() / self.config.workspace_lock_file

    def transfer_inbox(self) -> Path:
        return self._path(self.config.transfer_root) / self.config.transfer_inbox_name

    def transfer_outbox(self) -> Path:
        return self._path(self.config.transfer_root) / self.config.transfer_outbox_name

    def handoff_state_path(self) -> Path:
        return self._agentic_file_or_path(self.config.handoff_state_file)

    def operational_handoff_state_path(self) -> Path:
        return self._agentic_file_or_path(self.config.operational_handoff_state_file)

    def compiled_agent_context_path(self) -> Path:
        return self.agentic_file("compiled_agent_context.yaml")

    def status_path(self) -> Path:
        return self._docs_file_or_path(self.config.status_file)

    def test_gates_path(self) -> Path:
        return self._docs_file_or_path(self.config.test_gates_file)

    def documentation_coverage_path(self) -> Path:
        return self._docs_file_or_path(self.config.documentation_coverage_file)

    def doc_registry_path(self) -> Path:
        return self._docs_file_or_path(self.config.documentation_registry_file)

    def rule_registry_path(self) -> Path:
        return self._path(self.config.rule_registry_file)

    def rules_dir(self) -> Path:
        return self._path(self.config.rules_root)

    def reports_dir(self) -> Path:
        return self._path(self.config.reports_root)

    def terminal_reports_dir(self) -> Path:
        return self._path(self.config.terminal_reports_root)

    def terminal_report_file(self, name: str) -> Path:
        return self.terminal_reports_dir() / name

    def latest_terminal_log_pointer(self) -> Path:
        return self.terminal_report_file("LATEST_TERMINAL_LOG.txt")

    def command_runs_dir(self) -> Path:
        return self._path(self.config.command_runs_root)

    def command_run_file(self, name: str) -> Path:
        return self.command_runs_dir() / name

    def latest_command_run_pointer(self) -> Path:
        return self.command_run_file("LATEST_COMMAND_RUN.txt")

    def transfer_runs_dir(self) -> Path:
        return self._path(self.config.transfer_runs_root)

    def transfer_run_file(self, name: str) -> Path:
        return self.transfer_runs_dir() / name

    def current_workflow_output_path(self) -> Path:
        return self.reports_dir() / "CURRENT_WORKFLOW_OUTPUT.md"

    def communication_rules_output_path(self) -> Path:
        return self.reports_dir() / "communication_rules" / "CURRENT_COMMUNICATION_RULES.md"

    def handoff_rules_output_path(self) -> Path:
        return self.reports_dir() / "handoff_rules" / "CURRENT_HANDOFF_RULES.md"

    def post_pr_successor_chat_handoff_prefix(self) -> str:
        return self.config.terminal_post_pr_successor_chat_handoff_prefix

    def post_pr_successor_chat_handoff_path(self, after_pr: int) -> Path:
        return self._path(f"{self.config.terminal_post_pr_successor_chat_handoff_prefix}{after_pr}-successor-chat-handoff.md")

    def transfer_handoff_report_file(self, name: str) -> Path:
        return self._path(self.config.transfer_handoff_reports_root) / name

    def transfer_handoff_reports_dir(self) -> Path:
        return self._path(self.config.transfer_handoff_reports_root)

    def handoff_dir(self) -> Path:
        return self._path(self.config.handoff_root)

    def handoff_file(self, name: str) -> Path:
        return self.handoff_dir() / name

    def handoff_packages_latest(self) -> Path:
        return self._path(self.config.handoff_packages_latest_root)

    def package_file(self, name: str) -> Path:
        return self.handoff_packages_latest() / name

    def planning_dir(self) -> Path:
        return self._path(self.config.planning_root)

    def planning_file(self, name: str) -> Path:
        return self.planning_dir() / name

    def project_direction_path(self) -> Path:
        return self.planning_file(self.config.project_direction_file)

    def governance_dir(self) -> Path:
        return self._path(self.config.governance_root)

    def governance_file(self, name: str) -> Path:
        return self.governance_dir() / name

    def reference_dir(self) -> Path:
        return self._path(self.config.reference_root)

    def reference_file(self, name: str) -> Path:
        return self.reference_dir() / name

    def architecture_dir(self) -> Path:
        return self._path(self.config.architecture_root)

    def architecture_file(self, name: str) -> Path:
        return self.architecture_dir() / name

    def source_root(self) -> Path:
        return self._path(self.config.source_root)

    def pyproject_path(self) -> Path:
        return self._path(self.config.pyproject_file)

    def admin_refresh_branch_prefix(self) -> str:
        return self.config.admin_refresh_branch_prefix

    def admin_refresh_branch(self, after_pr: int) -> str:
        return f"{self.config.admin_refresh_branch_prefix}{after_pr}-handoff-refresh"


def load_workspace(
    root: Path = Path("."),
    *,
    suppress_legacy_profile_warning: bool | None = None,
) -> Workspace:
    """Load the workspace using the implicit legacy profile or a schema-v1 manifest."""

    config = LEGACY_DEFAULTS
    root = Path(root)
    manifest_path = root / config.workspace_manifest_file
    if manifest_path.exists():
        return _load_manifest_workspace(root, manifest_path, NAMESPACE_DEFAULTS)
    if not _suppress_legacy_profile_warning(suppress_legacy_profile_warning):
        warnings.warn(
            LEGACY_PROFILE_DEPRECATION_MESSAGE,
            LegacyProfileDeprecationWarning,
            stacklevel=1,
        )
    return Workspace(root=root, config=config)


def _suppress_legacy_profile_warning(explicit: bool | None) -> bool:
    if explicit is not None:
        return explicit
    return os.environ.get(LEGACY_PROFILE_WARNING_ENV, "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _load_manifest_workspace(root: Path, manifest_path: Path, config: KitConfig) -> Workspace:
    location = _manifest_location(config.workspace_manifest_file)
    manifest = _read_manifest(manifest_path, location)
    _validate_top_level(manifest, location)
    _validate_schema_version(manifest, location)
    project_name, project_type = _parse_project(manifest.get("project"), location)
    profile = _parse_profile(manifest.get("profile", "python-default"), location)
    modules = _parse_modules(manifest.get("modules"), location)
    transfer_visibility = _parse_transfer_visibility(manifest.get("transfer"), location)
    hygiene_doc_lifecycle, hygiene_review_budgets = _parse_hygiene(manifest.get("hygiene"), location)
    config = _apply_path_overrides(config, manifest.get("paths"), location)
    gates_extra, gates_skip = _parse_gates(manifest.get("gates"), location)
    return Workspace(
        root=root,
        config=config,
        profile=profile,
        project_name=project_name,
        project_type=project_type,
        modules=modules,
        transfer_visibility=transfer_visibility,
        hygiene_doc_lifecycle=hygiene_doc_lifecycle,
        hygiene_review_budgets=hygiene_review_budgets,
        gates_extra=gates_extra,
        gates_skip=gates_skip,
    )


def _read_manifest(manifest_path: Path, location: str) -> dict[str, Any]:
    try:
        loaded = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise RuntimeError(_manifest_error(location, f"invalid YAML: {exc}")) from exc
    except OSError as exc:
        raise RuntimeError(_manifest_error(location, f"cannot read manifest: {exc}")) from exc
    if not isinstance(loaded, dict):
        raise RuntimeError(_manifest_error(location, "expected top-level mapping"))
    return loaded


def _validate_top_level(manifest: dict[str, Any], location: str) -> None:
    for key in manifest:
        if key not in ALLOWED_TOP_LEVEL_KEYS:
            raise RuntimeError(
                _manifest_error(f"{location}:{key}", "unknown top-level key")
            )


def _validate_schema_version(manifest: dict[str, Any], location: str) -> None:
    version = manifest.get("kit_schema_version")
    if type(version) is not int or version < 1:
        raise RuntimeError(
            f"{location}:kit_schema_version: invalid kit_schema_version; "
            f"{WORKSPACE_MANIFEST_FIX_HINT}"
        )
    if version > SUPPORTED_MANIFEST_SCHEMA_VERSION:
        raise RuntimeError(
            f"{location}:kit_schema_version: manifest schema v{version} "
            "is newer than this kit; upgrade the kit"
        )


def _parse_project(project: object, location: str) -> tuple[str, str]:
    if project is None:
        return "", "generic"
    if not isinstance(project, dict):
        raise RuntimeError(_manifest_error(f"{location}:project", "expected mapping"))
    project_name = project.get("name", "")
    if not isinstance(project_name, str):
        raise RuntimeError(_manifest_error(f"{location}:project.name", "expected string"))
    project_type = project.get("type", "generic")
    if not isinstance(project_type, str) or project_type not in ALLOWED_PROJECT_TYPES:
        allowed = ", ".join(sorted(ALLOWED_PROJECT_TYPES))
        raise RuntimeError(
            _manifest_error(
                f"{location}:project.type",
                f"invalid project type {project_type!r}; expected one of {allowed}",
            )
        )
    return project_name, project_type


def _parse_profile(profile: object, location: str) -> str:
    if not isinstance(profile, str) or profile not in ALLOWED_PROFILES:
        allowed = ", ".join(sorted(ALLOWED_PROFILES))
        raise RuntimeError(
            _manifest_error(
                f"{location}:profile",
                f"invalid profile {profile!r}; expected one of {allowed}",
            )
        )
    return profile


def _parse_modules(modules: object, location: str) -> Mapping[str, bool]:
    if modules is None:
        return _default_modules()
    if not isinstance(modules, dict):
        raise RuntimeError(_manifest_error(f"{location}:modules", "expected mapping"))
    merged = dict(_default_modules())
    for name, enabled in modules.items():
        if not isinstance(name, str) or name not in ALLOWED_MODULES:
            raise RuntimeError(
                _manifest_error(f"{location}:modules.{name}", "unknown module key")
            )
        if type(enabled) is not bool:
            raise RuntimeError(
                _manifest_error(f"{location}:modules.{name}", "expected bool")
            )
        merged[name] = enabled
    return MappingProxyType(merged)


def _parse_transfer_visibility(transfer: object, location: str) -> str:
    if transfer is None:
        return "repo"
    if not isinstance(transfer, dict):
        raise RuntimeError(_manifest_error(f"{location}:transfer", "expected mapping"))
    visibility = transfer.get("visibility", "repo")
    if (
        not isinstance(visibility, str)
        or visibility not in ALLOWED_TRANSFER_VISIBILITIES
    ):
        allowed = ", ".join(sorted(ALLOWED_TRANSFER_VISIBILITIES))
        raise RuntimeError(
            _manifest_error(
                f"{location}:transfer.visibility",
                f"invalid transfer visibility {visibility!r}; expected one of {allowed}",
            )
        )
    return visibility


def _parse_hygiene(hygiene: object, location: str) -> tuple[str, Mapping[str, int]]:
    if hygiene is None:
        return DEFAULT_DOC_LIFECYCLE_MODE, default_review_budgets()
    if not isinstance(hygiene, dict):
        raise RuntimeError(_manifest_error(f"{location}:hygiene", "expected mapping"))

    for key in hygiene:
        if key not in {"doc_lifecycle", "review_budgets"}:
            raise RuntimeError(
                _manifest_error(f"{location}:hygiene.{key}", "unknown hygiene key")
            )

    mode = hygiene.get("doc_lifecycle", DEFAULT_DOC_LIFECYCLE_MODE)
    if not isinstance(mode, str) or mode not in ALLOWED_DOC_LIFECYCLE_MODES:
        allowed = ", ".join(sorted(ALLOWED_DOC_LIFECYCLE_MODES))
        raise RuntimeError(
            _manifest_error(
                f"{location}:hygiene.doc_lifecycle",
                f"invalid doc_lifecycle mode {mode!r}; expected one of {allowed}",
            )
        )

    budgets = dict(DEFAULT_REVIEW_BUDGETS)
    review_budgets = hygiene.get("review_budgets")
    if review_budgets is not None:
        if not isinstance(review_budgets, dict):
            raise RuntimeError(
                _manifest_error(f"{location}:hygiene.review_budgets", "expected mapping")
            )
        for name, days in review_budgets.items():
            if not isinstance(name, str) or name not in DEFAULT_REVIEW_BUDGETS:
                raise RuntimeError(
                    _manifest_error(
                        f"{location}:hygiene.review_budgets.{name}",
                        "unknown review budget key",
                    )
                )
            if type(days) is not int or days <= 0:
                raise RuntimeError(
                    _manifest_error(
                        f"{location}:hygiene.review_budgets.{name}",
                        "expected positive int",
                    )
                )
            budgets[name] = days

    return mode, MappingProxyType(budgets)


def _apply_path_overrides(config: KitConfig, paths: object, location: str) -> KitConfig:
    if paths is None:
        return config
    if not isinstance(paths, dict):
        raise RuntimeError(_manifest_error(f"{location}:paths", "expected mapping"))
    allowed_fields = {field.name for field in fields(KitConfig)}
    overrides: dict[str, str] = {}
    for name, value in paths.items():
        field_name = PATH_OVERRIDE_ALIASES.get(name, name) if isinstance(name, str) else name
        if not isinstance(field_name, str) or field_name not in allowed_fields:
            raise RuntimeError(
                _manifest_error(f"{location}:paths.{name}", "unknown paths key")
            )
        if not isinstance(value, str):
            raise RuntimeError(
                _manifest_error(f"{location}:paths.{name}", "expected string")
            )
        overrides[field_name] = value
    return replace(config, **overrides)


def _parse_gates(gates: object, location: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
    if gates is None:
        return (), ()
    if not isinstance(gates, dict):
        raise RuntimeError(_manifest_error(f"{location}:gates", "expected mapping"))
    return (
        _parse_string_list(gates.get("extra", []), f"{location}:gates.extra"),
        _parse_string_list(gates.get("skip", []), f"{location}:gates.skip"),
    )


def _parse_string_list(value: object, location: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise RuntimeError(_manifest_error(location, "expected list of strings"))
    return tuple(value)


def _manifest_location(path: str) -> str:
    return path


def _manifest_error(location: str, message: str) -> str:
    return f"{location}: {message}; {WORKSPACE_MANIFEST_FIX_HINT}"
