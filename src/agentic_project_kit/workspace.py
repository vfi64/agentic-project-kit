from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field, fields, replace
from pathlib import Path
from types import MappingProxyType
from typing import Any

import yaml


SUPPORTED_MANIFEST_SCHEMA_VERSION = 1
WORKSPACE_MANIFEST_FIX_HINT = "run `agentic-kit workspace upgrade`, or fix the manifest"
ALLOWED_PROJECT_TYPES = frozenset({"python", "node", "generic"})
ALLOWED_PROFILES = frozenset({"python-default", "generic"})
ALLOWED_MODULES = frozenset(
    {"release_governance", "doc_registry", "rule_registry", "transfer"}
)
ALLOWED_TRANSFER_VISIBILITIES = frozenset({"repo", "local"})
ALLOWED_TOP_LEVEL_KEYS = frozenset(
    {
        "kit_schema_version",
        "project",
        "profile",
        "modules",
        "transfer",
        "paths",
        "gates",
    }
)


def _default_modules() -> Mapping[str, bool]:
    return MappingProxyType({name: True for name in sorted(ALLOWED_MODULES)})


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
    handoff_state_file: str = "handoff_state.yaml"
    operational_handoff_state_file: str = "operational_handoff_state.yaml"


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
    gates_extra: tuple[str, ...] = ()
    gates_skip: tuple[str, ...] = ()

    def _path(self, relative: str | Path) -> Path:
        return self.root / Path(relative)

    def root_file(self, name: str) -> Path:
        return self.root / name

    def docs_root(self) -> Path:
        return self._path(self.config.docs_root)

    def docs_file(self, name: str) -> Path:
        return self.docs_root() / name

    def tmp(self) -> Path:
        return self._path(self.config.tmp_root)

    def agentic_root(self) -> Path:
        return self._path(self.config.agentic_root)

    def agentic_file(self, name: str) -> Path:
        return self.agentic_root() / name

    def agentic_tmp(self) -> Path:
        return self._path(self.config.agentic_tmp_root)

    def workspace_lock_path(self) -> Path:
        return self.agentic_tmp() / self.config.workspace_lock_file

    def transfer_inbox(self) -> Path:
        return self._path(self.config.transfer_root) / self.config.transfer_inbox_name

    def transfer_outbox(self) -> Path:
        return self._path(self.config.transfer_root) / self.config.transfer_outbox_name

    def handoff_state_path(self) -> Path:
        return self.agentic_file(self.config.handoff_state_file)

    def operational_handoff_state_path(self) -> Path:
        return self.agentic_file(self.config.operational_handoff_state_file)

    def compiled_agent_context_path(self) -> Path:
        return self.agentic_file("compiled_agent_context.yaml")

    def status_path(self) -> Path:
        return self.docs_file(self.config.status_file)

    def test_gates_path(self) -> Path:
        return self.docs_file(self.config.test_gates_file)

    def documentation_coverage_path(self) -> Path:
        return self.docs_file(self.config.documentation_coverage_file)

    def doc_registry_path(self) -> Path:
        return self.docs_file(self.config.documentation_registry_file)

    def reports_dir(self) -> Path:
        return self._path(self.config.reports_root)

    def terminal_reports_dir(self) -> Path:
        return self._path(self.config.terminal_reports_root)

    def post_pr_successor_chat_handoff_prefix(self) -> str:
        return self.config.terminal_post_pr_successor_chat_handoff_prefix

    def post_pr_successor_chat_handoff_path(self, after_pr: int) -> Path:
        return self._path(f"{self.config.terminal_post_pr_successor_chat_handoff_prefix}{after_pr}-successor-chat-handoff.md")

    def transfer_handoff_report_file(self, name: str) -> Path:
        return self._path(self.config.transfer_handoff_reports_root) / name

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


def load_workspace(root: Path = Path(".")) -> Workspace:
    """Load the workspace using the implicit legacy profile or a schema-v1 manifest."""

    config = KitConfig()
    root = Path(root)
    manifest_path = root / config.workspace_manifest_file
    if manifest_path.exists():
        return _load_manifest_workspace(root, manifest_path, config)
    return Workspace(root=root, config=config)


def _load_manifest_workspace(root: Path, manifest_path: Path, config: KitConfig) -> Workspace:
    location = _manifest_location(config.workspace_manifest_file)
    manifest = _read_manifest(manifest_path, location)
    _validate_top_level(manifest, location)
    _validate_schema_version(manifest, location)
    project_name, project_type = _parse_project(manifest.get("project"), location)
    profile = _parse_profile(manifest.get("profile", "python-default"), location)
    modules = _parse_modules(manifest.get("modules"), location)
    transfer_visibility = _parse_transfer_visibility(manifest.get("transfer"), location)
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


def _apply_path_overrides(config: KitConfig, paths: object, location: str) -> KitConfig:
    if paths is None:
        return config
    if not isinstance(paths, dict):
        raise RuntimeError(_manifest_error(f"{location}:paths", "expected mapping"))
    allowed_fields = {field.name for field in fields(KitConfig)}
    overrides: dict[str, str] = {}
    for name, value in paths.items():
        if not isinstance(name, str) or name not in allowed_fields:
            raise RuntimeError(
                _manifest_error(f"{location}:paths.{name}", "unknown paths key")
            )
        if not isinstance(value, str):
            raise RuntimeError(
                _manifest_error(f"{location}:paths.{name}", "expected string")
            )
        overrides[name] = value
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
